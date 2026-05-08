"""
压缩器基类 / Base Compressor

Unified interface for all compression modes.
Auto-detects language and routes to appropriate dialect.

Usage:
    from mempalace_tri.compressor import Compressor

    compressor = Compressor()

    # Auto-detect mode
    result = compressor.compress("我們決定使用PostgreSQL")
    # → uses Wenjian (Chinese)

    result = compressor.compress("The team decided to use GPT-4")
    # → uses AAAK (English)

    # Explicit mode
    result = compressor.compress("text", mode="aaak")
    result = compressor.compress("text", mode="wenjian_zh_cn")
    result = compressor.compress("text", mode="wenjian_zh_tw")
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional, List
from dataclasses import dataclass, field

from .lang_detect import detect_language, LanguageDetector, detect_auto_compress_mode
from .aaak import AAAKDialect
from .wenjian import WenjianCompressor, WenjianEntry
from .s2t_converter import convert_text


class CompressorMode(str, Enum):
    """Compression mode enumeration."""
    AUTO = "auto"
    AAAK = "aaak"
    WENJIAN_SIMPLIFIED = "wenjian_zh_cn"
    WENJIAN_TRADITIONAL = "wenjian_zh_tw"

    @classmethod
    def from_string(cls, mode: str):
        """Convert string to CompressorMode."""
        mapping = {
            "auto": cls.AUTO,
            "aaak": cls.AAAK,
            "wenjian": cls.WENJIAN_SIMPLIFIED,
            "wenjian_zh_cn": cls.WENJIAN_SIMPLIFIED,
            "wenjian_zh_tw": cls.WENJIAN_TRADITIONAL,
            "zh_cn": cls.WENJIAN_SIMPLIFIED,
            "zh_tw": cls.WENJIAN_TRADITIONAL,
        }
        return mapping.get(mode.lower(), cls.AUTO)


@dataclass
class CompressResult:
    """Result of text compression."""
    compressed: str                    # Compressed text
    original: str                      # Original text
    mode: str                          # Compression mode used (aaak, wenjian_zh_cn, etc.)
    lang: str                          # Detected language
    compression_stats: Dict = field(default_factory=dict)
    entry: Optional[WenjianEntry] = None

    def display(self) -> str:
        """Display the compressed result."""
        return self.compressed

    def to_dict(self) -> dict:
        """Serialize result to dict."""
        return {
            "compressed": self.compressed,
            "original": self.original,
            "mode": self.mode,
            "lang": self.lang,
            "stats": self.compression_stats,
        }


class Compressor:
    """Unified text compressor for trilingual input.

    Auto-detects language and uses appropriate compression:
    - English → AAAK Dialect
    - Simplified Chinese → 文簡 (Wenjian)
    - Traditional Chinese → 文簡 (Wenjian)

    Usage:
        compressor = Compressor()

        # Auto-detect (recommended)
        result = compressor.compress("我們團隊決定使用PostgreSQL")
        # → CompressResult(compressed="★★★[定] 議用PostgreSQL", mode="wenjian_zh_tw", lang="zh_tw")

        # Explicit mode
        result = compressor.compress("text", mode="aaak")

        # Get detailed entry
        entry = compressor.compress_to_entry("text", mode="wenjian_zh_cn")
        # → WenjianEntry(importance="★★★", status="[定]", content="議用PostgreSQL")
    """

    def __init__(
        self,
        entities: Dict[str, str] = None,
        skip_names: List[str] = None,
        default_mode: str = "auto",
    ):
        """
        Args:
            entities: Entity name → code mappings (for AAAK)
            skip_names: Names to skip
            default_mode: Default compression mode ("auto", "aaak", "wenjian_zh_cn", "wenjian_zh_tw")
        """
        self.entities = entities or {}
        self.skip_names = skip_names or []
        self.default_mode = default_mode
        self._detector = LanguageDetector()
        self._aaak = AAAKDialect(entities=entities, skip_names=skip_names)
        self._wenjian = WenjianCompressor()

    def compress(self, text: str, mode: str = None, **kwargs) -> CompressResult:
        """Compress text using auto-detection or explicit mode.

        Args:
            text: Input text (supports 简/繁/en)
            mode: Compression mode ("auto", "aaak", "wenjian_zh_cn", "wenjian_zh_tw")

        Returns:
            CompressResult with compressed text and metadata

        Examples:
            >>> c = Compressor()
            >>> result = c.compress("我們決定使用PostgreSQL")
            >>> print(result.compressed)
            '★★★[定] 議用PostgreSQL'
            >>> print(result.mode)
            'wenjian_zh_tw'
            >>> print(result.lang)
            'zh_tw'
        """
        mode = mode or self.default_mode

        if mode == "auto":
            mode = detect_auto_compress_mode(text)

        # Route to appropriate dialect
        if mode.startswith("wenjian"):
            return self._compress_wenjian(text, mode)
        elif mode == "aaak":
            return self._compress_aaak(text)
        else:
            raise ValueError(f"Unknown compression mode: {mode}. Use 'auto', 'aaak', 'wenjian_zh_cn', or 'wenjian_zh_tw'")

    def compress_to_entry(self, text: str, mode: str = None) -> WenjianEntry:
        """Compress text to a WenjianEntry (always uses 文簡 format).

        Args:
            text: Input text
            mode: Script mode ("wenjian_zh_cn", "wenjian_zh_tw", or "auto")

        Returns:
            WenjianEntry dataclass
        """
        if mode is None or mode == "auto":
            mode = detect_auto_compress_mode(text)
        if not mode.startswith("wenjian"):
            mode = "wenjian_zh_cn"
        return self._wenjian.compress_entry(self._wenjian._make_entry(text, mode))

    def expand(self, compressed: str, mode: str = None) -> str:
        """Expand compressed text back to readable form.

        Args:
            compressed: Compressed text
            mode: Compression mode (auto-detects if not provided)

        Returns:
            Expanded hint text
        """
        if mode is None:
            # Auto-detect mode from content
            if any(c in compressed for c in "★★★★"):
                mode = "wenjian_zh_cn"
            else:
                mode = "aaak"

        if mode.startswith("wenjian"):
            return self._wenjian.expand(compressed)
        return f"(AAAK: {compressed})"

    def detect_language(self, text: str) -> str:
        """Detect language of text."""
        return detect_language(text)

    def detect_compress_mode(self, text: str) -> str:
        """Detect which compression mode to use."""
        return detect_auto_compress_mode(text)

    def convert_script(self, text: str, to_traditional: bool = True) -> str:
        """Convert text between Simplified and Traditional Chinese."""
        return convert_text(text, to_traditional=to_traditional)

    def _compress_wenjian(self, text: str, mode: str) -> CompressResult:
        """Compress using 文簡."""
        script = mode  # "wenjian_zh_cn" or "wenjian_zh_tw"
        entry = self._wenjian._make_entry(text, script)
        entry = self._wenjian.compress_entry(entry)
        compressed = self._wenjian.format_entry(entry)
        stats = self._wenjian.compression_stats(text, compressed)
        lang = "zh_tw" if "tw" in mode else "zh_cn"

        return CompressResult(
            compressed=compressed,
            original=text,
            mode=mode,
            lang=lang,
            compression_stats=stats,
        )

    def _compress_aaak(self, text: str) -> CompressResult:
        """Compress using AAAK Dialect."""
        compressed = self._aaak.compress(text)
        stats = self._aaak.compression_stats(text, compressed)

        return CompressResult(
            compressed=compressed,
            original=text,
            mode="aaak",
            lang="en",
            compression_stats=stats,
        )

    def save_entity_config(self, path: str) -> None:
        """Save entity config to JSON."""
        self._aaak.save_config(path)

    @classmethod
    def load_entity_config(cls, path: str) -> "Compressor":
        """Load entity config from JSON."""
        aaak = AAAKDialect.from_config(path)
        return cls(entities=aaak.entity_codes, skip_names=aaak.skip_names)