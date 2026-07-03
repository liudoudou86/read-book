"""Skill 生成器测试"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from skill_generator import (
    slugify,
    split_sections,
    parse_methodology_units,
    parse_concept_table,
    check_v1, check_v2, check_v3,
    triple_verify,
    format_methodology_card,
)


class TestSlugify:
    def test_basic(self):
        assert slugify("刻意练习") == "刻意练习"
        assert slugify("How to Read a Book") == "how-to-read-a-book"

    def test_special_chars(self):
        assert slugify("Test!@# Title") == "test-title"


class TestSplitSections:
    def test_empty(self):
        assert split_sections("") == {}

    def test_simple(self):
        content = "## 核心概念\n概念1\n## 方法论\n方法1"
        sections = split_sections(content)
        assert "核心概念" in sections
        assert "方法论" in sections

    def test_no_headings(self):
        content = "普通文本\n没有标题"
        assert split_sections(content) == {}


class TestParseMethodologyUnits:
    def test_empty(self):
        assert parse_methodology_units("") == []

    def test_no_methodology_section(self):
        content = "## 核心概念\n概念1"
        assert parse_methodology_units(content) == []

    def test_with_units(self):
        content = """## 方法论拆解

### 方法论1

#### R — 原文引用
> 原文内容

#### I — 方法论骨架
骨架描述

#### A1 — 书中案例
- **问题**：问题描述

#### A2 — 触发场景
1. 场景1
2. 场景2
3. 场景3

"信号1"

#### E — 可执行步骤
1. 步骤1
2. 步骤2

#### B — 边界
- 边界1
- 边界2
"""
        units = parse_methodology_units(content)
        assert len(units) == 1
        assert units[0]["name"] == "方法论1"
        assert "原文内容" in units[0]["R"]
        assert "骨架描述" in units[0]["I"]


class TestParseConceptTable:
    def test_empty(self):
        assert parse_concept_table("") == []

    def test_valid_table(self):
        content = "| 概念 | 定义 | 适用场景 |\n|------|------|---------|\n| 概念1 | 定义1 | 场景1 |\n| 概念2 | 定义2 | 场景2 |"
        concepts = parse_concept_table(content)
        assert len(concepts) == 2
        assert concepts[0]["name"] == "概念1"


class TestTripleVerify:
    def make_unit(self, r="", a1="", a2="", b=""):
        return {"R": r, "I": "骨架", "A1": a1, "A2": a2, "E": "步骤", "B": b, "name": "测试"}

    def test_all_pass(self):
        unit = self.make_unit(
            r="来自第一章的内容和第2章的补充",
            a2="1. 场景1\n2. 场景2\n3. 场景3\n\"信号1\"\n\"信号2\"",
            a1="问题描述：某个场景下的案例结果",
            b="- 边界1\n- 边界2",
        )
        passed, result = triple_verify(unit)
        assert passed is True

    def test_r_empty(self):
        unit = self.make_unit(r="")
        passed, result = triple_verify(unit)
        assert passed is False
        assert result["V1"] == "✗"


class TestFormatMethodologyCard:
    def test_basic_format(self):
        unit = {
            "name": "测试方法",
            "R": "> 引用内容\n> — 第1章",
            "I": "方法论骨架内容",
            "A1": "案例描述",
            "A2": "1. 场景1\n2. 场景2\n3. 场景3",
            "E": "1. 步骤1\n2. 步骤2",
            "B": "- 边界1\n- 边界2",
        }
        card = format_methodology_card(unit, 0)
        assert "## 方法论 1" in card
        assert "### R" in card
        assert "### I" in card
        assert "### A1" in card
        assert "### A2" in card
        assert "### E" in card
        assert "### B" in card
