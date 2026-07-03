#!/usr/bin/env python3
"""
章节检测工具 — 多语言章节/TOC 检测
支持：中文、英文、日文、数字/罗马数字章节编号

用法：
  uv run python scripts/chapter_detector.py --file "./temp/book.txt"
  uv run python scripts/chapter_detector.py --file "./temp/book.txt" --json
"""

import argparse
import json
import re
import sys
from pathlib import Path


# 中文章节标题模式
CN_CHAPTER_PATTERNS = [
    r"^第[一二三四五六七八九十百千0-9]+[章节部篇卷]",
    r"^第[一二三四五六七八九十百千0-9]+[章节部篇卷]\s+\S+",
    r"^\d+[.、]\s+\S+",
]

# 英文章节标题模式
EN_CHAPTER_PATTERNS = [
    r"^Chapter\s+\d+",
    r"^Chapter\s+\d+[:\-]\s+\S+",
    r"^\d+\.\d+\s+\S+",
    r"^Part\s+[IVXLCDM\d]+",
    r"^Section\s+\d+",
]

# 日文章节标题模式
JP_CHAPTER_PATTERNS = [
    r"^第[一二三四五六七八九十0-9]+[章話節]",
    r"^\d+[.、]\s+\S+",
]

ALL_PATTERNS = [
    ("zh", CN_CHAPTER_PATTERNS),
    ("en", EN_CHAPTER_PATTERNS),
    ("ja", JP_CHAPTER_PATTERNS),
]


def detect_chapters(text, max_lines=5000):
    """检测文本中的章节标题，返回章节列表"""
    chapters = []
    lines = text.split("\n")[:max_lines]

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue
        if len(line_stripped) > 100:
            continue
        if re.match(r"^[-—=*]{3,}$", line_stripped):
            continue

        match = None
        lang = None
        for lang_name, patterns in ALL_PATTERNS:
            for pattern in patterns:
                if re.match(pattern, line_stripped, re.IGNORECASE if lang_name == "en" else 0):
                    match = line_stripped
                    lang = lang_name
                    break
            if match:
                break

        if match:
            chapters.append({
                "line_number": i + 1,
                "title": line_stripped[:80],
                "lang": lang,
            })

    return chapters


def detect_toc(text, max_lines=200):
    """检测目录区域"""
    lines = text.split("\n")[:max_lines]
    toc_start = None
    chapter_hits = 0

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue

        if re.match(r"^(目录|CONTENTS|Table\s+of\s+Contents|目次)", line_stripped, re.IGNORECASE):
            toc_start = i
            continue

        if toc_start is not None and toc_start != i:
            is_chapter = False
            for lang_name, patterns in ALL_PATTERNS:
                for pattern in patterns:
                    if re.match(pattern, line_stripped, re.IGNORECASE if lang_name == "en" else 0):
                        is_chapter = True
                        break
                if is_chapter:
                    break
            if is_chapter:
                chapter_hits += 1

    return {
        "has_toc": toc_start is not None and chapter_hits >= 3,
        "toc_line": toc_start + 1 if toc_start is not None else None,
        "chapter_count": chapter_hits,
    }


def summary(text):
    """返回章节检测摘要"""
    chapters = detect_chapters(text)
    toc = detect_toc(text)
    return {
        "total_chapters": len(chapters),
        "chapters": chapters[:50],
        "toc": toc,
        "languages_found": list(set(c["lang"] for c in chapters)),
    }


def print_summary(text, label="文档"):
    """打印人类可读的摘要"""
    s = summary(text)
    print(f"\n{'=' * 44}")
    print(f"  章节检测：{label}")
    print(f"{'=' * 44}")
    print(f"  检测到章节：{s['total_chapters']} 个")
    if s["languages_found"]:
        print(f"  章节语言：{', '.join(s['languages_found'])}")
    print(f"  含目录(TOC)：{'是' if s['toc']['has_toc'] else '否'}")
    if s['toc']['has_toc']:
        print(f"  目录位置：第 {s['toc']['toc_line']} 行")
        print(f"  目录内章节数：{s['toc']['chapter_count']}")
    print()
    if s["chapters"]:
        print("  前 20 个章节：")
        for ch in s["chapters"][:20]:
            print(f"    L{ch['line_number']:>5} [{ch['lang']}] {ch['title']}")
    print(f"{'=' * 44}\n")
    return s


def main():
    parser = argparse.ArgumentParser(description="章节检测工具")
    parser.add_argument("--file", "-f", type=str, required=True, help="文本文件路径")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    args = parser.parse_args()
    path = Path(args.file)
    if not path.exists():
        print(f"文件不存在：{path}")
        sys.exit(1)

    text = path.read_text(encoding="utf-8")
    s = summary(text)

    if args.json:
        print(json.dumps(s, ensure_ascii=False, indent=2))
    else:
        print_summary(text, path.name)
        # 如果章节太多，给出建议
        if s["total_chapters"] > 30:
            print("  提示：章节较多，建议按章节分步处理而非一次性读取全文")


if __name__ == "__main__":
    main()
