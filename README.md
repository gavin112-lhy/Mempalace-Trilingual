# MemPalace Trilingual — 三語記憶宮殿 / Trilingual Memory Palace

> **The world's first trilingual AI memory palace: English (AAAK) + Chinese Simplified (文簡) + Chinese Traditional (文簡).**

Store everything. Find anything. Three languages, one palace.

## Features

| Feature | English | 簡體中文 | 繁體中文 |
|---------|---------|----------|----------|
| Compression | AAAK | 文簡 (簡) | 文簡 (繁) |
| Palace Structure | Wing/Room/Drawer | 殿/軒/犢 | 殿/軒/犢 |
| Knowledge Graph | ✅ | ✅ | ✅ |
| MCP Server | ✅ | ✅ | ✅ |
| CLI | ✅ | ✅ | ✅ |
| Auto Lang Detect | ✅ | ✅ | ✅ |
| S2T Convert | N/A | ✅ | ✅ |
| 4-Layer Stack | ✅ | ✅ | ✅ |
| Graph Navigation | ✅ | ✅ | ✅ |

## Quick Start

```bash
# Install
pip install -e .

# Create a palace
python -c "from mempalace_tri import Palace; p = Palace('.mempalace')"

# Compress text (auto-detects language)
python -c "
from mempalace_tri import Compressor
c = Compressor()
# Chinese Traditional
print(c.compress('我們決定遷移認證服務'))
# English
print(c.compress('The team decided to use PostgreSQL', mode='aaak'))
"

# Search
python -c "from mempalace_tri import search_memories; search_memories('認證')"

# Knowledge graph
python -c "
from mempalace_tri import KnowledgeGraph
kg = KnowledgeGraph()
kg.add_triple('Team', 'uses', 'PostgreSQL')
"

# Palace graph
python -c "from mempalace_tri import build_graph; build_graph('.mempalace')"
```

## Architecture

```
memPalace-trilingual/
├── mempalace_tri/
│   ├── __init__.py          ← Package exports
│   ├── palace.py            ← Palace, Wing, Room, Drawer, Closet, Hall, Tunnel
│   ├── config.py            ← Configuration loading
│   ├── knowledge_graph.py   ← Temporal entity-relationship triples
│   ├── searcher.py          ← Semantic search via ChromaDB
│   ├── layers.py            ← 4-layer memory stack (L0-L3)
│   ├── palace_graph.py      ← Graph traversal (build, traverse, find_tunnels)
│   ├── mcp_server.py        ← MCP server (bilingual tools + extraction)
│   ├── cli.py               ← Unified CLI (bilingual commands)
│   ├── version.py           ← Package version
│   ├── spellcheck.py        ← Chinese spell-check correction
│   ├── onboarding.py        ← Interactive onboarding wizard
│   ├── hooks_cli.py         ← AI IDE hook management
│   ├── split_mega_files.py  ← Mega transcript splitter
│   ├── extraction/          ← Entity extraction pipeline
│   │   ├── __init__.py
│   │   ├── entity_registry.py
│   │   ├── entity_detector.py
│   │   ├── normalize.py
│   │   └── general_extractor.py
│   └── compressor/
│       ├── __init__.py      ← Compressor factory + CompressorMode
│       ├── base.py          ← Base compression interface
│       ├── aaak.py          ← AAAK English dialect
│       ├── wenjian.py       ← 文簡 Chinese dialect (簡 + 繁)
│       ├── s2t_converter.py ← Simplified↔Traditional converter
│       └── lang_detect.py   ← Auto-detect language (EN/ZH-T/ZH-S)
│   └── instructions/        ← AI instruction sets
│       ├── init.md          ← Setup instructions
│       ├── mine.md          ← Mining instructions
│       ├── search.md        ← Search instructions
│       └── status.md        ← Status instructions
├── pyproject.toml           ← Package config
└── README.md                ← This file
```

## Entity Extraction Pipeline

Mine directories for named entities (people, locations, projects, organizations, concepts) with auto-detection and canonicalization.

```python
from mempalace_tri import GeneralExtractor, EntityRegistry

# Register a known entity
reg = EntityRegistry.load()
reg.add_entity("Maya Wang", "person", aliases=["Maya"], context="Project lead")

# Detect entities from text
extractor = GeneralExtractor()
results = extractor.extract_from_text("Maya decided to use PostgreSQL for the auth service")
# → {"people": ["Maya Wang"], "projects": ["auth service"], "entities": [...]}

# Scan entire directory
results = extractor.extract_from_directory("./my-project")
# → {people: 5, locations: 2, projects: 3, entities: 15, languages: {"en": 10, "zh": 5}}

# Normalize entity names
from mempalace_tri import NormalizeService
ns = NormalizeService()
result = ns.normalize("maya wang", entity_type="person")
# → canonical: "Maya Wang", aliases_used: {"Maya", "maya wang"}
```

## Spell-Check

Auto-correct common Chinese typos.

```python
from mempalace_tri import spellcheck_user_text

corrected = spellcheck_user_text("我們決遷認證服務")
# → "我們決定遷移認證服務"
```

## Mega Transcript Splitter

Split large conversation files into per-session files.

```python
from mempalace_tri import split_file

written = split_file("mega_transcript.txt", "output_dir/")
# → ["session_2026-04-20_10-00.txt", "session_2026-04-20_14-00.txt"]
```

## Compression Modes

### English (AAAK)
```python
from mempalace_tri import Compressor
c = Compressor(mode=CompressorMode.AAAK)

c.compress("The team decided to use PostgreSQL because of pricing and developer experience.")
# → team dec use PostgreSQL by price + devex
```

### Chinese Simplified (文簡-簡)
```python
from mempalace_tri import Compressor
c = Compressor(mode=CompressorMode.WENJIAN_SIMPLIFIED)

c.compress("我们团队决定使用PostgreSQL作为主数据库，因为价格更便宜")
# → 議隊用PostgreSQL主資料庫以價故
```

### Chinese Traditional (文簡-繁)
```python
from mempalace_tri import Compressor
c = Compressor(mode=CompressorMode.WENJIAN_TRADITIONAL)

c.compress("我們團隊決定使用PostgreSQL作為主資料庫，因為價格更便宜")
# → 議隊用PostgreSQL主資料庫以價故
```

## S2T Converter

```python
from mempalace_tri import convert_s2t

# Simplified → Traditional
print(convert_s2t("我們決定使用PostgreSQL"))  # 我們決定使用PostgreSQL

# Traditional → Simplified
print(convert_s2t("我们决定使用PostgreSQL"))  # 我们决定使用PostgreSQL

# Bidirectional
print(convert_s2t("我們決定", direction="s2t"))  # 我們決定
print(convert_s2t("我们決定", direction="t2s"))  # 我们決定
```

## Knowledge Graph

```python
from mempalace_tri import KnowledgeGraph

kg = KnowledgeGraph()

# Add temporal facts
kg.add_triple("Team", "uses", "PostgreSQL", valid_from="2026-04-20")
kg.add_triple("Maya", "assigned_to", "auth-migration", valid_from="2026-04-20")

# Query current state
kg.query_entity("Team")
# → [Team → uses → PostgreSQL (current)]

# Query historical state
kg.query_entity("Maya", as_of="2026-03-01")
# → [Maya → assigned_to → auth-migration (active)]

# Timeline
kg.timeline("auth-migration")
# → chronological story of auth migration
```

## Memory Stack

```python
from mempalace_tri import MemoryStack

stack = MemoryStack()

# Wake up (~600-900 tokens, all languages)
context = stack.wake_up()
# → L0 (Identity: "I am MemPalace assistant") +
#    L1 (Critical facts: team, projects, prefs in compressed form)

# On-demand recall
context = stack.recall(wing="AI")
# → L2: recent session memories for the AI wing

# Deep search
results = stack.search("PostgreSQL decision")
# → L3: semantic search across all memories
```

## Palace Graph Navigation

```python
from mempalace_tri import build_graph, traverse, find_tunnels, graph_stats

# Build graph from palace
nodes, edges = build_graph(".mempalace")

# Traverse from a room
results = traverse("auth-migration", ".mempalace")

# Find cross-wing connections
tunnels = find_tunnels("wing_team", "wing_project", ".mempalace")

# Get graph statistics
stats = graph_stats(".mempalace")
# → {total_rooms, tunnel_rooms, total_edges, rooms_per_wing, top_tunnels}
```

## Language Detection

```python
from mempalace_tri.compressor import LangType, detect_language

# Auto-detect
lang = detect_language("我們決定遷移認證服務")
print(lang)  # LangType.TRADITIONAL_CHINESE

lang = detect_language("我们决定迁移认证服务")
print(lang)  # LangType.SIMPLIFIED_CHINESE

lang = detect_language("We decided to migrate")
print(lang)  # LangType.ENGLISH
```

## CLI Commands

### Core Commands — 核心命令
```bash
# All commands are bilingual
python -m mempalace_tri status        # 狀態查詢 / Status
python -m mempalace_tri search "認證"  # 搜索記憶 / Search
python -m mempalace_tri add-drawer ... # 添加抽屜 / Add drawer
python -m mempalace_tri compress ...   # 壓縮 / Compress
python -m mempalace_tri kg-query ...   # 知識圖查詢 / KG query
python -m mempalace_tri list-wings ... # 列出殿堂 / List wings
python -m mempalace_tri mine ~/project --compression-mode auto  # 導入並壓縮 / Mine + compress
```

### Language Tools — 語言工具
```bash
# Language detection — 語言檢測
python -m mempalace_tri detect-lang "我們決定遷移"
# → Detected language: Chinese (Traditional) (zh_tw)

# 簡繁轉換 / Simplified ↔ Traditional conversion
python -m mempalace_tri convert-s2t "我們決定" --direction s2t
# → 我們決定 (traditional → traditional, no change)

python -m mempalace_tri convert-s2t "我们决定" --direction t2s
# → 我們決定

# Compression-aware mining — 壓縮導入
python -m mempalace_tri mine ~/project --compression-mode auto
python -m mempalace_tri mine ~/project --compression-mode aaak
python -m mempalace_tri mine ~/project --compression-mode wenjian_simplified
python -m mempalace_tri mine ~/project --compression-mode wenjian_traditional
```

## MCP Server

```bash
# Start bilingual MCP server
python -m mempalace_tri.mcp_server

# Available tools (bilingual labels):
# - mempalace_search (搜索)
# - mempalace_add_drawer (添加抽屜)
# - mempalace_delete_drawer (刪除抽屜)
# - mempalace_kg_query (知識圖查詢)
# - mempalace_kg_add (添加知識)
# - mempalace_kg_invalidate (撤銷知識)
# - mempalace_kg_timeline (時間線)
# - mempalace_kg_stats (知識圖統計)
# - mempalace_traverse (遍歷)
# - mempalace_find_tunnels (查找連接)
# - mempalace_diary_write (日記寫入)
# - mempalace_diary_read (日記讀取)
# - mempalace_check_duplicate (檢查重複)
# - mempalace_compress (壓縮)
# - mempalace_status (狀態)
# - mempalace_list_wings (列出殿堂)
# - mempalace_list_rooms (列出房間)
# - mempalace_get_taxonomy (獲取分類)
# - mempalace_get_aaak_spec (獲取方言規範)
#
# === Trilingual Tools — 三語工具 ===
# - mempalace_detect_lang (語言檢測)
# - mempalace_convert_s2t (簡繁轉換)
# - mempalace_compression_test (壓縮測試)
```

## Design Principles

1. **Language-neutral core**: Palace functions work identically across all 3 languages
2. **Compressors are the differentiator**: AAAK for English, 文簡 for Chinese
3. **Auto-detect, never force**: Detect input language, apply appropriate compression
4. **S2T toggle for Chinese**: Convert between 繁簡 at any time
5. **No language barriers**: MCP tools and CLI have bilingual labels
6. **Same architecture, different dialects**: All 3 languages share Palace, KG, Stack, Graph

## Comparison

| Feature | MemPalace 3.1.0 | ChinesePalace | TraChinesePalace | **Trilingual** |
|---------|-----------------|---------------|------------------|---|-----------|
| English AAAK | ✅ | ❌ | ❌ | ✅ |
| Chinese 文簡 | ❌ | ✅ (簡) | ✅ (繁) | ✅ |
| S2T Converter | ❌ | ❌ | ✅ | ✅ |
| Lang Detection | ❌ | ✅ | ✅ | ✅ |
| MCP (bilingual) | ✅ | ✅ | ✅ | ✅ |
| Unified CLI | ✅ | ✅ | ✅ | ✅ |
| Knowledge Graph | ✅ | ✅ | ✅ | ✅ |
| Memory Stack | ✅ | ✅ | ✅ | ✅ |
| Graph Navigation | ✅ | ✅ | ✅ | ✅ |
| Compression Modes | 1 (AAAK) | 1 (文簡) | 1 (文簡) | **3 (AAAK+文簡簡+文簡繁)** |

## License

MIT