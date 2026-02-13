"""
FRA Parsers package.

Registers all available parsers in a global ParserRegistry instance.
The registry auto-detects the correct parser for uploaded files.
"""
from app.parsers.base import (
    BaseFRAParser,
    ParserRegistry,
    ParseResult,
    ParseStatus,
    RawFRAData,
)
from app.parsers.csv_parser import GenericCSVParser
from app.parsers.xml_parser import GenericXMLParser
from app.parsers.omicron_parser import OmicronParser
from app.parsers.megger_parser import MeggerFRAXParser
from app.parsers.doble_parser import DobleParser

# Global parser registry — vendor-specific parsers first, then generic fallbacks
registry = ParserRegistry()
registry.register(OmicronParser())
registry.register(MeggerFRAXParser())
registry.register(DobleParser())
registry.register(GenericCSVParser())
registry.register(GenericXMLParser())

__all__ = [
    "registry",
    "BaseFRAParser",
    "ParserRegistry",
    "ParseResult",
    "ParseStatus",
    "RawFRAData",
    "GenericCSVParser",
    "GenericXMLParser",
    "OmicronParser",
    "MeggerFRAXParser",
    "DobleParser",
]