#!/usr/bin/env python3
"""
Compression Comparison Demo — 压缩对比示例

Compare Wenjian (文简) vs AAAK compression across all 3 languages.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mempalace_tri.compressor import Compressor, detect_language


def demo_compress_compare():
    """Compare compression across Simplified Chinese, Traditional Chinese, and English."""
    compressor = Compressor()

    print("=" * 60)
    print("  Compression Comparison / 压缩对比")
    print("=" * 60)

    # Test texts (same content in 3 languages)
    tests = [
        {
            "name": "简体中文 / Simplified Chinese",
            "text": "我们团队决定从Auth0迁移到Clerk认证服务，因为Clerk更便宜且开发者体验更好。",
            "mode": "zh_cn",
        },
        {
            "name": "繁體中文 / Traditional Chinese",
            "text": "我們團隊決定從Auth0遷移到Clerk認證服務，因為Clerk更便宜且開發者體驗更好。",
            "mode": "zh_tw",
        },
        {
            "name": "English",
            "text": "Our team decided to migrate from Auth0 to Clerk auth service because Clerk is cheaper and has better developer experience.",
            "mode": "en",
        },
    ]

    results = []
    for test in tests:
        compressed = compressor.compress(test["text"], mode=test["mode"])
        lang = detect_language(test["text"])
        orig_len = len(test["text"])
        comp_len = len(compressed)
        ratio = orig_len / max(comp_len, 1)

        print(f"\n--- {test['name']} ---")
        print(f"  Original ({lang}): {orig_len} chars")
        print(f"  Compressed:        {comp_len} chars")
        print(f"  Ratio:             {ratio:.1f}x")
        print(f"  Compressed text:   {compressed}")
        results.append((test["name"], ratio))

    # Cross-language comparison
    print("\n" + "=" * 60)
    print("  Summary / 摘要")
    print("=" * 60)
    for name, ratio in results:
        bar = "█" * int(ratio) + "░" * (20 - int(ratio))
        print(f"  {name[:30]:30} |{bar}| {ratio:.1f}x")

    # Language detection
    print("\n" + "=" * 60)
    print("  Language Detection / 语言检测")
    print("=" * 60)
    sample_texts = [
        "你好世界",
        "你好，世界！",
        "Hello world",
        "こんにちは世界",
        "안녕하세요 세계",
        "Our team uses PostgreSQL",
        "我們的團隊使用PostgreSQL",
    ]
    for text in sample_texts:
        lang = detect_language(text)
        print(f"  {text:40} → {lang}")


# ── Main ──

if __name__ == "__main__":
    demo_compress_compare()
    print("\n" + "=" * 60)
    print("  Demo complete! / 示例完成!")
    print("=" * 60)