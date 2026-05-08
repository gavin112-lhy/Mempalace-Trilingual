"""
wenjian.py — 文簡 Chinese Compression Dialect

文簡 (Wenjian) is a Classical Chinese shorthand dialect for AI memory systems.
- Not for human reading, for fast AI processing
- Based on modern Chinese but further compressed — removes all function particles
- Technical terms (API names, code, URLs) kept in English
- Supports both Traditional Chinese (default) and Simplified Chinese output

Wenjian compression for Chinese text:
    from mempalace_tri.compressor.wenjian import WenjianCompressor
    
    compressor = WenjianCompressor(traditional_mode=True)
    result = compressor.compress("我们团队决定使用PostgreSQL")
    # → 議隊用PostgreSQL (Traditional)
    
    compressor = WenjianCompressor(traditional_mode=False)
    result = compressor.compress("我们团队决定使用PostgreSQL")
    # → 议队用PostgreSQL (Simplified)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MemoryType(Enum):
    """記憶類型 / Memory types"""
    YI = "議"    # 決策/結論
    SHI = "事"   # 事件/里程碑
    DE = "得"    # 發現/洞見
    HAO = "好"   # 偏好/習慣
    CE = "策"    # 建議/方案


class Importance(Enum):
    """重要程度 / Importance levels"""
    LOW = "★"
    MED = "★★"
    HIGH = "★★★"
    KEY = "★★★"
    CRITICAL = "★★★★★"


class Status(Enum):
    """狀態標記 / Status markers"""
    DECIDED = "[定]"
    UNCERTAIN = "[疑]"
    DEPRECATED = "[廢]"
    IN_PROGRESS = "[進]"
    DONE = "[畢]"
    BLOCKED = "[阻]"


@dataclass
class WenjianEntry:
    """一條文簡記錄 / A single Wenjian entry"""
    memory_type: MemoryType
    content: str
    time_ref: Optional[str] = None
    status: Optional[Status] = None
    importance: Importance = Importance.MED
    raw_source: Optional[str] = None
    entities: list[str] = field(default_factory=list)

    def to_wenjian(self) -> str:
        """序列化為文簡格式 / Serialize to Wenjian format"""
        parts = [self.memory_type.value]
        if self.time_ref:
            parts.append(self.time_ref)
        parts.append(" ")
        parts.append(self.content)
        if not self.content.endswith("。"):
            parts.append("。")
        if self.status:
            parts.append(self.status.value)
        parts.append(self.importance.value)
        return "".join(parts)


class WenjianCompressor:
    """
    文簡壓縮引擎 - Wenjian Compression Engine
    
    Compresses modern Chinese/English content into Classical Chinese format.
    
    Args:
        traditional_mode: Output Traditional Chinese (default True)
        simplified_mode: Output Simplified Chinese (alternative)
    
    Example:
        # Traditional mode (default)
        compressor = WenjianCompressor(traditional_mode=True)
        result = compressor.compress("我們決定遷移認證服務")
        # → 議遷認證服務
        
        # Simplified mode
        compressor = WenjianCompressor(simplified_mode=True)
        result = compressor.compress("我们决定迁移认证服务")
        # → 议迁认证服务
    """

    # Replaced words: Chinese compound patterns → single characters
    REPLACEMENTS = [
        # Memory type headers
        (r"([^議事得好策])決定([^。,，]|$)", r"\1議\2"),
        (r"([^議事得好策])發現([^。,，]|$)", r"\1得\2"),
        (r"([^議事得好策])偏好([^。,，]|$)", r"\1好\2"),
        (r"([^議事得好策])建議([^。,，]|$)", r"\1策\2"),
        # Common compounds
        (r"團隊決定|团队决定", "隊議定"),
        (r"已經完成", "已畢"),
        (r"正在進行", "進行中"),
        (r"需要注意", "注"),
        (r"建議使用", "薦"),
        (r"因為(.{1,8})便宜", r"以\1故"),
        (r"因為(.{1,8})原因", r"以\1故"),
        (r"由於(.{1,8})原因", r"以\1故"),
        (r"相比(之下)?", "較"),
        (r"優於", "勝"),
        (r"劣於", "遜於"),
        (r"大家都同意", "眾從"),
        (r"所有人同意", "眾從"),
        # Domain-specific
        (r"文化", "化"),
        (r"悠久", "長"),
        (r"傳統", "統"),
        (r"遺產", "產"),
        (r"體現", "現"),
        (r"城市", "城"),
        (r"科技", "技"),
        (r"數位|数字", "數"),
        (r"網路|网络", "網"),
        (r"人工智能", "AI"),
        (r"綠色能源", "綠"),
        (r"發展", "展"),
        (r"改變", "變"),
        (r"建設", "建"),
        (r"歷史", "史"),
        # Short phrases
        (r"重新", "再"),
        (r"徹底", "盡"),
        (r"複雜", "雜"),
        (r"跨越", "跨"),
        (r"指向", "向"),
        (r"因為", "以"),
        (r"但是", "而"),
        (r"基於|基于", "依"),
        (r"對於", "對"),
        (r"關於", "關"),
        (r"根據", "根"),
    ]

    # Chinese function particles to remove
    REMOVABLE_PARTICLES = [
        "的", "了", "著", "過",
        "嗎", "呢", "啊", "呀", "哦", "嗯", "喎",
        "就是", "也就是說", "其實", "然後", "接下來", "所以說",
        "這個", "那個", "這些", "那些",
        "我們", "我们",
        "的",
    ]

    def __init__(self, traditional_mode: bool = True, simplified_mode: bool = False):
        """
        Initialize Wenjian compressor.
        
        Args:
            traditional_mode: Output Traditional Chinese (default)
            simplified_mode: Output Simplified Chinese (overrides traditional_mode)
        """
        self.traditional_mode = not simplified_mode
        self.simplified_mode = simplified_mode

    def _is_english_text(self, text: str) -> bool:
        """Detect if text is primarily English."""
        en_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        total = sum(1 for c in text if c.isalpha())
        return (en_chars / max(total, 1)) > 0.5

    def _apply_replacements(self, text: str) -> str:
        """Apply all compound pattern replacements."""
        result = text
        for pattern, replacement in self.REPLACEMENTS:
            result = re.sub(pattern, replacement, result)
        return result

    def _remove_particles(self, text: str) -> str:
        """Remove function particles."""
        result = text
        for particle in self.REMOVABLE_PARTICLES:
            result = result.replace(particle, "")
        return result

    def compress(self, text: str, memory_type: MemoryType = MemoryType.YI) -> str:
        """
        Compress Chinese text using Wenjian dialect.
        
        Args:
            text: Input text (Simplified or Traditional Chinese)
            memory_type: Memory type header (default: YI/議 for decisions)
            
        Returns:
            Compressed Wenjian text
        """
        result = text

        # Apply compound replacements first
        result = self._apply_replacements(result)

        # Remove function particles
        result = self._remove_particles(result)

        # Clean up extra spaces
        result = re.sub(r"\s+", " ", result).strip()

        # Build Wenjian format: [Type][Time] Content[Status][Importance]
        parts = [memory_type.value, " ", result]
        return "".join(parts)

    def compress_entry(self, entry: WenjianEntry) -> str:
        """Compress a WenjianEntry into Wenjian format string."""
        return entry.to_wenjian()

    def format_output(self, text: str) -> str:
        """
        Convert output to the configured script.
        
        Args:
            text: Text to format
            
        Returns:
            Text in Traditional or Simplified Chinese
        """
        from .s2t_converter import full_convert
        if self.traditional_mode:
            return full_convert(text, to_traditional=True)
        return full_convert(text, to_traditional=False)