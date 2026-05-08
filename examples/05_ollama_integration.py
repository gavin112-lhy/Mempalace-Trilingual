#!/usr/bin/env python3
"""
Ollama Integration Demo — Ollama 集成示例

Demonstrates using Ollama (local LLM) for:
- Wenjian (文简) compression via Ollama API
- LLM-powered extraction (entities, decisions, problems)
- Cross-lingual translation via Ollama
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mempalace_tri.compressor import Compressor, detect_language


# ── Ollama helper ──────────────────────────────────────────────────

OLLAMA_BASE = "http://localhost:11434"


def ollama_available(model: str = "llama3.2") -> bool:
    """Check if Ollama is running and has the requested model."""
    try:
        import urllib.request
        req = urllib.request.Request(f"{OLLAMA_BASE}/api/tags")
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read())
            models = data.get("models", [])
            return any(model in m.get("name", "") for m in models)
    except Exception:
        return False


def ollama_generate(prompt: str, model: str = "llama3.2", system: str = "") -> str:
    """Send a prompt to Ollama and get the generated response."""
    import urllib.request

    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        f"{OLLAMA_BASE}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())
        return result.get("response", "").strip()


# ── Example 1: Wenjian compression via Ollama ──────────────────────

def demo_ollama_compress():
    """Use Ollama to compress text into Wenjian format."""
    print("=" * 60)
    print("  Example 1: Wenjian Compression via Ollama / Ollama压缩")
    print("=" * 60)

    if not ollama_available():
        print("  [SKIP] Ollama not running. Start it with: ollama serve")
        print("  Then download a model: ollama pull llama3.2")
        return

    model = "llama3.2"
    if not ollama_available(model):
        print(f"  [SKIP] Model '{model}' not found. Run: ollama pull {model}")
        return

    # Wenjian compression spec as system prompt
    system_prompt = """你是一个文简压缩助手。请将用户输入的文本压缩为文简格式。

文简规范：
- 使用简短的词语和缩写
- 保留关键信息：人物、时间、决策、原因、状态
- 使用标准符号：议(讨论中)、定(已决定)、执(执行中)、完(已完成)、风(风险)、失(错误决策)
- 用 → 表示变迁，/ 表示替代
- 用 ★★★★★★★ 表示重要性
- 输出纯文简文本，不要解释

示例：
输入：我们的团队决定了要从Auth0迁移到Clerk这个认证服务，主要的原因是因为Clerk的价格更加便宜，而且开发者体验更好
输出：议 迁身份：Auth0→Clerk。伟明工荐（价240→25/mo，工便）[定]。"""

    texts = [
        ("简体中文", "我们的团队决定从Auth0迁移到Clerk认证服务，因为Clerk更便宜且开发者体验更好。"),
        ("繁體中文", "我們的團隊決定從Auth0遷移到Clerk認證服務，原因是Clerk的價格更優惠且開發者體驗更佳。"),
        ("English", "Our team decided to migrate from Auth0 to Clerk auth service because Clerk is cheaper and has better developer experience."),
    ]

    for lang_name, text in texts:
        lang = detect_language(text)
        prompt = f"请压缩以下文本为文简格式：\n\n{text}"
        compressed = ollama_generate(prompt, model=model, system=system_prompt)

        # Also do local compression for comparison
        local = Compressor()
        local_compressed = local.compress(text, mode="zh_cn" if "中文" in lang_name else "en")

        print(f"\n--- {lang_name} ({lang}) ---")
        print(f"  Input:   {text[:80]}")
        print(f"  Ollama:  {compressed[:80]}")
        print(f"  Local:   {local_compressed[:80]}")


# ── Example 2: Entity extraction via Ollama ────────────────────────

def demo_ollama_extract():
    """Use Ollama to extract structured data from text."""
    print("\n" + "=" * 60)
    print("  Example 2: Entity Extraction via Ollama / Ollama实体提取")
    print("=" * 60)

    if not ollama_available():
        print("  [SKIP] Ollama not running. Start it with: ollama serve")
        return

    system_prompt = """你是一个实体提取助手。请从文本中提取以下信息，以JSON格式返回：
{
  "entity": "人名或组织名",
  "role": "角色/职位",
  "decision": "关键决策",
  "reason": "决策原因",
  "status": "当前状态(议/定/执/完)"
}
如果无法提取某些字段，用 null 表示。只输出JSON，不要解释。"""

    texts = [
        ("伟明工荐迁Clerk", "伟明是后端工程师，他推荐从Auth0迁移到Clerk，因为价格更便宜。"),
        ("Maya完成迁移", "美云运完成auth迁移，历时12日，状态为已完成。"),
    ]

    for label, text in texts:
        prompt = f"从以下文本提取实体信息：\n\n{text}"
        result = ollama_generate(prompt, model="llama3.2", system=system_prompt)

        print(f"\n--- {label} ---")
        print(f"  Input:  {text}")
        print(f"  Output: {result[:200]}")


# ── Example 3: Cross-lingual translation via Ollama ─────────────────

def demo_ollama_translate():
    """Use Ollama for cross-lingual translation."""
    print("\n" + "=" * 60)
    print("  Example 3: Cross-Lingual Translation / 跨语言翻译")
    print("=" * 60)

    if not ollama_available():
        print("  [SKIP] Ollama not running. Start it with: ollama serve")
        return

    system_prompt = "你是一个翻译助手。请准确翻译以下文本，保持专业术语不变。只输出翻译结果，不要解释。"

    translations = [
        ("中文→英文", "我们的团队决定使用GPT-5作为主要模型。", "zh→en"),
        ("英文→中文", "The team decided to use PostgreSQL for the database.", "en→zh"),
        ("简→繁", "我们团队决定从Auth0迁移到Clerk。", "zh_cn→zh_tw"),
        ("繁→简", "我們團隊決定從Auth0遷移到Clerk。", "zh_tw→zh_cn"),
    ]

    for label, text, direction in translations:
        prompt = f"请翻译以下文本 ({direction})：\n\n{text}"
        result = ollama_generate(prompt, model="llama3.2", system=system_prompt)

        print(f"\n--- {label} ({direction}) ---")
        print(f"  Input:  {text}")
        print(f"  Output: {result[:100]}")


# ── Example 4: Palace wake-up generation via Ollama ─────────────────

def demo_ollama_wake_up():
    """Use Ollama to generate a personalized wake-up context."""
    print("\n" + "=" * 60)
    print("  Example 4: Wake-up Context via Ollama / Ollama唤醒上下文")
    print("=" * 60)

    if not ollama_available():
        print("  [SKIP] Ollama not running. Start it with: ollama serve")
        return

    # Simulated palace memories
    memories = [
        "伟明工荐迁Clerk（价240→25/mo）[定]",
        "美云运完成auth迁移，历时12日[完]",
        "团队决定用GPT-5作为主要模型[定]",
        "PostgreSQL作为数据库，处理并发写[定]",
        "下轮荐迁CI至GitHub Actions[议]",
    ]

    system_prompt = """你是一个AI助手，帮助用户回忆昨天的工作内容。
根据提供的记忆片段，生成一段简短的、个性化的唤醒上下文。
用中文和英文双语输出，语气友好、鼓励。
不要编造不存在的信息，只基于给定的记忆片段。"""

    memories_text = "\n".join(f"- {m}" for m in memories)
    prompt = f"根据以下记忆，生成今天的唤醒上下文：\n\n{memories_text}"

    result = ollama_generate(prompt, model="llama3.2", system=system_prompt)

    print(f"\n  Memories / 记忆:")
    for m in memories:
        print(f"    - {m}")
    print(f"\n  Wake-up / 唤醒:")
    print(f"    {result[:300]}")


# ── Main ────────────────────────────────────────────────────────────

def main():
    print("MemPalace × Ollama Integration Demo / Ollama集成示例")
    print("=" * 60)
    print(f"  Ollama base: {OLLAMA_BASE}")
    print(f"  Available:   {ollama_available('llama3.2')}")
    print()

    demo_ollama_compress()
    demo_ollama_extract()
    demo_ollama_translate()
    demo_ollama_wake_up()

    print("\n" + "=" * 60)
    print("  Demo complete! / 示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()