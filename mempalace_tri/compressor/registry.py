"""
压缩器注册表 / Compressor Registry

Dialect registry and factory pattern for pluggable compression backends.
Provides a unified interface to discover, register, and instantiate
compression dialects (AAAK, Wenjian-CN, Wenjian-TW).

Usage:
    from mempalace_tri.compressor.registry import DialectRegistry

    # Get default registry
    reg = DialectRegistry.default()

    # List available dialects
    print(reg.list_dialects())  # ["aaak", "wenjian_zh_cn", "wenjian_zh_tw"]

    # Create compressor for a specific mode
    compressor = reg.create("aaak")
    compressor = reg.create("wenjian_zh_cn", entities={"Alice": "ALC"})

    # Auto-select best dialect for text
    best = reg.best_for("我们决定迁移")  # "wenjian_zh_cn"
    best = reg.best_for("The team decided")  # "aaak"
"""

from __future__ import annotations

import importlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from .lang_detect import detect_language, detect_auto_compress_mode

logger = logging.getLogger(__name__)


class DialectCapability(str, Enum):
    """Capabilities a dialect compressor can provide."""
    COMPRESS = "compress"
    EXPAND = "expand"
    ENTITY_DETECTION = "entities"
    EMOTION_DETECTION = "emotions"
    STATISTICS = "stats"


@dataclass
class DialectInfo:
    """Metadata about a registered dialect."""
    name: str
    display_name: str
    description: str
    capabilities: List[DialectCapability] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    module: str = ""
    class_name: str = ""
    factory: Optional[Callable] = None
    priority: int = 0

    def __str__(self) -> str:
        caps = ", ".join(c.value for c in self.capabilities)
        return f"{self.display_name} [{self.name}] caps={caps}"


# ─── Base Dialect Interface ───

class DialectBackend(ABC):
    """Abstract base class for all compression dialects."""

    @abstractmethod
    def compress(self, text: str, **kwargs) -> str:
        """Compress text using this dialect."""
        ...

    def expand(self, compressed: str, **kwargs) -> str:
        """Expand compressed text back to readable form."""
        return compressed

    def stats(self, original: str, compressed: str) -> dict:
        """Return compression statistics."""
        return {
            "original_chars": len(original),
            "compressed_chars": len(compressed),
            "ratio": round(len(original) / max(len(compressed), 1), 2),
        }


# ─── Registry ───

class DialectRegistry:
    """Registry for compression dialect backends."""

    _instance: Optional["DialectRegistry"] = None
    _initialized: bool = False

    def __init__(self):
        self._dialects: Dict[str, DialectInfo] = {}

    @classmethod
    def default(cls) -> "DialectRegistry":
        """Get the default (singleton) registry, initializing if needed."""
        if cls._instance is None:
            cls._instance = cls()
        if not cls._initialized:
            cls._instance._register_defaults()
            cls._initialized = True
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (for testing)."""
        cls._instance = None
        cls._initialized = False

    # ─── Registration ───

    def register(
        self,
        name: str,
        *,
        display_name: str = "",
        description: str = "",
        capabilities: List[DialectCapability] = None,
        languages: List[str] = None,
        module: str = "",
        class_name: str = "",
        factory: Callable = None,
        priority: int = 0,
    ) -> DialectInfo:
        """Register a new dialect backend."""
        info = DialectInfo(
            name=name,
            display_name=display_name or name,
            description=description,
            capabilities=capabilities or [DialectCapability.COMPRESS],
            languages=languages or [],
            module=module,
            class_name=class_name,
            factory=factory,
            priority=priority,
        )
        self._dialects[name] = info
        logger.debug("Registered dialect: %s", name)
        return info

    def unregister(self, name: str) -> bool:
        """Unregister a dialect by name."""
        if name in self._dialects:
            del self._dialects[name]
            return True
        return False

    def has(self, name: str) -> bool:
        """Check if a dialect is registered."""
        return name in self._dialects

    def get_info(self, name: str) -> Optional[DialectInfo]:
        """Get metadata for a registered dialect."""
        return self._dialects.get(name)

    def list_dialects(self) -> List[str]:
        """List all registered dialect names."""
        return list(self._dialects.keys())

    def list_dialects_with_info(self) -> List[DialectInfo]:
        """List all registered dialects with metadata."""
        return list(self._dialects.values())

    # ─── Factory ───

    def create(self, name: str, **kwargs) -> DialectBackend:
        """Create a configured instance of a dialect backend."""
        info = self._dialects.get(name)
        if info is None:
            available = ", ".join(self.list_dialects())
            raise ValueError(f"Unknown dialect '{name}'. Available: {available}")

        if info.factory:
            try:
                return info.factory(**kwargs)
            except Exception as e:
                raise RuntimeError(f"Factory for '{name}' failed: {e}") from e

        if info.module and info.class_name:
            try:
                mod = importlib.import_module(info.module)
                cls = getattr(mod, info.class_name)
                return cls(**kwargs)
            except Exception as e:
                raise RuntimeError(
                    f"Cannot instantiate '{name}' from {info.module}.{info.class_name}: {e}"
                ) from e

        raise RuntimeError(f"Dialect '{name}' has no factory or module configured")

    # ─── Auto-Selection ───

    def best_for(self, text: str) -> str:
        """Select the best dialect for the given text."""
        mode = detect_auto_compress_mode(text)
        if mode in self._dialects:
            return mode

        lang = detect_language(text)
        candidates = [
            (info.priority, info)
            for info in self._dialects.values()
            if lang in info.languages or "all" in info.languages
        ]
        if candidates:
            candidates.sort(key=lambda x: -x[0])
            return candidates[0][1].name

        return "aaak" if "aaak" in self._dialects else self.list_dialects()[0]

    def compress_with_best(self, text: str, **kwargs) -> Tuple[str, str]:
        """Compress text using the auto-selected best dialect."""
        name = self.best_for(text)
        backend = self.create(name, **kwargs)
        compressed = backend.compress(text)
        return name, compressed

    # ─── Default Registration ───

    def _register_defaults(self) -> None:
        """Register the default set of compression dialects."""

        self.register(
            name="aaak",
            display_name="AAAK / 英语压缩",
            description="Structured symbolic summary for English text.",
            capabilities=[
                DialectCapability.COMPRESS,
                DialectCapability.ENTITY_DETECTION,
                DialectCapability.EMOTION_DETECTION,
                DialectCapability.STATISTICS,
            ],
            languages=["en", "all"],
            module="mempalace_tri.compressor.aaak",
            class_name="AAAKDialect",
            priority=10,
        )

        self.register(
            name="wenjian_zh_cn",
            display_name="文简 / 简体中文压缩",
            description="Chinese symbolic compression for Simplified Chinese.",
            capabilities=[
                DialectCapability.COMPRESS,
                DialectCapability.EXPAND,
                DialectCapability.STATISTICS,
            ],
            languages=["zh_cn", "zh"],
            module="mempalace_tri.compressor.wenjian",
            class_name="WenjianCompressor",
            priority=20,
        )

        self.register(
            name="wenjian_zh_tw",
            display_name="文簡 / 繁体中文压缩",
            description="Chinese symbolic compression for Traditional Chinese.",
            capabilities=[
                DialectCapability.COMPRESS,
                DialectCapability.EXPAND,
                DialectCapability.STATISTICS,
            ],
            languages=["zh_tw", "zh"],
            module="mempalace_tri.compressor.wenjian",
            class_name="WenjianCompressor",
            priority=20,
        )

        self.register(
            name="auto",
            display_name="自动 / Auto-Detect",
            description="Auto-detects language and routes to appropriate dialect.",
            capabilities=[
                DialectCapability.COMPRESS,
                DialectCapability.EXPAND,
            ],
            languages=["en", "zh_cn", "zh_tw", "all"],
            factory=lambda **kwargs: _AutoDialectBackend(**kwargs),
            priority=30,
        )

        logger.info(
            "Dialect registry initialized with %d dialects: %s",
            len(self._dialects),
            ", ".join(self.list_dialects()),
        )


# ─── Auto-Detect Backend Wrapper ───

class _AutoDialectBackend(DialectBackend):
    """Backend that auto-selects the best dialect per call."""

    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._reg = DialectRegistry.default()

    def compress(self, text: str, **override_kwargs) -> str:
        """Compress using auto-detected dialect."""
        name = self._reg.best_for(text)
        backend = self._reg.create(name, **{**self._kwargs, **override_kwargs})
        return backend.compress(text, **override_kwargs)

    def expand(self, compressed: str, **kwargs) -> str:
        """Expand - best-effort without knowing original dialect."""
        return compressed

    def stats(self, original: str, compressed: str) -> dict:
        """Basic stats for auto mode."""
        return {
            "original_chars": len(original),
            "compressed_chars": len(compressed),
            "ratio": round(len(original) / max(len(compressed), 1), 2),
            "dialect": self._reg.best_for(original),
        }


# ─── Convenience Functions ───

def get_registry() -> DialectRegistry:
    """Get the default registry instance."""
    return DialectRegistry.default()


def create_dialect(name: str, **kwargs) -> DialectBackend:
    """Shortcut to create a dialect backend."""
    return get_registry().create(name, **kwargs)


def compress_auto(text: str, **kwargs) -> Tuple[str, str]:
    """Compress text using auto-detected best dialect."""
    return get_registry().compress_with_best(text, **kwargs)


def list_available() -> List[str]:
    """List all available dialect names."""
    return get_registry().list_dialects()