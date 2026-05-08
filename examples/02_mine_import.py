#!/usr/bin/env python3
"""
Mine & Import Demo — 挖掘导入示例

Demonstrates:
- mine() — project directory mining
- mine_convos() — conversation import
- file_already_mined() — skip already-mined files
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from mempalace_tri.miner import mine, status, scan_project, process_file
from mempalace_tri.convo_miner import mine_convos, scan_convos, chunk_exchanges
from mempalace_tri.palace import get_collection, file_already_mined


# ── Example 1: Project mining ───────────────────────────────────────

def demo_project_mining():
    """Mine a project directory for code patterns and decisions."""
    print("=" * 60)
    print("  Example 1: Project Mining / 项目挖掘")
    print("=" * 60)

    # Create a temp project with some files
    project_dir = tempfile.mkdtemp(prefix="demo_project_")
    palace_path = tempfile.mkdtemp(prefix="demo_palace_")

    # Create sample files
    (Path(project_dir) / "README.md").write_text(
        "# My Project\n\nWe decided to use FastAPI for the backend.\n"
        "The team chose PostgreSQL as the database.\n\n## Architecture\n"
        "Modular design with separate services for auth, users, and payments."
    )
    (Path(project_dir) / "main.py").write_text(
        'from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/")\n'
        "def home():\n    return {'status': 'ok'}\n\n# Migration: SQLAlchemy 1.x → 2.x\n"
    )
    (Path(project_dir) / "config.py").write_text(
        "# Config for production\nDATABASE_URL = 'postgresql://localhost/mydb'\n"
        "# TODO: migrate to Clerk for auth\n"
    )

    print(f"\nProject dir: {project_dir}")
    print(f"Palace path: {palace_path}")

    # Dry run first
    print("\n--- Dry Run ---")
    mine(project_dir=project_dir, palace_path=palace_path, wing="demo_project", dry_run=True)

    # Actual mining
    print("\n--- Actual Mine ---")
    mine(project_dir=project_dir, palace_path=palace_path, wing="demo_project", dry_run=False)

    # Status
    print("\n--- Palace Status ---")
    do_status(status, palace_path)


# ── Example 2: Conversation mining ───────────────────────────────────

def demo_conversation_mining():
    """Mine conversation exports into the palace."""
    print("\n" + "=" * 60)
    print("  Example 2: Conversation Mining / 对话挖掘")
    print("=" * 60)

    # Create a temp convo directory
    convo_dir = tempfile.mkdtemp(prefix="demo_convos_")
    palace_path = tempfile.mkdtemp(prefix="demo_palace2_")

    # Create sample conversation file
    (Path(convo_dir) / "claude_export.txt").write_text(
        "> How should I handle authentication?\n"
        "I recommend using Clerk. It's cheaper than Auth0 and has better DX.\n\n"
        "> What about database choice?\n"
        "PostgreSQL is the safest choice. It handles concurrent writes well.\n\n"
        "> Should I use Docker?\n"
        "Yes for staging, no for dev. Docker Compose works great for local."
    )

    print(f"\nConvo dir: {convo_dir}")
    print(f"Palace path: {palace_path}")

    # Scan
    files = scan_convos(convo_dir)
    print(f"\nFound {len(files)} conversation files")

    # Chunk demo
    content = files[0].read_text() if files else ""
    chunks = chunk_exchanges(content) if content else []
    print(f"Generated {len(chunks)} exchange chunks")

    # Mine
    print("\n--- Mine Conversations ---")
    mine_convos(
        convo_dir=convo_dir,
        palace_path=palace_path,
        wing="convos_demo",
        dry_run=False,
    )


# ── Example 3: Already-mined check ──────────────────────────────────

def demo_skip_check():
    """Demonstrate file_already_mined skip logic."""
    print("\n" + "=" * 60)
    print("  Example 3: Skip Already-Mined Files / 跳过已挖掘")
    print("=" * 60)

    palace_path = tempfile.mkdtemp(prefix="demo_palace3_")

    # Create palace and collection
    collection = get_collection(palace_path)

    # Add a dummy entry
    collection.add(
        documents=["dummy"],
        ids=["dummy_id"],
        metadatas=[{"source_file": "/test/file.py", "wing": "test", "room": "general"}],
    )

    # Check
    source = "/test/file.py"
    exists = file_already_mined(collection, source)
    new_file = "/test/new_file.py"
    new_exists = file_already_mined(collection, new_file)

    print(f"  File {source} mined: {exists}")
    print(f"  File {new_file} mined: {new_exists}")


# ── Main ──

if __name__ == "__main__":
    print("MemPalace Mine & Import Demo / 挖掘导入示例")
    print("=" * 60)

    try:
        demo_project_mining()
    except Exception as e:
        print(f"  [Note] Project mining skipped: {e}")

    try:
        demo_conversation_mining()
    except Exception as e:
        print(f"  [Note] Conversation mining skipped: {e}")

    demo_skip_check()

    print("\n" + "=" * 60)
    print("  Demo complete! / 示例完成!")
    print("=" * 60)