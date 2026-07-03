"""章节检测器测试"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from chapter_detector import detect_chapters, detect_toc, summary


class TestDetectChapters:
    def test_empty_text(self):
        assert detect_chapters("") == []

    def test_no_chapters(self):
        text = "这是一段普通文本\n没有任何章节标题\n只是随便写写"
        assert detect_chapters(text) == []

    def test_cn_chapter(self):
        text = "前言\n第一章 基础知识\n内容内容\n第二章 进阶\n更多内容"
        chapters = detect_chapters(text)
        assert len(chapters) == 2
        assert chapters[0]["title"] == "第一章 基础知识"
        assert chapters[0]["lang"] == "zh"

    def test_en_chapter(self):
        text = "Introduction\nChapter 1: Basics\nSome content\nChapter 2: Advanced\nMore content"
        chapters = detect_chapters(text)
        assert len(chapters) == 2
        assert chapters[0]["title"] == "Chapter 1: Basics"
        assert chapters[0]["lang"] == "en"

    def test_numeric_chapter(self):
        text = "1. 概述\n内容\n2. 方法\n更多内容"
        chapters = detect_chapters(text)
        assert len(chapters) == 2

    def test_mixed_languages(self):
        text = "Chapter 1: Intro\n第一章 基础\nChapter 3: Advanced"
        chapters = detect_chapters(text)
        assert len(chapters) == 3
        langs = set(c["lang"] for c in chapters)
        assert "zh" in langs
        assert "en" in langs


class TestDetectToc:
    def test_has_toc(self):
        text = "目录\n第一章 概述..........1\n第二章 方法..........10\n第三章 案例..........20\n第四章 总结..........30"
        result = detect_toc(text)
        assert result["has_toc"] is True
        assert result["chapter_count"] >= 3

    def test_no_toc(self):
        text = "这是一本没有目录的书\n直接开始正文\n第一章 内容"
        result = detect_toc(text)
        assert result["has_toc"] is False


class TestSummary:
    def test_summary_structure(self):
        text = "第一章 开头\n内容\n第二章 中间\n第三章 结尾"
        s = summary(text)
        assert "total_chapters" in s
        assert "chapters" in s
        assert "toc" in s
        assert "languages_found" in s
