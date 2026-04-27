#!/usr/bin/env python3
"""
读书 Skill 生成器
根据读书笔记解析结构化内容，生成专属 AI Skill
"""

import argparse
import os
import re
from datetime import datetime
from pathlib import Path


def slugify(text):
    """将书名转换为 slug 格式（中文转拼音式短横连接，去除非ASCII）"""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-").strip("-") or "book"


def slug_from_path(note_path):
    """从笔记路径中提取 slug（目录名）"""
    path = Path(note_path)
    parent = path.parent
    while parent.name != "books" and parent.name != parent.anchor:
        if (parent / "note.md").exists():
            return parent.name
        parent = parent.parent
    return None


def split_sections(content):
    """按 ## 标题拆分笔记"""
    sections = {}
    current_key = None
    current_lines = []

    def _cleanup(content):
        content = re.sub(r"\n---+\n", "\n", content)
        content = re.sub(r"\n---+\s*$", "", content)
        content = re.sub(r"\n{3,}", "\n\n", content)
        return content.strip()

    for line in content.split("\n"):
        heading_match = re.match(r"^##\s+(.+?)(?:\s*（.*?）)?\s*$", line)
        if heading_match:
            if current_key:
                sections[current_key] = _cleanup("\n".join(current_lines))
            current_key = heading_match.group(1).strip()
            current_lines = []
        else:
            if current_key:
                current_lines.append(line)

    if current_key:
        sections[current_key] = _cleanup("\n".join(current_lines))

    return sections


def parse_table_value(sections, section_name, key):
    """从 sections 中的表格里提取指定 key 的值"""
    content = sections.get(section_name, "")
    pattern = rf"\|\s*{re.escape(key)}\s*\|\s*(.+?)\s*\|"
    match = re.search(pattern, content)
    return match.group(1).strip() if match else ""


def extract_subsection_text(content, sub_heading_pattern):
    """从 section 内容中提取子标题下的文本"""
    pattern = rf"^###\s+{sub_heading_pattern}.*?\n(.*?)(?=\n^###|\n^##|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match:
        return ""
    text = match.group(1)
    text = re.sub(r"[-]{3,}\s*$", "", text.strip())
    return text.strip()


def parse_viewpoints(content):
    """从核心观点 section 中解析观点列表"""
    viewpoints = []
    blocks = re.split(r"\n(?=###\s+)", content)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        heading_match = re.match(r"^###\s+(.+?)(?:\n|$)", block)
        if heading_match:
            title_full = heading_match.group(1).strip()
            # 处理 "观点1：双系统理论" → "观点1：双系统理论"
            body = block[heading_match.end():].strip()
            # 去掉 "观点N：" 前缀使标题更清晰
            display_title = re.sub(r"^观点\d+[：:]\s*", "", title_full)
            viewpoints.append({"title": display_title or title_full, "body": body})
    return viewpoints


def parse_concept_table(content):
    """从核心概念表格中解析概念列表"""
    concepts = []
    rows = re.findall(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", content, re.MULTILINE)
    for row in rows:
        name = row[0].strip()
        # 跳过表头行和分隔行
        if not name or name in ("概念", "概念1") or re.match(r"^[-]+$", name):
            continue
        concepts.append({
            "name": name,
            "definition": row[1].strip(),
            "scenario": row[2].strip(),
        })
    return concepts


def parse_list_items(content):
    """从内容中解析列表项（支持 - 和 1. 格式）"""
    items = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            item = line[2:].strip()
        elif re.match(r"^\d+[.、]\s+", line):
            item = re.sub(r"^\d+[.、]\s+", "", line)
        else:
            continue
        if item and not item.startswith("[") and not item.startswith("#"):
            item = re.sub(r"\*\*(.+?)\*\*", r"\1", item)
            items.append(item)
    return items


def generate_skill(book_title, note_path, output_dir):
    """根据读书笔记生成结构化专属 AI Skill"""
    # 构建 slug：优先从笔记路径提取，fallback 到书名拼音
    slug = slug_from_path(note_path) or slugify(book_title)

    output_path = Path(output_dir) / slug
    output_path.mkdir(parents=True, exist_ok=True)

    with open(note_path, "r", encoding="utf-8") as f:
        note_content = f.read()

    sections = split_sections(note_content)

    # 提取基本信息
    title = parse_table_value(sections, "书籍信息", "书名") or book_title
    if not title or title == "未知":
        # 从笔记标题行提取
        h1_match = re.search(r"^#\s+(.+?)(?:\s*[-–—]\s*读书笔记)?\s*$", note_content, re.MULTILINE)
        if h1_match:
            title = h1_match.group(1).strip()
    title = title or book_title

    author = parse_table_value(sections, "书籍信息", "作者") or ""

    # 提取核心主题：尝试多个来源
    core_topic = ""
    # 来源1：附录中的一句话概括
    appendix = sections.get("附录：分析过程记录", "")
    skeleton_match = re.search(r"一句话概括[：:]\s*(.+?)(?:\n|$)", appendix)
    if skeleton_match:
        core_topic = skeleton_match.group(1).strip()
    # 来源2：书籍骨架中的一句话概括
    if not core_topic:
        skeleton_sec = sections.get("书籍骨架", "")
        summary_match = re.search(r"###\s+一句话概括\s*\n+(.+?)(?=\n###|$)", skeleton_sec, re.DOTALL)
        if summary_match:
            core_topic = summary_match.group(1).strip()

    # 提取核心观点
    viewpoints = parse_viewpoints(
        sections.get("核心观点（3-5条）", "")
        or sections.get("核心观点", "")
        or sections.get("核心主旨", "")
    )
    # 如果还是空的，尝试从 核心主旨 解析编号列表
    if not viewpoints:
        core_theme = sections.get("核心主旨", "")
        if core_theme:
            numbered = re.findall(r"^\d+[.、]\s*(.+?)(?:\n|$)", core_theme, re.MULTILINE)
            for n in numbered:
                n_clean = n.split("\n")[0].strip()
                n_clean = re.sub(r"\*\*(.+?)\*\*", r"\1", n_clean)  # 去掉已有加粗
                if n_clean:
                    viewpoints.append({"title": n_clean, "body": ""})

    # 提取核心概念
    knowledge = sections.get("知识框架", "")
    concepts = parse_concept_table(knowledge)
    # 尝试从独立的 核心概念 section 解析
    if not concepts:
        concepts = parse_concept_table(sections.get("核心概念", ""))

    # 提取评价信息
    evaluation = sections.get("我的评价", "") or sections.get("评价与思考", "")
    limits_section = extract_subsection_text(evaluation, "局限[／/]不足") or extract_subsection_text(evaluation, "不同意的点")
    limits = parse_list_items(limits_section) if limits_section else []

    audience = extract_subsection_text(evaluation, "适合谁读")

    # 提取行动启发
    relevance = sections.get("与我何干", "")
    actions_section = extract_subsection_text(relevance, "行动启发")
    # 尝试从评价与思考中提取
    if not actions_section:
        actions_section = extract_subsection_text(evaluation, "与我何干")
        # 如果包含嵌套格式（如 - **标题**：内容），只取实际内容
        if actions_section:
            lines = []
            for line in actions_section.split("\n"):
                line = line.strip().lstrip("- ").strip()
                line = re.sub(r"\*\*(.+?)\*\*[：:]\s*", "", line)
                if line and not line.startswith("#"):
                    lines.append(line)
            actions_section = "\n".join(lines)
    actions_list = []
    if actions_section:
        for line in actions_section.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                line_clean = re.sub(r"^-\s*\[.\]\s*", "", line)
                line_clean = re.sub(r"^-\s+", "", line_clean)
                line_clean = line_clean.strip()
                if line_clean and not line_clean.startswith("[") and len(line_clean) > 2:
                    actions_list.append(line_clean)

    # 构建核心观点输出
    viewpoints_md_lines = []
    for i, vp in enumerate(viewpoints, 1):
        viewpoints_md_lines.append(f"{i}. **{vp['title']}**")
        if vp["body"]:
            viewpoints_md_lines.append(f"   - {vp['body']}")
    viewpoints_md = "\n\n".join(viewpoints_md_lines) if viewpoints_md_lines else ""

    # 构建关键概念输出
    concepts_md = "| 概念 | 定义 | 适用场景 |\n|------|------|---------|\n"
    if concepts:
        for c in concepts:
            concepts_md += f"| {c['name']} | {c['definition']} | {c['scenario']} |\n"
    else:
        concepts_md += "| （从笔记中提取） | （待补充） | （待补充） |"

    # 构建适用场景
    scenarios_md = "\n".join(f"{i}. {a}" for i, a in enumerate(actions_list, 1)) if actions_list else "（详见笔记中的与我何干章节）"

    # 构建边界与局限
    limits_md = "\n".join(f"- {l}" for l in limits) if limits else "（详见笔记中的我的评价章节）"

    # 构建 FAQ
    faq_lines = []
    faq_lines.append(f"**Q: 这本书的核心观点是什么？**")
    faq_lines.append(f"A: {core_topic if core_topic else '见核心观点章节'}")
    if audience:
        faq_lines.append("")
        faq_lines.append(f"**Q: 这本书适合谁读？**")
        audience_clean = re.sub(r"^-\s+", "", audience, flags=re.MULTILINE).strip()
        audience_clean = re.sub(r"[-]{3,}.*$", "", audience_clean, flags=re.MULTILINE).strip()
        audience_flat = "；".join(filter(None, audience_clean.split("\n"))).strip("；")
        faq_lines.append(f"A: {audience_flat}")
    if limits:
        faq_lines.append("")
        faq_lines.append(f"**Q: 这本书有什么局限？**")
        limits_text = "; ".join(limits[:3])
        faq_lines.append(f"A: {limits_text}")
    faq_md = "\n".join(faq_lines)

    skill_content = f"""---
name: book-{slug}
description: "{title} - 读书笔记助手，基于《{title}》的专属 AI 助手"
user-invocable: true
use_case: |
  当用户询问关于《{title}》的内容、核心观点、方法论、概念解释时，
  应调用本 Skill 回答。用户可通过 /book-{slug} 触发。
---

# {title} 助手

> 本 Skill 基于《{title}》的读书笔记生成，可回答关于这本书的问题。

## 书籍信息

- 作者：{author}
- 核心主题：{core_topic if core_topic else title}
- 笔记来源：{note_path}
- 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 核心观点

{viewpoints_md.strip()}

---

## 关键概念

{concepts_md.strip()}

---

## 适用场景

{scenarios_md.strip()}

---

## 边界与局限

{limits_md.strip()}

---

## 常见问题 FAQ

{faq_md.strip()}

---

## 使用说明

当你需要以下帮助时调用本 Skill：
- 想了解《{title}》的核心内容
- 遇到相关问题时，想参考书中的方法
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
    print(f"   触发词：/book-{slug}")

    return skill_file


def main():
    parser = argparse.ArgumentParser(description="读书笔记生成专属 AI Skill")
    parser.add_argument("--book-title", type=str, help="书名")
    parser.add_argument("--note-path", type=str, help="读书笔记路径")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.path.expanduser("~/.opencode/skill/books"),
        help="输出目录（默认 ~/.opencode/skill/books）",
    )
    parser.add_argument(
        "--action",
        type=str,
        default="generate",
        choices=["generate", "list"],
        help="操作类型",
    )

    args = parser.parse_args()
    books_dir = os.path.expanduser(args.output_dir)

    if args.action == "generate":
        if not args.book_title or not args.note_path:
            print("❌ 请提供书名和笔记路径")
            print("   用法：python skill_generator.py --book-title '书名' --note-path '笔记路径'")
            return

        note_path = os.path.expanduser(args.note_path)
        if not os.path.exists(note_path):
            print(f"❌ 笔记文件不存在：{note_path}")
            return

        generate_skill(args.book_title, note_path, books_dir)

    elif args.action == "list":
        books_path = Path(books_dir)
        if not books_path.exists():
            print("📚 暂无已分析的书籍")
            return

        print("📚 已分析的书籍：")
        for item in sorted(books_path.iterdir()):
            if item.is_dir():
                skill_file = item / "SKILL.md"
                if skill_file.exists():
                    with open(skill_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    title_match = re.search(r"^# (.+?) 助手", content, re.MULTILINE)
                    title = title_match.group(1) if title_match else item.name
                    print(f"   · {title}  → /book-{item.name}")
                else:
                    print(f"   · {item.name} (无 Skill)")


if __name__ == "__main__":
    main()
