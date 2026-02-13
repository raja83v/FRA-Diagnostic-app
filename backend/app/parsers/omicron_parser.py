"""
Omicron FRAnalyzer parser.

Handles Omicron-specific CSV exports and the proprietary .fra format.
CSV exports typically have a multi-line header block with metadata
followed by tab-separated data columns.
"""
import csv
import io
import re
from typing import BinaryIO

from app.parsers.base import BaseFRAParser, ParseResult, ParseStatus, RawFRAData


class OmicronParser(BaseFRAParser):
    """
    Parser for Omicron FRAnalyzer exported files.

    Omicron CSV exports typically contain:
      - Header block with "FRAnalyzer" or "OMICRON" identifier
      - Metadata lines (serial number, date, winding config, etc.)
      - Tab-separated data: Frequency [Hz]  |  Magnitude [dB]  |  Phase [°]
    """

    name = "omicron"
    supported_extensions = (".csv", ".txt", ".fra", ".xml")

    def detect(self, filename: str, header_bytes: bytes) -> bool:
        if not self.can_handle_extension(filename):
            return False

        try:
            text = header_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            return False

        text_lower = text.lower()
        return "omicron" in text_lower or "franalyzer" in text_lower

    def parse(self, filename: str, fileobj: BinaryIO) -> ParseResult:
        warnings: list[str] = []
        raw = fileobj.read()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")

        lines = text.strip().splitlines()
        metadata: dict = {}

        # Extract metadata from header lines (before data block)
        data_start = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Look for metadata key-value pairs
            kv = re.match(r"^([A-Za-z\s_]+)\s*[:=]\s*(.+)$", stripped)
            if kv:
                metadata[kv.group(1).strip()] = kv.group(2).strip()
                continue

            # Detect start of numeric data
            parts = re.split(r"[\t,;]+", stripped)
            try:
                float(parts[0])
                data_start = i
                break
            except (ValueError, IndexError):
                continue

        # Parse data rows (tab-separated is typical for Omicron)
        frequency: list[float] = []
        magnitude: list[float] = []
        phase: list[float] = []
        bad_rows = 0

        for line in lines[data_start:]:
            parts = re.split(r"[\t,;]+", line.strip())
            try:
                f = float(parts[0])
                m = float(parts[1])
                p = float(parts[2]) if len(parts) > 2 else None
            except (ValueError, IndexError):
                bad_rows += 1
                continue

            frequency.append(f)
            magnitude.append(m)
            if p is not None:
                phase.append(p)

        if bad_rows > 0:
            warnings.append(f"Skipped {bad_rows} unparseable row(s)")

        if not frequency:
            return ParseResult(
                status=ParseStatus.FAILED,
                errors=["No valid data rows found in Omicron file"],
                original_filename=filename,
                detected_format="omicron",
            )

        data = RawFRAData(
            frequency_hz=frequency,
            magnitude_db=magnitude,
            phase_degrees=phase if phase else None,
            vendor="Omicron",
            extra_metadata=metadata,
        )

        # Map metadata fields
        for key, val in metadata.items():
            k = key.lower()
            if "serial" in k:
                data.serial_number = val
            elif "date" in k or "time" in k:
                data.measurement_date = val
            elif "winding" in k or "config" in k:
                data.winding_config = val
            elif "temp" in k:
                try:
                    data.temperature_celsius = float(re.sub(r"[^\d.\-]", "", val))
                except ValueError:
                    pass

        status = ParseStatus.SUCCESS if bad_rows == 0 else ParseStatus.PARTIAL
        return ParseResult(
            status=status,
            data=data,
            warnings=warnings,
            original_filename=filename,
            detected_format="omicron",
        )
