#!/usr/bin/env python3
"""
读书 Skill 生成器
根据读书笔记生成专属 AI Skill
"""

import argparse
import json
import re
import os
from datetime import datetime
from pathlib import Path


def slugify(text):
    """将书名转换为 slug 格式"""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def generate_skill(book_title, note_path, output_dir="./books"):
    """根据读书笔记生成专属 AI Skill"""

    output_path = Path(output_dir) / slugify(book_title)
    output_path.mkdir(parents=True, exist_ok=True)

    with open(note_path, "r", encoding="utf-8") as f:
        note_content = f.read()

    # 提取核心信息
    skill_content = f"""---
name: book-{slugify(book_title)}
description: "{book_title} - 读书笔记助手"
user-invocable: true
---

# {book_title} 助手

> 本 Skill 基于《{book_title}》的读书笔记生成，可回答关于这本书的问题。

---

## 书籍信息

- 来源：{note_path}
- 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 笔记内容

{note_content}

---

## 使用说明

当你需要以下帮助时调用本 Skill：
- 想了解《{book_title}》的核心内容
- 遇到相关问题，想参考书中的方法
- 想深入理解书中的概念
- 想把这本书的知识应用到实际场景

---

## 评价与反馈

如果你对这本书的笔记有任何补充或纠正，请告诉我，我会更新笔记内容。
"""

    skill_file = output_path / "SKILL.md"
    with open(skill_file, "w", encoding="utf-8") as f:
        f.write(skill_content)

    print(f"✅ 专属 Skill 已生成！")
    print(f"   路径：{skill_file}")
    print(f"   触发词：/book-{slugify(book_title)}")

    return skill_file


def main():
    parser = argparse.ArgumentParser(description="读书笔记生成专属 AI Skill")
    parser.add_argument("--book-title", type=str, help="书名")
    parser.add_argument("--note-path", type=str, help="读书笔记路径")
    parser.add_argument("--output-dir", type=str, default="./books", help="输出目录")
    parser.add_argument(
        "--action",
        type=str,
        default="generate",
        choices=["generate", "list"],
        help="操作类型",
    )

    args = parser.parse_args()

    if args.action == "generate":
        if not args.book_title or not args.note_path:
            print("❌ 请提供书名和笔记路径")
            print(
                "   用法：python skill_generator.py --book-title '书名' --note-path '笔记路径'"
            )
            return

        generate_skill(args.book_title, args.note_path, args.output_dir)

    elif args.action == "list":
        # 列出所有已生成的书籍 Skill
        books_dir = Path(args.output_dir)
        if not books_dir.exists():
            print("📚 暂无已分析的书籍")
            return

        print("📚 已分析的书籍：")
        for item in books_dir.iterdir():
            if item.is_dir():
                skill_file = item / "SKILL.md"
                if skill_file.exists():
                    print(f"   - {item.name} → /book-{item.name}")
                else:
                    print(f"   - {item.name} (无 Skill)")


if __name__ == "__main__":
    main()
