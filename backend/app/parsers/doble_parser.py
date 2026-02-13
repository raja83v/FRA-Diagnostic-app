"""
Doble M4000 / M5000 parser.

Handles Doble-exported CSV files. Doble exports typically
have a header block with test setup info followed by CSV data.
"""
import re
from typing import BinaryIO

from app.parsers.base import BaseFRAParser, ParseResult, ParseStatus, RawFRAData


class DobleParser(BaseFRAParser):
    """
    Parser for Doble M-series exported files.

    Doble CSV exports typically contain:
      - Header block with "Doble" or "M4000" / "M5000" identifier
      - Metadata section (asset info, test conditions)
      - CSV data: Frequency, Magnitude, Phase
    """

    name = "doble"
    supported_extensions = (".csv", ".txt", ".m4000", ".xml")

    def detect(self, filename: str, header_bytes: bytes) -> bool:
        if not self.can_handle_extension(filename):
            return False

        try:
            text = header_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            return False

        text_lower = text.lower()
        return "doble" in text_lower or "m4000" in text_lower or "m5000" in text_lower

    def parse(self, filename: str, fileobj: BinaryIO) -> ParseResult:
        warnings: list[str] = []
        raw = fileobj.read()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")

        lines = text.strip().splitlines()
        metadata: dict = {}

        data_start = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            kv = re.match(r"^([A-Za-z\s_]+)\s*[:=]\s*(.+)$", stripped)
            if kv:
                metadata[kv.group(1).strip()] = kv.group(2).strip()
                continue

            parts = re.split(r"[,\t;]+", stripped)
            try:
                float(parts[0])
                data_start = i
                break
            except (ValueError, IndexError):
                continue

        frequency: list[float] = []
        magnitude: list[float] = []
        phase: list[float] = []
        bad_rows = 0

        for line in lines[data_start:]:
            parts = re.split(r"[,\t;]+", line.strip())
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
                errors=["No valid data found in Doble file"],
                original_filename=filename,
                detected_format="doble",
            )

        data = RawFRAData(
            frequency_hz=frequency,
            magnitude_db=magnitude,
            phase_degrees=phase if phase else None,
            vendor="Doble",
            extra_metadata=metadata,
        )

        for key, val in metadata.items():
            k = key.lower()
            if "serial" in k:
                data.serial_number = val
            elif "date" in k:
                data.measurement_date = val
            elif "winding" in k:
                data.winding_config = val
            elif "temp" in k:
                try:
                    data.temperature_celsius = float(re.sub(r"[^\d.\-]", "", val))
                except ValueError:
                    pass

        return ParseResult(
            status=ParseStatus.SUCCESS if bad_rows == 0 else ParseStatus.PARTIAL,
            data=data,
            warnings=warnings,
            original_filename=filename,
            detected_format="doble",
        )
