"""
压缩模块 / Compression Module

三语压缩支持 (Trilingual Compression Support):
- AAAK Dialect for English compression
- 文簡 (Wenjian) Dialect for Chinese compression
- 繁簡 (Traditional/Simplified) bidirectional conversion
- Auto language detection
- Pluggable dialect registry

Usage:
    from mempalace_tri.compressor import Compressor, CompressorMode

    compressor = Compressor()

    # Auto-detect language
    result = compressor.compress("我們決定使用PostgreSQL")
    # → 議用PostgreSQL

    result = compressor.compress("The team decided to use GPT-4")
    # → team dec use GPT-4

    # Registry for pluggable dialects
    from mempalace_tri.compressor.registry import DialectRegistry, compress_auto
    reg = DialectRegistry.default()
    dialect_name, compressed = compress_auto("我们决定迁移")
"""

from .base import Compressor, CompressorMode, CompressResult
from .lang_detect import LanguageDetector, detect_language
from .aaak import AAAKDialect
from .wenjian import WenjianCompressor
from .s2t_converter import (
    convert_text,
    full_convert,
    SIMPLIFIED_TO_TRADITIONAL,
    TRADITIONAL_TO_SIMPLIFIED,
)

# Registry exports
from .registry import (
    DialectRegistry,
    DialectBackend,
    DialectCapability,
    DialectInfo,
    get_registry,
    create_dialect,
    compress_auto,
    list_available,
)

__all__ = [
    # Core
    "Compressor",
    "CompressorMode",
    "CompressResult",
    # Language detection
    "LanguageDetector",
    "detect_language",
    # Dialect backends
    "AAAAKDialect",
    "WenjianCompressor",
    # S2T conversion
    "convert_text",
    "full_convert",
    "SIMPLIFIED_TO_TRADITIONAL",
    "TRADITIONAL_TO_SIMPLIFIED",
    # Registry
    "DialectRegistry",
    "DialectBackend",
    "DialectCapability",
    "DialectInfo",
    "get_registry",
    "create_dialect",
    "compress_auto",
    "list_available",
]

__version__ = "1.0.0"