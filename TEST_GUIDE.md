# MemPalace Trilingual — Manual Test Guide — 手動測試指南

> This guide explains the difference between `examples/` and `tests/`, and provides step-by-step manual tests for the trilingual merge verification.

---

## Examples vs Tests: What's the Difference?

| | `examples/` | `tests/` |
|---|---|---|
| **Purpose** | Demonstrate features, show how to use the library | Verify correctness, catch regressions |
| **Who runs them** | Users, developers learning the API | CI/CD pipeline, developers before merging |
| **Format** | Standalone Python scripts you run manually | pytest test functions with assertions |
| **Output** | Human-readable console output | Pass/fail results |
| **Dependencies** | May need Ollama (for 05_ollama_integration.py) | Self-contained, use test fixtures |
| **Example** | `python examples/01_trilingual_demo.py` | `python -m pytest tests/test_dialect.py` |

**In short:**
- **Examples** = Tutorial-style scripts to understand features
- **Tests** = Automated checks that assert expected behavior

---

## Manual Test Steps

Run each step in your terminal one at a time. Verify the output matches expectations.

---

### Test 1: Installation — 安裝

```bash
cd mempalace-trilingual
pip install -e .
```

**Expected:** `Successfully installed mempalace-trilingual-3.3.5-tri.1` (or similar)

---

### Test 2: Package Import — 套件導入

```python
python -c "
from mempalace_tri import Palace, Compressor, KnowledgeGraph
from mempalace_tri.compressor import CompressorMode, detect_language, convert_text
print('All imports successful!')
print('CompressorMode values:', [m.name for m in CompressorMode])
"
```

**Expected output:**
```
All imports successful!
CompressorMode values: ['AUTO', 'AAAK', 'WENJIAN_SIMPLIFIED', 'WENJIAN_TRADITIONAL']
```

---

### Test 3: Language Detection — 語言檢測

```python
python -c "
from mempalace_tri.compressor import detect_language

# Test English
r1 = detect_language('The team decided to use PostgreSQL')
print(f'EN: {r1}')

# Test Simplified Chinese
r2 = detect_language('我们决定迁移认证服务')
print(f'ZH-S: {r2}')

# Test Traditional Chinese
r3 = detect_language('我們決定遷移認證服務')
print(f'ZH-T: {r3}')

# Test mixed
r4 = detect_language('The team decided 我們決定使用')
print(f'MIXED: {r4}')
"
```

**Expected output:**
```
EN: en
ZH-S: zh_cn
ZH-T: zh_tw
MIXED: mixed
```

---

### Test 4: S2T Conversion — 簡繁轉換

```python
python -c "
from mempalace_tri import convert_text

# Simplified → Traditional
s2t = convert_text('我们决定迁移', direction='s2t')
print(f'S→T: {s2t}')

# Traditional → Simplified
t2s = convert_text('我們決定遷移', direction='t2s')
print(f'T→S: {t2s}')

# Roundtrip check
back = convert_text(s2t, direction='t2s')
print(f'Roundtrip: {back}')
"
```

**Expected output:**
```
S→T: 我們決定遷移
T→S: 我们决定迁移
Roundtrip: 我们决定迁移
```

---

### Test 5: Compression — 壓縮

```python
python -c "
from mempalace_tri import Compressor, CompressorMode

c = Compressor()

# English (AAAK)
r1 = c.compress('The team decided to use PostgreSQL because of pricing and developer experience.')
print(f'EN compressed: {r1.compressed}')
print(f'EN language: {r1.detected_language}')
print(f'EN ratio: {r1.compression_ratio:.2f}')
print()

# Chinese Simplified (文簡-簡)
r2 = c.compress('我们团队决定使用PostgreSQL作为主数据库', mode=CompressorMode.WENJIAN_SIMPLIFIED)
print(f'ZH-S compressed: {r2.compressed}')
print(f'ZH-S language: {r2.detected_language}')
print(f'ZH-S ratio: {r2.compression_ratio:.2f}')
print()

# Chinese Traditional (文簡-繁)
r3 = c.compress('我們團隊決定使用PostgreSQL作為主資料庫', mode=CompressorMode.WENJIAN_TRADITIONAL)
print(f'ZH-T compressed: {r3.compressed}')
print(f'ZH-T language: {r3.detected_language}')
print(f'ZH-T ratio: {r3.compression_ratio:.2f}')
print()

# Auto mode (should detect language automatically)
r4 = c.compress('我們決定使用PostgreSQL')  # no mode specified
print(f'Auto compressed: {r4.compressed}')
print(f'Auto language: {r4.detected_language}')
"
```

**Expected:** All compressions produce shortened output with appropriate compression ratios.

---

### Test 6: Palace Workflow — 記憶宮殿工作流

```python
python -c "
import tempfile, os
from mempalace_tri import Palace, Wing

# Create a temp palace
tmpdir = tempfile.mkdtemp()
palace_path = os.path.join(tmpdir, '.mempalace')

p = Palace(palace_path)

# Add a wing
w = p.add_wing('Engineering')
print(f'Added wing: {w.name}')

# Add a room
r = w.add_room('auth-migration')
print(f'Added room: {r.name}')

# Add a drawer with Traditional Chinese
from mempalace_tri import Compressor, CompressorMode
c = Compressor(default_mode=CompressorMode.WENJIAN_TRADITIONAL)
compressed = c.compress('我們決定將認證服務從JWT遷移至OAuth2')
d = r.add_drawer(compressed.compressed, language='zh_tw')
print(f'Added drawer: {d.id[:20]}... lang={d.language}')

# Search
results = p.search('認證服務', wing='Engineering')
print(f'Search results: {len(results)} matches')

# Cleanup
import shutil
shutil.rmtree(tmpdir)
print('Palace test complete!')
"
```

**Expected:** Palace creates wings, rooms, drawers, and returns search matches.

---

### Test 7: Knowledge Graph — 知識圖

```python
python -c "
import tempfile
from mempalace_tri import KnowledgeGraph

tmpdir = tempfile.mkdtemp()
kg = KnowledgeGraph(tmpdir)

# Add facts
kg.add_triple('Team', 'uses', 'PostgreSQL', valid_from='2026-05-08')
kg.add_triple('Maya', 'assigned_to', 'auth-migration', valid_from='2026-05-08')

# Query
results = kg.query_entity('Team')
print(f'Team facts: {len(results)} entries')

# Timeline
timeline = kg.timeline('auth-migration')
print(f'Timeline entries: {len(timeline)}')

# Stats
stats = kg.stats()
print(f'KG stats: {stats}')

import shutil
shutil.rmtree(tmpdir)
print('KG test complete!')
"
```

**Expected:** Facts added, queried, timeline returned, stats printed.

---

### Test 8: CLI Commands — CLI命令

```bash
# Language detection
python -m mempalace_tri detect-lang "我們決定遷移"
# Expected: Detected language: Chinese (Traditional) (zh_tw)

# S2T conversion
python -m mempalace_tri convert-s2t "我们决定" --direction s2t
# Expected: 我們決定

# Palace status (cold start, no palace yet)
python -m mempalace_tri status 2>/dev/null || echo "No palace found (expected)"

# List wings (cold start)
python -m mempalace_tri list-wings 2>/dev/null || echo "No palace found (expected)"
```

---

### Test 9: Trilingual Examples — 三語示例

```bash
# Run the core trilingual demo
python examples/01_trilingual_demo.py

# Run compression comparison
python examples/04_compress_compare.py
```

**Expected:** Both scripts run to completion without errors, showing compression comparisons across languages.

---

### Test 10: Dedup Extraction — 去重提取

```python
python -c "
from mempalace_tri.extraction import GeneralExtractor, EntityRegistry

# Test entity registry
reg = EntityRegistry.load()
reg.add_entity('Maya Wang', 'person', aliases=['Maya'], context='Project lead')
print(f'Entities in registry: {reg.entity_count}')

# Test entity detection
extractor = GeneralExtractor()
results = extractor.extract_from_text('Maya decided to use PostgreSQL for auth')
print(f'Detected entities: {results}')

# Test normalization
from mempalace_tri import NormalizeService
ns = NormalizeService()
result = ns.normalize('maya wang', entity_type='person')
print(f'Normalized: canonical={result.get(\"canonical\", \"N/A\")}')
"
```

---

### Test 11: Spell-Check — 拼寫檢查

```python
python -c "
from mempalace_tri import spellcheck_user_text

# Traditional Chinese typo
corrected = spellcheck_user_text('我們決遷認證服務')
print(f'Corrected: {corrected}')
# Expected: 我們決定遷移認證服務

# Simplified Chinese typo
corrected2 = spellcheck_user_text('我们决遷认证服务')
print(f'Corrected: {corrected2}')
# Expected: 我们决定迁移认证服务
"
```

---

### Test 12: Mega Transcript Splitter — 大文件分割器

```python
python -c "
from mempalace_tri import split_file
import tempfile, os

# Create a test mega file
tmpdir = tempfile.mkdtemp()
mega_path = os.path.join(tmpdir, 'mega.txt')
with open(mega_path, 'w') as f:
    f.write('=== Session 2026-05-08 10:00 ===\nHello World\n')
    f.write('=== Session 2026-05-08 14:00 ===\nSecond session\n')

output_dir = os.path.join(tmpdir, 'output')
os.makedirs(output_dir)

written = split_file(mega_path, output_dir)
print(f'Split into {len(written)} files: {written}')

import shutil
shutil.rmtree(tmpdir)
"
```

---

## Test Checklist — 測試清單

Copy this checklist and mark as you go:

- [ ] **Test 1**: Installation succeeds
- [ ] **Test 2**: All imports work
- [ ] **Test 3**: Language detection (EN, ZH-S, ZH-T, MIXED)
- [ ] **Test 4**: S2T conversion (s2t, t2s, roundtrip)
- [ ] **Test 5**: Compression (EN-AAAK, ZH-S-Wenjian, ZH-T-Wenjian, Auto)
- [ ] **Test 6**: Palace workflow (wing → room → drawer → search)
- [ ] **Test 7**: Knowledge graph (add, query, timeline)
- [ ] **Test 8**: CLI commands (detect-lang, convert-s2t, status)
- [ ] **Test 9**: Examples run without errors
- [ ] **Test 10**: Entity extraction works
- [ ] **Test 11**: Spell-check corrects typos
- [ ] **Test 12**: Mega file splitter works

---

## Troubleshooting — 故障排除

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'mempalace_tri'` | Run `pip install -e .` in mempalace-trilingual directory |
| `OSError` on Windows | Close any files that may be locked by another process |
| Compression produces empty output | Check input text is not too short (minimum ~5 characters) |
| S2T returns unchanged text | Ensure input contains Traditional Chinese characters |
| Palace search returns 0 results | Add drawers before searching; empty palace = no results |
| Examples hang at import | Check for conflicting `mempalace` package installed elsewhere |

---

## What Constitutes Success — 成功標準

All tests pass if:
1. ✅ No `ImportError` or `ModuleNotFoundError`
2. ✅ Language detection correctly identifies EN, ZH-S, ZH-T, and mixed text
3. ✅ S2T conversion is bidirectional and roundtrips correctly
4. ✅ Compression produces shorter output for all 3 modes
5. ✅ Palace workflow creates, stores, and retrieves memories
6. ✅ CLI commands execute without crashing
7. ✅ Examples run to completion