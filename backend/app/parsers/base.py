"""
Abstract base parser for FRA data files.

All vendor-specific and generic parsers inherit from BaseFRAParser
and implement detect() and parse() methods.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import BinaryIO


class ParseStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class RawFRAData:
    """Raw parsed FRA data before validation / normalization."""
    frequency_hz: list[float] = field(default_factory=list)
    magnitude_db: list[float] = field(default_factory=list)
    phase_degrees: list[float] | None = None

    # Metadata extracted from the file
    vendor: str | None = None
    winding_config: str | None = None
    measurement_date: str | None = None
    temperature_celsius: float | None = None
    serial_number: str | None = None
    transformer_name: str | None = None
    notes: str | None = None
    extra_metadata: dict = field(default_factory=dict)


@dataclass
class ParseResult:
    """Result of a parse operation."""
    status: ParseStatus
    data: RawFRAData | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    original_filename: str | None = None
    detected_format: str | None = None

    @property
    def is_ok(self) -> bool:
        return self.status in (ParseStatus.SUCCESS, ParseStatus.PARTIAL)


class BaseFRAParser(ABC):
    """
    Abstract base class for all FRA file parsers.

    Subclasses must implement:
        - detect(filepath, content) -> bool
        - parse(filepath, fileobj) -> ParseResult
    """

    # Human-readable name of the parser / vendor
    name: str = "base"
    supported_extensions: tuple[str, ...] = ()

    def can_handle_extension(self, filename: str) -> bool:
        """Quick check based on file extension."""
        suffix = Path(filename).suffix.lower()
        return suffix in self.supported_extensions

    @abstractmethod
    def detect(self, filename: str, header_bytes: bytes) -> bool:
        """
        Return True if this parser can handle the given file.

        Parameters
        ----------
        filename : str
            Original filename (used for extension matching).
        header_bytes : bytes
            First ~4 KB of the file for content sniffing.
        """
        ...

    @abstractmethod
    def parse(self, filename: str, fileobj: BinaryIO) -> ParseResult:
        """
        Parse the file and return structured FRA data.

        Parameters
        ----------
        filename : str
            Original filename.
        fileobj : BinaryIO
            Seekable file-like object opened in binary mode.
        """
        ...


class ParserRegistry:
    """
    Registry that holds all available parsers and selects
    the best match for a given file.
    """

    def __init__(self) -> None:
        self._parsers: list[BaseFRAParser] = []

    def register(self, parser: BaseFRAParser) -> None:
        self._parsers.append(parser)

    def detect_parser(self, filename: str, header_bytes: bytes) -> BaseFRAParser | None:
        """
        Try each registered parser and return the first one that claims
        it can handle the file.  Vendor-specific parsers are tried first
        (anything other than 'generic_csv' / 'generic_xml'), then fallback
        to generic parsers.
        """
        vendor_parsers = [p for p in self._parsers if "generic" not in p.name]
        generic_parsers = [p for p in self._parsers if "generic" in p.name]

        for parser in vendor_parsers + generic_parsers:
            try:
                if parser.detect(filename, header_bytes):
                    return parser
            except Exception:
                continue
        return None

    @property
    def parsers(self) -> list[BaseFRAParser]:
        return list(self._parsers)
