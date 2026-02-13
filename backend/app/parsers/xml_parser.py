"""
Generic XML parser for FRA measurement files.

Handles XML files with frequency/magnitude/phase data in various
common structures:
  - <measurement><point><freq/><mag/><phase/></point></measurement>
  - <fra_data><data_point freq="..." mag="..." /></fra_data>
  - And other similar structures via recursive element discovery.
"""
import re
import xml.etree.ElementTree as ET
from typing import BinaryIO

from app.parsers.base import BaseFRAParser, ParseResult, ParseStatus, RawFRAData


# Element / attribute name patterns
_FREQ_PAT = re.compile(r"(freq|frequency|f_hz|freq_hz)", re.IGNORECASE)
_MAG_PAT = re.compile(r"(mag|magnitude|amplitude|gain|transfer|impedance|tf)", re.IGNORECASE)
_PHASE_PAT = re.compile(r"(phase|angle|arg)", re.IGNORECASE)

# Metadata element patterns
_DATE_PAT = re.compile(r"(date|timestamp|time|measured)", re.IGNORECASE)
_TEMP_PAT = re.compile(r"(temp|temperature)", re.IGNORECASE)
_SERIAL_PAT = re.compile(r"(serial|serial_number|sn)", re.IGNORECASE)
_WINDING_PAT = re.compile(r"(winding|config|configuration)", re.IGNORECASE)


def _find_data_elements(root: ET.Element) -> list[ET.Element]:
    """
    Recursively find the deepest repeated sibling elements
    that likely represent data points.
    """
    # Group children by tag
    tag_groups: dict[str, list[ET.Element]] = {}
    for child in root:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        tag_groups.setdefault(tag, []).append(child)

    # Find the tag with the most repetitions (likely data points)
    best_tag = ""
    best_count = 0
    for tag, elements in tag_groups.items():
        if len(elements) > best_count:
            best_tag = tag
            best_count = len(elements)

    if best_count >= 5:
        return tag_groups[best_tag]

    # Recurse into children
    for child in root:
        result = _find_data_elements(child)
        if result:
            return result

    return []


def _extract_value(element: ET.Element, pattern: re.Pattern) -> float | None:
    """
    Extract a numeric value from a child element or attribute
    whose name matches the given pattern.
    """
    # Check attributes
    for attr_name, attr_val in element.attrib.items():
        clean_name = attr_name.split("}")[-1] if "}" in attr_name else attr_name
        if pattern.search(clean_name):
            try:
                return float(attr_val)
            except ValueError:
                pass

    # Check child elements
    for child in element:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if pattern.search(tag) and child.text:
            try:
                return float(child.text.strip())
            except ValueError:
                pass

    return None


def _extract_metadata(root: ET.Element) -> dict:
    """Extract metadata from non-data elements in the XML."""
    meta: dict = {}

    def _recurse(el: ET.Element, depth: int = 0) -> None:
        if depth > 4:
            return
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag

        # Check element text
        text = (el.text or "").strip()
        if text:
            if _DATE_PAT.search(tag):
                meta["measurement_date"] = text
            elif _TEMP_PAT.search(tag):
                meta["temperature"] = text
            elif _SERIAL_PAT.search(tag):
                meta["serial_number"] = text
            elif _WINDING_PAT.search(tag):
                meta["winding_config"] = text

        # Check attributes
        for attr_name, attr_val in el.attrib.items():
            clean = attr_name.split("}")[-1] if "}" in attr_name else attr_name
            if _DATE_PAT.search(clean):
                meta["measurement_date"] = attr_val
            elif _TEMP_PAT.search(clean):
                meta["temperature"] = attr_val
            elif _SERIAL_PAT.search(clean):
                meta["serial_number"] = attr_val
            elif _WINDING_PAT.search(clean):
                meta["winding_config"] = attr_val

        for child in el:
            _recurse(child, depth + 1)

    _recurse(root)
    return meta


class GenericXMLParser(BaseFRAParser):
    """
    Parses generic XML files containing FRA data.

    Detection heuristics:
      - .xml extension
      - Content starts with <?xml or < root element
    """

    name = "generic_xml"
    supported_extensions = (".xml",)

    def detect(self, filename: str, header_bytes: bytes) -> bool:
        if not self.can_handle_extension(filename):
            return False

        try:
            text = header_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            return False

        stripped = text.lstrip()
        return stripped.startswith("<?xml") or stripped.startswith("<")

    def parse(self, filename: str, fileobj: BinaryIO) -> ParseResult:
        warnings: list[str] = []

        raw = fileobj.read()
        try:
            root = ET.fromstring(raw)
        except ET.ParseError as e:
            return ParseResult(
                status=ParseStatus.FAILED,
                errors=[f"Invalid XML: {e}"],
                original_filename=filename,
                detected_format="xml",
            )

        # Extract metadata
        meta = _extract_metadata(root)

        # Find repeating data-point elements
        data_elements = _find_data_elements(root)
        if not data_elements:
            return ParseResult(
                status=ParseStatus.FAILED,
                errors=["Could not find repeating data-point elements in XML"],
                original_filename=filename,
                detected_format="xml",
            )

        # Parse each data element
        frequency: list[float] = []
        magnitude: list[float] = []
        phase: list[float] = []
        bad_points = 0

        for el in data_elements:
            f = _extract_value(el, _FREQ_PAT)
            m = _extract_value(el, _MAG_PAT)

            if f is None or m is None:
                bad_points += 1
                continue

            frequency.append(f)
            magnitude.append(m)

            p = _extract_value(el, _PHASE_PAT)
            if p is not None:
                phase.append(p)

        if bad_points > 0:
            warnings.append(f"Skipped {bad_points} data point(s) missing freq or magnitude")

        if len(frequency) == 0:
            return ParseResult(
                status=ParseStatus.FAILED,
                errors=["No valid data points extracted from XML"],
                original_filename=filename,
                detected_format="xml",
            )

        data = RawFRAData(
            frequency_hz=frequency,
            magnitude_db=magnitude,
            phase_degrees=phase if phase else None,
            vendor="Generic XML",
            measurement_date=meta.get("measurement_date"),
            serial_number=meta.get("serial_number"),
            winding_config=meta.get("winding_config"),
            extra_metadata=meta,
        )

        # Temperature
        temp_str = meta.get("temperature")
        if temp_str:
            try:
                data.temperature_celsius = float(re.sub(r"[^\d.\-]", "", temp_str))
            except ValueError:
                pass

        status = ParseStatus.SUCCESS if bad_points == 0 else ParseStatus.PARTIAL
        return ParseResult(
            status=status,
            data=data,
            warnings=warnings,
            original_filename=filename,
            detected_format="xml",
        )
