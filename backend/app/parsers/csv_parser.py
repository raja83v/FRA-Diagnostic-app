"""
Generic CSV parser for FRA measurement files.

Handles various CSV layouts:
  - Column-based with headers (Frequency, Magnitude, Phase)
  - Delimiter auto-detection (comma, tab, semicolon)
  - Various header naming conventions
"""
import csv
import io
import re
from typing import BinaryIO

from app.parsers.base import BaseFRAParser, ParseResult, ParseStatus, RawFRAData


# Common header patterns (case-insensitive)
_FREQ_PATTERNS = re.compile(
    r"^(freq|frequency|f[\s_]?\(?hz\)?|freq[\s_]?\(?hz\)?|frequency[\s_]?\(?hz\)?)$",
    re.IGNORECASE,
)
_MAG_PATTERNS = re.compile(
    r"^(mag|magnitude|amplitude|gain|mag[\s_]?\(?db\)?|magnitude[\s_]?\(?db\)?|"
    r"transfer[\s_]?function|tf[\s_]?\(?db\)?|impedance[\s_]?\(?db\)?)$",
    re.IGNORECASE,
)
_PHASE_PATTERNS = re.compile(
    r"^(phase|angle|phase[\s_]?\(?deg\)?|phase[\s_]?\(?(degrees|°)\)?|"
    r"arg[\s_]?\(?deg\)?)$",
    re.IGNORECASE,
)


def _detect_delimiter(sample: str) -> str:
    """Auto-detect CSV delimiter from a text sample."""
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(sample, delimiters=",\t;|")
        return dialect.delimiter
    except csv.Error:
        # Fall back to comma
        return ","


def _match_columns(
    headers: list[str],
) -> tuple[int | None, int | None, int | None]:
    """
    Match header names to (freq_idx, mag_idx, phase_idx).
    Returns column indices or None.
    """
    freq_idx = mag_idx = phase_idx = None

    for i, h in enumerate(headers):
        h_stripped = h.strip()
        if freq_idx is None and _FREQ_PATTERNS.match(h_stripped):
            freq_idx = i
        elif mag_idx is None and _MAG_PATTERNS.match(h_stripped):
            mag_idx = i
        elif phase_idx is None and _PHASE_PATTERNS.match(h_stripped):
            phase_idx = i

    return freq_idx, mag_idx, phase_idx


def _try_numeric_columns(row: list[str]) -> bool:
    """Check if all columns of a row can be converted to float."""
    try:
        for val in row:
            float(val.strip())
        return True
    except (ValueError, AttributeError):
        return False


class GenericCSVParser(BaseFRAParser):
    """
    Parses generic CSV files containing FRA data.

    Detection heuristics:
      - File extension is .csv or .txt
      - Content contains numeric columns interpretable as freq / mag / phase
    """

    name = "generic_csv"
    supported_extensions = (".csv", ".txt", ".tsv")

    def detect(self, filename: str, header_bytes: bytes) -> bool:
        if not self.can_handle_extension(filename):
            return False

        # Quick content check — should be decodable text with numbers
        try:
            text = header_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                text = header_bytes.decode("latin-1")
            except UnicodeDecodeError:
                return False

        # Must contain at least some digits and delimiters
        if not re.search(r"\d+[\.\d]*", text):
            return False

        return True

    def parse(self, filename: str, fileobj: BinaryIO) -> ParseResult:
        warnings: list[str] = []
        errors: list[str] = []

        # Read full content
        raw = fileobj.read()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")

        lines = text.strip().splitlines()
        if len(lines) < 2:
            return ParseResult(
                status=ParseStatus.FAILED,
                errors=["File has fewer than 2 lines"],
                original_filename=filename,
                detected_format="csv",
            )

        # Strip comment lines (lines starting with # or //)
        metadata: dict = {}
        data_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                # Try to extract key-value metadata from comments
                kv = re.match(r"^[#/]+\s*(.+?)\s*[:=]\s*(.+)$", stripped)
                if kv:
                    metadata[kv.group(1).strip()] = kv.group(2).strip()
                continue
            if stripped:
                data_lines.append(stripped)

        if len(data_lines) < 2:
            return ParseResult(
                status=ParseStatus.FAILED,
                errors=["No data lines found after stripping comments"],
                original_filename=filename,
                detected_format="csv",
            )

        # Detect delimiter from first few data lines
        sample = "\n".join(data_lines[:5])
        delimiter = _detect_delimiter(sample)

        # Parse header row
        first_row = data_lines[0].split(delimiter) if delimiter != "," else next(
            csv.reader([data_lines[0]])
        )
        first_row = [c.strip() for c in first_row]

        has_header = not _try_numeric_columns(first_row)

        freq_idx: int | None = None
        mag_idx: int | None = None
        phase_idx: int | None = None
        data_start = 0

        if has_header:
            freq_idx, mag_idx, phase_idx = _match_columns(first_row)
            data_start = 1

            if freq_idx is None or mag_idx is None:
                # Fallback: assume column order freq, mag, [phase]
                ncols = len(first_row)
                if ncols >= 2:
                    freq_idx, mag_idx = 0, 1
                    if ncols >= 3:
                        phase_idx = 2
                    warnings.append(
                        f"Could not match headers {first_row}; assuming column order: "
                        "frequency, magnitude, phase"
                    )
                else:
                    return ParseResult(
                        status=ParseStatus.FAILED,
                        errors=[f"Only {ncols} column(s) found; need at least 2"],
                        original_filename=filename,
                        detected_format="csv",
                    )
        else:
            # No header — assume col order
            ncols = len(first_row)
            if ncols >= 2:
                freq_idx, mag_idx = 0, 1
                if ncols >= 3:
                    phase_idx = 2
                warnings.append(
                    "No header row detected; assuming column order: frequency, magnitude, phase"
                )
            else:
                return ParseResult(
                    status=ParseStatus.FAILED,
                    errors=[f"Only {ncols} column(s); need at least 2"],
                    original_filename=filename,
                    detected_format="csv",
                )

        # Parse data rows
        frequency: list[float] = []
        magnitude: list[float] = []
        phase: list[float] = []
        bad_rows = 0

        reader_lines = data_lines[data_start:]
        for i, line in enumerate(reader_lines):
            if delimiter != ",":
                cols = [c.strip() for c in line.split(delimiter)]
            else:
                cols = [c.strip() for c in next(csv.reader([line]))]

            try:
                f = float(cols[freq_idx])
                m = float(cols[mag_idx])
                p = float(cols[phase_idx]) if phase_idx is not None and phase_idx < len(cols) else None
            except (IndexError, ValueError):
                bad_rows += 1
                continue

            frequency.append(f)
            magnitude.append(m)
            if p is not None:
                phase.append(p)

        if bad_rows > 0:
            warnings.append(f"Skipped {bad_rows} unparseable row(s)")

        if len(frequency) == 0:
            return ParseResult(
                status=ParseStatus.FAILED,
                errors=["No valid data rows could be parsed"],
                original_filename=filename,
                detected_format="csv",
            )

        data = RawFRAData(
            frequency_hz=frequency,
            magnitude_db=magnitude,
            phase_degrees=phase if phase else None,
            vendor="Generic CSV",
            extra_metadata=metadata,
        )

        # Try to extract metadata from comments
        for key, val in metadata.items():
            k = key.lower()
            if "serial" in k:
                data.serial_number = val
            elif "temperature" in k or "temp" in k:
                try:
                    data.temperature_celsius = float(re.sub(r"[^\d.\-]", "", val))
                except ValueError:
                    pass
            elif "winding" in k or "config" in k:
                data.winding_config = val
            elif "date" in k:
                data.measurement_date = val
            elif "transformer" in k or "name" in k:
                data.transformer_name = val

        status = ParseStatus.SUCCESS if bad_rows == 0 else ParseStatus.PARTIAL
        return ParseResult(
            status=status,
            data=data,
            warnings=warnings,
            original_filename=filename,
            detected_format="csv",
        )
