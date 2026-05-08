# MemPalace Trilingual Examples — 三語記憶宮殿示例

Examples demonstrating the features of **MemPalace Trilingual** (三語記憶宮殿).

## Examples

| File | Description / 描述 |
|------|------------------|
| `01_trilingual_demo.py` | Core trilingual demo: compression (Wenjian/AAAK), palace workflow, search, wake-up |
| `02_mine_import.py` | Project mining & conversation import demos |
| `04_compress_compare.py` | Compression comparison across Simplified Chinese, Traditional Chinese, and English |
| `05_ollama_integration.py` | Ollama integration: Wenjian compression, entity extraction, cross-lingual translation, wake-up generation |

## Running Examples

```bash
# From mempalace-trilingual root
cd mempalace-trilingual

# Install dependencies
pip install -e .

# Run each example
python examples/01_trilingual_demo.py
python examples/02_mine_import.py
python examples/04_compress_compare.py
python examples/05_ollama_integration.py
```

## What Each Example Demonstrates

### 01_trilingual_demo.py — 核心功能示例
- **Wenjian compression** (文簡壓縮) for Chinese (Simplified & Traditional)
- **AAAK compression** for English
- **Language detection** across 3+ languages
- **Simplified ↔ Traditional conversion**
- **Palace workflow**: create wings → add rooms → add memories → search → wake-up

### 02_mine_import.py — 挖掘與導入示例
- **Project mining**: scan source code for decisions, patterns, problems
- **Conversation mining**: import chat exports (Claude, ChatGPT, Slack exports)
- **Skip logic**: automatically skip already-mined files

### 04_compress_compare.py — 壓縮對比示例
- Compare Wenjian vs AAAK compression ratios
- Language detection for Chinese, English, Japanese, Korean
- Visual summary of compression effectiveness

### 05_ollama_integration.py — Ollama集成示例
- **Wenjian compression via Ollama**: use local LLM for Chinese compression
- **Entity extraction**: extract structured data (people, decisions, status) from text
- **Cross-lingual translation**: translate between Simplified/Traditional Chinese and English
- **Wake-up context**: generate personalized daily wake-up using Ollama

## Requirements
To run the Ollama example, you need:
1. **Ollama installed**: https://ollama.ai
2. **A model downloaded**: `ollama pull llama3.2`
3. **Ollama running**: `ollama serve` (default: http://localhost:11434)

All other examples run without external dependencies beyond the mempalace-trilingual package.

## Architecture Reference

```
mempalace-trilingual/
├── mempalace_tri/          # Main package
│   ├── palace.py           # Palace data structure
│   ├── compressor/         # Compression modules
│   │   ├── wenjian.py      # Chinese compression
│   │   ├── aaak.py         # English AAAK compression
│   │   └── lang_detect.py  # Language detection
│   ├── miner.py            # Project miner
│   ├── convo_miner.py      # Conversation miner
│   ├── cli.py              # CLI interface
│   └── ...
└── examples/               # This directory
    ├── README.md
    ├── 01_trilingual_demo.py
    ├── 02_mine_import.py
    └── 04_compress_compare.py