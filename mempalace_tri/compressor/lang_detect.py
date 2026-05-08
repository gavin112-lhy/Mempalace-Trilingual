"""
语言检测 / Language Detection

Auto-detect text language for appropriate compression selection.
Supports: Simplified Chinese, Traditional Chinese, English, and mixed.

Usage:
    from mempalace_tri.compressor.lang_detect import detect_language, LanguageDetector
    
    lang = detect_language("我們決定使用PostgreSQL")
    # → "zh_tw"
    
    lang = detect_language("The team decided to use GPT-4")
    # → "en"
    
    detector = LanguageDetector()
    lang, confidence = detector.detect(text)
"""

from __future__ import annotations

import re
from typing import Tuple, Dict
from enum import Enum


class Language(Enum):
    """Detected language codes."""
    SIMPLIFIED = "zh_cn"
    TRADITIONAL = "zh_tw"
    ENGLISH = "en"
    MIXED = "mixed"


# CJK Unified Ideographs range
_CJK_RANGE = set(range(0x4E00, 0x9FFF + 1))

# Traditional-only common characters (not in Simplified)
_TRADITIONAL_CHARS = set("龜龍臺麵發條後鬚夠鬆鬱龍")

# Simplified-only common characters
_SIMPLIFIED_CHARS = set("龟龙台麵发条后须够松郁")

# Common English patterns
_EN_PATTERN = re.compile(r"[a-zA-Z]{3,}")


def detect_language(text: str) -> str:
    """Auto-detect the primary language of the text.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Language code: "zh_cn", "zh_tw", "en", or "mixed"
    
    Example:
        >>> detect_language("我們決定使用PostgreSQL")
        'zh_tw'
        >>> detect_language("我们决定使用PostgreSQL")
        'zh_cn'
        >>> detect_language("The team decided to use GPT-4")
        'en'
    """
    if not text or not text.strip():
        return "en"  # default

    cn_chars = 0
    trad_chars = 0
    sim_chars = 0
    en_words = 0

    for char in text:
        code = ord(char)
        if code in _CJK_RANGE:
            cn_chars += 1
            if char in _TRADITIONAL_CHARS:
                trad_chars += 1
            if char in _SIMPLIFIED_CHARS:
                sim_chars += 1
        elif _EN_PATTERN.fullmatch(char):
            en_words += 1

    total = cn_chars + en_words
    if total == 0:
        return "en"

    cn_ratio = cn_chars / total
    en_ratio = en_words / total

    # If more Chinese than English
    if cn_ratio > en_ratio:
        if trad_chars > sim_chars:
            return "zh_tw"
        return "zh_cn"

    # If more English than Chinese
    if en_ratio > cn_ratio:
        return "en"

    # Mixed: check primary language
    if trad_chars > sim_chars:
        return "zh_tw"
    return "zh_cn"


class LanguageDetector:
    """Language detector with confidence scoring."""

    def __init__(self, thresholds: Dict[str, float] = None):
        self.thresholds = thresholds or {
            "chinese": 0.3,   # Minimum Chinese ratio to be detected as Chinese
            "english": 0.5,   # Minimum English ratio to be detected as English
        }

    def detect(self, text: str) -> Tuple[str, float]:
        """Detect language with confidence.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (language_code, confidence)
        """
        if not text or not text.strip():
            return ("en", 1.0)

        cn_chars = sum(1 for c in text if ord(c) in _CJK_RANGE)
        en_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        total = max(len(text), 1)

        cn_ratio = cn_chars / total
        en_ratio = en_chars / total

        # Detect Traditional vs Simplified
        trad_chars = sum(1 for c in text if c in _TRADITIONAL_CHARS)
        sim_chars = sum(1 for c in text if c in _SIMPLIFIED_CHARS)

        if cn_ratio > self.thresholds["chinese"] and cn_ratio > en_ratio:
            if trad_chars > sim_chars:
                return ("zh_tw", min(cn_ratio * 1.5, 1.0))
            return ("zh_cn", min(cn_ratio * 1.5, 1.0))

        if en_ratio > self.thresholds["english"]:
            return ("en", min(en_ratio * 1.5, 1.0))

        # Fallback: return the dominant language
        if cn_chars > en_chars:
            if trad_chars > sim_chars:
                return ("zh_tw", cn_ratio)
            return ("zh_cn", cn_ratio)
        return ("en", en_ratio)

    def detect_auto_compress_mode(self, text: str) -> str:
        """Detect which compression mode to use.
        
        Args:
            text: Input text
            
        Returns:
            Mode: "aaak" for English, "wenjian_zh_cn" for Simplified,
                  "wenjian_zh_tw" for Traditional
        """
        lang, _ = self.detect(text)
        if lang == "en":
            return "aaak"
        elif lang == "zh_tw":
            return "wenjian_zh_tw"
        return "wenjian_zh_cn"


# Convenience function
def detect_auto_compress_mode(text: str) -> str:
    """Auto-detect compression mode for text.
    
    Returns:
        "aaak", "wenjian_zh_cn", or "wenjian_zh_tw"
    """
    detector = LanguageDetector()
    return detector.detect_auto_compress_mode(text)