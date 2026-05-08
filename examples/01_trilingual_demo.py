#!/usr/bin/env python3
"""
Trilingual Memory Palace Demo — 三语记忆宫殿示例

Demonstrates the core trilingual features:
- Chinese (Simplified/Traditional) ↔ English compression
- Palace create/search/wake-up workflow
- Cross-lingual memory filing
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mempalace_tri.compressor import Compressor, detect_language
from mempalace_tri.palace import Palace, Importance, MemoryType


# ── Step 1: Compression across 3 languages ─────────────────────────────

def demo_compression():
    """Test Wenjian (Chinese) and AAAK (English) compression."""
    compressor = Compressor()

    print("=" * 60)
    print("  Trilingual Compression Demo / 三语压缩示例")
    print("=" * 60)

    # Chinese Simplified
    zh_cn_text = "我们的团队决定了要从Auth0迁移到Clerk这个认证服务，主要的原因是因为Clerk的价格更加便宜，而且开发者体验更好"
    compressed_cn = compressor.compress(zh_cn_text, mode="zh_cn")
    lang_cn = detect_language(zh_cn_text)
    print(f"\n[简体中文]\n  原文: {zh_cn_text}\n  压缩: {compressed_cn}\n  语言: {lang_cn}")

    # Chinese Traditional
    zh_tw_text = "我們的團隊決定了要從Auth0遷移到Clerk這個認證服務，主要原因是Clerk的價格更便宜，開發者體驗更好"
    compressed_tw = compressor.compress(zh_tw_text, mode="zh_tw")
    lang_tw = detect_language(zh_tw_text)
    print(f"\n[繁體中文]\n  原文: {zh_tw_text}\n  壓縮: {compressed_tw}\n  語言: {lang_tw}")

    # English
    en_text = ("The team decided to migrate authentication from Auth0 to Clerk. "
               "Kai (backend lead) recommended this based on pricing: "
               "Auth0 is $240/mo, Clerk is $25/mo. Developer experience is also better.")
    compressed_en = compressor.compress(en_text, mode="en")
    lang_en = detect_language(en_text)
    print(f"\n[English]\n  Original: {en_text}\n  Compressed: {compressed_en}\n  Language: {lang_en}")

    # Cross-language conversion
    print("\n" + "=" * 60)
    print("  Simplified ↔ Traditional Conversion / 繁简转换")
    print("=" * 60)
    converted = compressor.convert_script(zh_cn_text, to_traditional=True)
    print(f"  简: {zh_cn_text}")
    print(f"  繁: {converted}")


# ── Step 2: Palace workflow ────────────────────────────────────────────

def demo_palace_workflow():
    """Create palace, add memories, search, wake-up."""
    import tempfile
    palace_path = tempfile.mkdtemp(prefix="tri_demo_")

    print("\n" + "=" * 60)
    print("  Palace Workflow / 宫殿工作流程")
    print("=" * 60)

    palace = Palace(palace_path)

    # Create wings
    wing_ai = palace.add_wing("AI", label="AI Projects / AI项目 / 人工智能项目")
    wing_per = palace.add_wing("Personal", label="Personal / 個人 / 个人")

    print(f"\nWings created / 殿已创建: {wing_ai.name}, {wing_per.name}")

    # Add room
    palace.add_room(wing="AI", room="LLM", label="Large Language Models / 大型語言模型")
    palace.add_room(wing="AI", room="RAG", label="Retrieval Augmented Generation / 檢索增強生成")
    palace.add_room(wing="Personal", room="Health", label="Health / 健康")

    # Add memories in different languages
    print("\nAdding memories / 添加記憶...")

    # Memory 1: Chinese
    drawer1, closet1 = palace.add_memory(
        wing="AI", room="LLM",
        content="我們團隊決定使用GPT-5作為主要模型，因為它在中文理解方面表現更好",
        source="demo", lang="zh_cn",
        memory_type=MemoryType.YI, importance=Importance.HIGH
    )
    print(f"  [中文] Drawer: {drawer1.id[:16]}...")
    print(f"  [中文] Closet: {closet1.compressed_text[:60]}...")

    # Memory 2: English
    drawer2, closet2 = palace.add_memory(
        wing="AI", room="LLM",
        content="We evaluated GPT-5 vs Claude 3 vs Gemini 2. GPT-5 won on Chinese comprehension benchmarks.",
        source="demo", lang="en",
        memory_type=MemoryType.DE, importance=Importance.HIGH
    )
    print(f"  [English] Drawer: {drawer2.id[:16]}...")
    print(f"  [English] Closet: {closet2.compressed_text[:60]}...")

    # Memory 3: Traditional Chinese
    drawer3, closet3 = palace.add_memory(
        wing="AI", room="RAG",
        content="我們決定採用向量資料庫進行檢索增強生成，以解決知識時效性問題",
        source="demo", lang="zh_tw",
        memory_type=MemoryType.CE, importance=Importance.KEY
    )
    print(f"  [繁中]  Drawer: {drawer3.id[:16]}...")
    print(f"  [繁中] Closet: {closet3.compressed_text[:60]}...")

    # Memory 4: Cross-wing
    drawer4, closet4 = palace.add_memory(
        wing="Personal", room="Health",
        content="Daily exercise: 30min jogging + 20min stretching. Consistent for 90 days.",
        source="demo", lang="en",
        memory_type=MemoryType.HAO, importance=Importance.MED
    )
    print(f"  [Health] Drawer: {drawer4.id[:16]}...")

    # Search
    print("\n" + "=" * 60)
    print("  Search / 搜索")
    print("=" * 60)

    results = palace.search("GPT", wing="AI", top_k=5)
    print(f"\nSearch 'GPT' in wing 'AI': {len(results)} results")
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r['text'][:80]}...")

    # Wake-up
    print("\n" + "=" * 60)
    print("  Wake-up Context / 醒上上下文")
    print("=" * 60)

    wake_up = palace.wake_up(wing="AI", include_spec=True)
    print(f"\n{wake_up[:500]}...")

    # Stats
    print("\n" + "=" * 60)
    print("  Palace Stats / 宫殿统计")
    print("=" * 60)
    stats = palace.stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print(f"\nPalace saved to: {palace_path}")
    print("(Demo palace is in temp dir and can be deleted)")


# ── Main ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("MemPalace Trilingual Demo / 三语记忆宫殿示例")
    print("=" * 60)

    demo_compression()
    demo_palace_workflow()

    print("\n" + "=" * 60)
    print("  Demo complete! / 示例完成!")
    print("=" * 60)