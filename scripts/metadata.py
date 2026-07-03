#!/usr/bin/env python3
"""
元数据聚合工具 — 生成 metadata.json
"""

import json
import re
from datetime import datetime
from pathlib import Path


def generate_metadata(book_title, note_path, output_dir, all_units, passed_units, rejected_units, text_stats=None):
    """生成 metadata.json"""
    slug = Path(note_path).parent.name if Path(note_path).parent.name != "books" else slugify(book_title)

    total, v1p, v2p, v3p = 0, 0, 0, 0
    if all_units:
        from skill_generator import check_v1, check_v2, check_v3
        total = len(all_units)
        v1p = sum(1 for u in all_units if check_v1(u)[0])
        v2p = sum(1 for u in all_units if check_v2(u)[0])
        v3p = sum(1 for u in all_units if check_v3(u)[0])

    metadata = {
        "book_title": book_title,
        "slug": slug,
        "generated_at": datetime.now().isoformat(),
        "version": "0.2.0",
        "stats": {
            "total_methodology_units": total,
            "passed_units": len(passed_units),
            "rejected_units": len(rejected_units),
            "v1_pass": v1p,
            "v2_pass": v2p,
            "v3_pass": v3p,
        },
        "text_stats": text_stats or {},
        "output_files": [
            "SKILL.md",
            "glossary.md",
            "patterns.md",
            "cheatsheet.md",
            "note.md",
        ],
    }

    output_path = Path(output_dir) / slug / "metadata.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  元数据：{output_path}")
    return output_path


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-") or "book"
