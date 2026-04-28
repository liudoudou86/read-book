#!/usr/bin/env python3
"""
RIA++ Skill 生成器 (book2skill)
================================
解析 RIA++ 结构化笔记 → 三重验证过滤 → 生成方法论 Skill

用法:
  uv run python scripts/skill_generator.py --book-title "书名" --note-path "~/.../note.md"
  uv run python scripts/skill_generator.py --action list
  uv run python scripts/skill_generator.py ... --force    # 跳过验证
"""

import argparse
import os
import re
from datetime import datetime
from pathlib import Path


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-") or "book"


def slug_from_path(note_path):
    path = Path(note_path)
    parent = path.parent
    while parent.name != "books" and parent.name != parent.anchor:
        if (parent / "note.md").exists():
            return parent.name
        prev, parent = parent, parent.parent
        if prev == parent:  # reached root (Path("/").parent == Path("/"))
            break
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


def _match_subsection(subsections, *candidates):
    """从 subsections dict 中模糊匹配 key，支持 emoji 后缀"""
    for key in subsections:
        for candidate in candidates:
            if key.startswith(candidate):
                return subsections[key]
    return ""


def parse_methodology_units(content):
    """从笔记中解析方法论单元列表（### 层级），返回列表"""
    units = []
    sections = split_sections(content)
    methodology_section = (
        sections.get("方法论拆解") or sections.get("方法论") or ""
    )
    if not methodology_section:
        return units

    blocks = re.split(r"\n(?=###\s+)", methodology_section)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        heading_match = re.match(r"^###\s+(.+?)(?:\n|$)", block)
        if not heading_match:
            continue
        name = heading_match.group(1).strip()
        body = block[heading_match.end():].strip()

        subsections = {}
        sub_blocks = re.split(r"\n(?=####\s+)", body)
        for sb in sub_blocks:
            sb = sb.strip()
            if not sb:
                continue
            sub_match = re.match(r"^####\s+(.+?)(?:\n|$)", sb)
            if sub_match:
                key = sub_match.group(1).strip()
                val = sb[sub_match.end():].strip()
                subsections[key] = val

        unit = {
            "name": name,
            "R": _match_subsection(subsections, "R — 原文引用", "R"),
            "I": _match_subsection(subsections, "I — 方法论骨架", "I"),
            "A1": _match_subsection(subsections, "A1 — 书中案例", "A1"),
            "A2": _match_subsection(subsections, "A2 — 触发场景", "A2"),
            "E": _match_subsection(subsections, "E — 可执行步骤", "E"),
            "B": _match_subsection(subsections, "B — 边界", "B"),
            "verification": _match_subsection(subsections, "验证记录", "验证"),
        }
        units.append(unit)

    return units

    blocks = re.split(r"\n(?=###\s+)", methodology_section)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        heading_match = re.match(r"^###\s+(.+?)(?:\n|$)", block)
        if not heading_match:
            continue
        name = heading_match.group(1).strip()
        body = block[heading_match.end():].strip()

        subsections = {}
        sub_blocks = re.split(r"\n(?=####\s+)", body)
        for sb in sub_blocks:
            sb = sb.strip()
            if not sb:
                continue
            sub_match = re.match(r"^####\s+(.+?)(?:\n|$)", sb)
            if sub_match:
                key = sub_match.group(1).strip()
                val = sb[sub_match.end():].strip()
                subsections[key] = val

        unit = {
            "name": name,
            "R": subsections.get("R \u2014 \u539f\u6587\u5f15\u7528", "") or subsections.get("R", ""),
            "I": subsections.get("I \u2014 \u65b9\u6cd5\u8bba\u9aa8\u67b6", "") or subsections.get("I", ""),
            "A1": subsections.get("A1 \u2014 \u4e66\u4e2d\u6848\u4f8b", "") or subsections.get("A1", ""),
            "A2": subsections.get("A2 \u2014 \u89e6\u53d1\u573a\u666f", "") or subsections.get("A2", ""),
            "E": subsections.get("E \u2014 \u53ef\u6267\u884c\u6b65\u9aa4", "") or subsections.get("E", ""),
            "B": subsections.get("B \u2014 \u8fb9\u754c", "") or subsections.get("B", ""),
            "verification": subsections.get("\u9a8c\u8bc1\u8bb0\u5f55", "")
                              or subsections.get("\u9a8c\u8bc1", ""),
        }
        units.append(unit)

    return units


# ── 三重验证 ──────────────────────────────────────────────

def check_v1(unit):
    """V1 跨域：检查 R 段是否包含 ≥2 个独立章节来源"""
    r_text = unit.get("R", "")
    if not r_text:
        return False, "R 段为空"
    chapters = re.findall(r"第[一二三四五六七八九十\d百]+[章节部篇]", r_text)
    chapters += re.findall(r"Chapter\s+\d+", r_text, re.IGNORECASE)
    if not chapters:
        chapters = re.findall(r"[—–-]{1,2}\s*\S+?[章节]", r_text)
    unique = set(chapters)
    if len(unique) >= 2:
        return True, f"跨域 ✓ ({', '.join(unique)})"
    return False, f"仅 {len(unique)} 处独立来源"


def check_v2(unit):
    """V2 预测力：检查 A2 段是否 ≥3 条触发场景 + ≥2 个语言信号"""
    a2_text = unit.get("A2", "")
    if not a2_text:
        return False, "A2 段为空"
    scenarios = re.findall(r"^\d+[.、]\s+", a2_text, re.MULTILINE)
    scenarios += re.findall(r"^- ", a2_text, re.MULTILINE)
    signals = len(re.findall(r'"', a2_text)) + len(re.findall(r'「', a2_text))
    if len(scenarios) >= 3 and signals >= 2:
        return True, f"场景 {len(scenarios)} 条, 信号 {signals} 个"
    return False, f"场景 {len(scenarios)} 条 (需≥3), 信号 {signals} 个 (需≥2)"


def check_v3(unit):
    """V3 独特性：检查 B 段 ≥2 条边界 + A1 段有案例"""
    b_text = unit.get("B", "")
    a1_text = unit.get("A1", "")
    if not b_text or not a1_text:
        return False, "B 段或 A1 段为空"
    b_items = len(re.findall(r"^- ", b_text, re.MULTILINE))
    has_case = bool(re.search(r"问题|场景|案例|result|case|结果", a1_text, re.IGNORECASE))
    if b_items >= 2 and has_case:
        return True, f"边界 {b_items} 条, A1 有案例 ✓"
    return False, f"边界 {b_items} 条 (需≥2), A1 案例 {'✓' if has_case else '✗'}"


def triple_verify(unit):
    """对方法论单元执行三重验证"""
    v1_ok, v1_msg = check_v1(unit)
    v2_ok, v2_msg = check_v2(unit)
    v3_ok, v3_msg = check_v3(unit)
    passed = v1_ok and v2_ok and v3_ok
    reasons = []
    if not v1_ok:
        reasons.append(v1_msg)
    if not v2_ok:
        reasons.append(v2_msg)
    if not v3_ok:
        reasons.append(v3_msg)
    return passed, {
        "V1": ("✓" if v1_ok else "✗"),
        "V2": ("✓" if v2_ok else "✗"),
        "V3": ("✓" if v3_ok else "✗"),
        "reasons": reasons,
    }


# ── 笔记信息提取 ──────────────────────────────────────────

def parse_concept_table(content):
    concepts = []
    rows = re.findall(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", content, re.MULTILINE)
    for row in rows:
        name = row[0].strip()
        if not name or name in ("概念", "概念1", "核心概念") or re.match(r"^[-]+$", name):
            continue
        concepts.append({
            "name": name,
            "definition": row[1].strip(),
            "scenario": row[2].strip(),
        })
    return concepts


def extract_verification_summary(units):
    """计算验证统计"""
    total = len(units)
    v1_pass = sum(1 for u in units if check_v1(u)[0])
    v2_pass = sum(1 for u in units if check_v2(u)[0])
    v3_pass = sum(1 for u in units if check_v3(u)[0])
    return total, v1_pass, v2_pass, v3_pass


# ── 输出生成 ──────────────────────────────────────────────

def format_methodology_card(unit, index):
    """生成单个方法论单元的 RIA++ 六段卡片 Markdown"""
    lines = []
    lines.append(f"## 方法论 {index + 1}")
    lines.append("")
    lines.append("### R — 原文引用")
    lines.append("")
    for line in unit["R"].strip().split("\n"):
        lines.append(f">{line}" if not line.startswith(">") else line)
    lines.append("")
    lines.append("### I — 方法论骨架")
    lines.append("")
    lines.append(unit["I"].strip())
    lines.append("")
    lines.append("### A1 — 书中案例")
    lines.append("")
    lines.append(unit["A1"].strip())
    lines.append("")
    lines.append("### A2 — 触发场景 ★")
    lines.append("")
    lines.append(unit["A2"].strip())
    lines.append("")
    lines.append("### E — 可执行步骤")
    lines.append("")
    lines.append(unit["E"].strip())
    lines.append("")
    lines.append("### B — 边界")
    lines.append("")
    lines.append(unit["B"].strip())
    return "\n".join(lines)


def generate_skill(book_title, note_path, output_dir, force=False):
    """主函数：解析笔记 → 验证 → 生成 RIA++ SKILL.md"""
    slug = slug_from_path(note_path) or slugify(book_title)
    output_path = Path(output_dir) / slug
    output_path.mkdir(parents=True, exist_ok=True)

    with open(note_path, "r", encoding="utf-8") as f:
        note_content = f.read()

    sections = split_sections(note_content)

    # ── 基本信息 ──
    title = book_title
    h1_match = re.search(r"^#\s+(.+?)(?:\s*[-–—]\s*读书笔记)?\s*$", note_content, re.MULTILINE)
    if h1_match:
        title = h1_match.group(1).strip()

    author = ""
    info_table = sections.get("书籍信息", "")
    author_match = re.search(r"\|\s*作者\s*\|\s*(.+?)\s*\|", info_table)
    if author_match:
        author = author_match.group(1).strip()

    core_topic = ""
    appendix = sections.get("附录：分析过程记录", "")
    topic_match = re.search(r"一句话概括[：:]\s*(.+?)(?:\n|$)", appendix)
    if topic_match:
        core_topic = topic_match.group(1).strip()

    # ── 解析方法论单元 ──
    all_units = parse_methodology_units(note_content)

    if not all_units:
        print("⚠ 笔记中未找到方法论单元（## 方法论拆解），回退到旧格式解析...")
        return _generate_legacy(book_title, note_path, output_dir, note_content, sections, slug, title, author, core_topic)

    # ── 三重验证 ──
    passed_units = []
    rejected_units = []
    for unit in all_units:
        passed, result = triple_verify(unit)
        if passed or force:
            passed_units.append(unit)
        else:
            rejected_units.append({"unit": unit, "result": result})

    # ── 写入被拒绝的单元 ──
    rejected_dir = output_path / "rejected"
    if rejected_units:
        rejected_dir.mkdir(parents=True, exist_ok=True)
        for r in rejected_units:
            safe_name = re.sub(r"[^\w\- ]", "", r["unit"]["name"]).strip().replace(" ", "_")
            content = (
                f"# {r['unit']['name']} — 被过滤\n\n"
                f"## 验证结果\n\n"
                f"| 维度 | 结果 |\n|------|------|\n"
                f"| V1 跨域 | {r['result']['V1']} |\n"
                f"| V2 预测力 | {r['result']['V2']} |\n"
                f"| V3 独特性 | {r['result']['V3']} |\n\n"
                f"## 未通过原因\n\n"
                + "\n".join(f"- {reason}" for reason in r['result']['reasons'])
                + "\n\n---\n\n"
                + f"## R 段原文\n\n{r['unit']['R']}\n\n"
                + f"## I 段\n\n{r['unit']['I']}\n\n"
                + f"## A1 段\n\n{r['unit']['A1']}\n\n"
                + f"## A2 段\n\n{r['unit']['A2']}\n\n"
                + f"## E 段\n\n{r['unit']['E']}\n\n"
                + f"## B 段\n\n{r['unit']['B']}"
            )
            with open(rejected_dir / f"{safe_name}.md", "w", encoding="utf-8") as f:
                f.write(content)

    # ── 解析核心概念 ──
    concepts = parse_concept_table(sections.get("核心概念", ""))
    concepts_text = ""
    if concepts:
        concepts_text = "| 概念 | 定义 | 适用场景 |\n|------|------|---------|\n"
        for c in concepts:
            concepts_text += f"| {c['name']} | {c['definition']} | {c['scenario']} |\n"

    # ── 构建 A2 摘要（用于 description）──
    a2_summaries = []
    for u in passed_units:
        a2 = u.get("A2", "")
        scenarios = re.findall(r"^\d+[.、]\s*(.+?)$", a2, re.MULTILINE)
        scenarios += re.findall(r"^- (.+?)$", a2, re.MULTILINE)
        a2_summaries.extend(s[:30] for s in scenarios[:2])
    a2_desc = "；".join(a2_summaries[:4]) if a2_summaries else "RIA++ 方法论助手"

    # ── 统计 ──
    total, v1p, v2p, v3p = extract_verification_summary(all_units)

    # ── 生成 SKILL.md ──
    units_cards = []
    for i, u in enumerate(passed_units):
        units_cards.append(format_methodology_card(u, i))
    methods_md = "\n\n---\n\n".join(units_cards)

    skill_content = f"""---
name: book-{slug}
description: |
  {title} — RIA++ 结构化方法论助手。{a2_desc}
user-invocable: true
use_case: |
  当用户询问关于《{title}》的方法论、决策框架、可执行步骤时，应调用本 Skill。
  可使用 "/book-{slug}" 触发。含 {len(passed_units)} 个方法论单元，每个包含
  原文引用(R)、方法论骨架(I)、案例(A1)、触发场景(A2)、执行步骤(E)、边界(B)。
---

# {title} — 方法论助手

> 基于《{title}》的 RIA++ 结构化笔记生成，共 {len(passed_units)} 个方法论单元。
> 由 `skill_generator.py` 自动生成 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 书籍信息

- **作者**：{author}
- **核心主题**：{core_topic if core_topic else title}
- **方法论单元**：{len(passed_units)} 个（初始 {total} 个，{len(rejected_units)} 个未通过三重验证）
- **笔记路径**：{note_path}
- **验证统计**：V1 ✓{v1p}/{total} | V2 ✓{v2p}/{total} | V3 ✓{v3p}/{total}

---

{methods_md}

---

## 核心概念

{concepts_text if concepts_text else "（笔记中无独立核心概念表）"}

---

## 常见的跨方法论问题

**Q: 这本书的核心观点是什么？**
A: {core_topic if core_topic else "见方法论卡片"}

**Q: 这个方法论的局限是什么？**
A: 每个方法论卡片的 B（边界）段有详细说明，包括不适用场景和作者的失败模式警告。请注意书中的时代局限和方法适用的前提条件。

**Q: 这些方法论如何组合使用？**
A: 每个方法论卡片的 A2（触发场景）指出了适用情境。可根据实际场景选择最匹配的方法论，多个方法论可以按先后步骤组合。

---

## 使用说明

当你需要以下帮助时调用本 Skill：
- 想了解《{title}》的某个方法论的具体步骤
- 遇到 {a2_desc} 相关的问题，想参考书中的方法
- 需要可执行的操作步骤指导

**触发词**：`/book-{slug}`

---

## 被过滤的方法论单元

{len(rejected_units)} 个未通过三重验证的单元已写入：
`~/.opencode/skill/books/{slug}/rejected/`

可通过 `ls ~/.opencode/skill/books/{slug}/rejected/` 查看。
如需强制纳入，重新运行脚本时加 `--force` 参数。
"""

    skill_file = output_path / "SKILL.md"
    with open(skill_file, "w", encoding="utf-8") as f:
        f.write(skill_content)

    print(f"✅ RIA++ Skill 已生成！")
    print(f"   路径：{skill_file}")
    print(f"   方法论单元：{len(passed_units)} 个")
    if rejected_units:
        print(f"   被过滤（未通过验证）：{len(rejected_units)} 个 → {rejected_dir}")
    print(f"   触发词：/book-{slug}")

    return skill_file


# ── 旧格式回退 ────────────────────────────────────────────

def _generate_legacy(book_title, note_path, output_dir, note_content, sections, slug, title, author, core_topic):
    """旧版生成逻辑：兼容旧格式笔记"""
    output_path = Path(output_dir) / slug
    output_path.mkdir(parents=True, exist_ok=True)

    viewpoints = []
    for sec_name in ["核心观点（3-5条）", "核心观点", "核心主旨"]:
        sec = sections.get(sec_name, "")
        if not sec:
            continue
        blocks = re.split(r"\n(?=###\s+)", sec)
        for block in blocks:
            vm = re.match(r"^###\s+(.+?)(?:\n|$)", block.strip())
            if vm:
                t = re.sub(r"^观点\d+[：:]\s*", "", vm.group(1).strip())
                body = block[vm.end():].strip()
                viewpoints.append({"title": t, "body": body})
        if viewpoints:
            break
    if not viewpoints:
        core_theme = sections.get("核心主旨", "")
        if core_theme:
            for line in core_theme.split("\n"):
                nm = re.match(r"^\d+[.、]\s*(.+?)$", line.strip())
                if nm:
                    viewpoints.append({"title": nm.group(1).strip(), "body": ""})

    concepts = parse_concept_table(sections.get("知识框架", "")) or parse_concept_table(sections.get("核心概念", ""))
    evaluation = sections.get("我的评价", "") or sections.get("评价与思考", "")
    limits = re.findall(r"^- (.+?)$", evaluation, re.MULTILINE)

    viewpoints_md = "\n\n".join(
        f"{i+1}. **{vp['title']}**" + (f"\n   - {vp['body']}" if vp["body"] else "")
        for i, vp in enumerate(viewpoints)
    )
    concepts_md = "| 概念 | 定义 | 适用场景 |\n|------|------|---------|\n"
    if concepts:
        for c in concepts:
            concepts_md += f"| {c['name']} | {c['definition']} | {c['scenario']} |\n"
    else:
        concepts_md += "| （旧格式笔记中未提取到） | （待补充） | （待补充） |"

    skill_content = f"""---
name: book-{slug}
description: "{title} - 读书笔记助手（旧格式），基于《{title}》"
user-invocable: true
---

# {title} — 读书笔记助手

> 本 Skill 基于旧格式笔记生成，建议迁移到 RIA++ 结构。

## 书籍信息

- 作者：{author}
- 核心主题：{core_topic or title}
- 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 核心观点

{viewpoints_md.strip() if viewpoints_md else "（笔记中未提取到核心观点）"}

---

## 关键概念

{concepts_md.strip()}

---

## 使用说明

当你需要以下帮助时调用本 Skill：
- 想了解《{title}》的核心内容
- 想深入理解书中的概念

**触发词**：`/book-{slug}`
"""

    skill_file = output_path / "SKILL.md"
    with open(skill_file, "w", encoding="utf-8") as f:
        f.write(skill_content)

    print(f"✅ 旧格式 Skill 已生成（兼容模式）")
    print(f"   路径：{skill_file}")
    print(f"   提示：建议升级笔记为 RIA++ 结构以获得更好效果")
    return skill_file


# ── 命令行 ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="RIA++ Skill 生成器")
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
    parser.add_argument(
        "--force",
        action="store_true",
        help="跳过三重验证，强制纳入所有方法论单元",
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

        generate_skill(args.book_title, note_path, books_dir, force=args.force)

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
                    title_match = re.search(r"^# (.+?) —", content, re.MULTILINE)
                    title = title_match.group(1) if title_match else item.name
                    # 统计方法论数量
                    unit_count = len(re.findall(r"^## 方法论 \d+", content, re.MULTILINE))
                    unit_info = f" ({unit_count} 个方法论)" if unit_count else ""
                    rejected_dir = item / "rejected"
                    rejected_info = ""
                    if rejected_dir.exists():
                        rejected_files = list(rejected_dir.iterdir())
                        if rejected_files:
                            rejected_info = f" [被过滤 {len(rejected_files)} 个]"
                    print(f"   · {title}  → /book-{item.name}{unit_info}{rejected_info}")
                else:
                    print(f"   · {item.name} (无 Skill)")


if __name__ == "__main__":
    main()
