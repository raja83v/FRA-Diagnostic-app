"""
Megger FRAX parser.

Handles Megger FRAX-series exported CSV files. FRAX exports
typically include a header section with device/measurement info
followed by comma-separated data.
"""
import re
from typing import BinaryIO

from app.parsers.base import BaseFRAParser, ParseResult, ParseStatus, RawFRAData


class MeggerFRAXParser(BaseFRAParser):
    """
    Parser for Megger FRAX exported files.

    Megger FRAX CSV exports typically contain:
      - Header block with "FRAX" or "Megger" identifier
      - Metadata section (serial, date, winding, temperature)
      - CSV data: Frequency, Magnitude, Phase
    """

    name = "megger_frax"
    supported_extensions = (".csv", ".txt", ".frax", ".xml")

    def detect(self, filename: str, header_bytes: bytes) -> bool:
        if not self.can_handle_extension(filename):
            return False

        try:
            text = header_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            return False

        text_lower = text.lower()
        return "megger" in text_lower or "frax" in text_lower

    def parse(self, filename: str, fileobj: BinaryIO) -> ParseResult:
        warnings: list[str] = []
        raw = fileobj.read()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")

        lines = text.strip().splitlines()
        metadata: dict = {}

        # Extract metadata from header lines
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

        # Parse data
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
                errors=["No valid data found in Megger FRAX file"],
                original_filename=filename,
                detected_format="megger_frax",
            )

        data = RawFRAData(
            frequency_hz=frequency,
            magnitude_db=magnitude,
            phase_degrees=phase if phase else None,
            vendor="Megger FRAX",
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
            detected_format="megger_frax",
        )
