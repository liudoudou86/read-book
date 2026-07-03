#!/usr/bin/env python3
"""
EPUB 书籍解析工具
回退链：ebooklib+BeautifulSoup → stdlib zipfile+xml
"""

import argparse
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile


def extract_ebooklib(epub_path):
    """方式1: ebooklib + BeautifulSoup"""
    try:
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
        book = epub.read_epub(epub_path)
        parts = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), "html.parser")
                text = soup.get_text(separator="\n").strip()
                if text:
                    parts.append(text)
        return "\n\n".join(parts)
    except Exception:
        pass
    return None


def extract_zipfallback(epub_path):
    """方式2: stdlib zipfile + XML 回退"""
    try:
        import html
        text_parts = []
        with ZipFile(epub_path) as z:
            # 找 OPF 文件
            try:
                container = ET.fromstring(z.read("META-INF/container.xml"))
            except Exception:
                container = None

            if container is not None:
                ns = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
                rootfile = container.find(".//c:rootfile", ns)
                if rootfile is not None:
                    opf_path = rootfile.get("full-path", "")
                else:
                    opf_path = ""
            else:
                opf_path = ""

            # 尝试读取所有 .xhtml / .html 文件
            for name in z.namelist():
                if name.startswith("META-INF/") or name == "mimetype":
                    continue
                if name.endswith((".xhtml", ".html", ".xml")) and not name.endswith(".opf"):
                    try:
                        content = z.read(name)
                        # 简单的 HTML 标签剥离
                        text = content.decode("utf-8", errors="ignore")
                        text = html.unescape(text)
                        text = text.replace("<br/>", "\n").replace("<br />", "\n")
                        text = text.replace("<p>", "\n").replace("</p>", "\n")
                        text = text.replace("<div>", "\n").replace("</div>", "\n")
                        # 剥离标签
                        import re as _re
                        text = _re.sub(r"<[^>]+>", "", text)
                        text = _re.sub(r"\n{3,}", "\n\n", text).strip()
                        if text:
                            text_parts.append(text)
                    except Exception:
                        pass

        return "\n\n".join(text_parts) if text_parts else None
    except Exception:
        pass
    return None


def extract_text_from_epub(epub_path, output_path=None):
    epub_path = Path(epub_path)
    if not epub_path.exists():
        print(f"文件不存在：{epub_path}")
        return None

    print(f"正在读取 EPUB：{epub_path}")

    text = None
    for name, extractor in [("ebooklib", extract_ebooklib), ("zipfile 回退", extract_zipfallback)]:
        print(f"  尝试：{name}...")
        result = extractor(epub_path)
        if result and result.strip():
            text = result
            print(f"  成功：{name}")
            break

    if not text:
        print("所有 EPUB 引擎均提取失败")
        print("提示：安装 ebooklib + beautifulsoup4 可提升提取质量")
        return None

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(f"已保存到：{output_path}")
    else:
        output_path = epub_path.with_suffix(".txt")
        output_path.write_text(text, encoding="utf-8")
        print(f"已保存到：{output_path}")

    print(f"  字符数：{len(text)}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="EPUB 书籍解析工具")
    parser.add_argument("--file", "-f", type=str, required=True, help="EPUB 文件路径")
    parser.add_argument("--output", "-o", type=str, help="输出文本文件路径")
    args = parser.parse_args()
    result = extract_text_from_epub(args.file, args.output)
    if result:
        print("\n下一步：使用 Read 工具读取生成的文本文件")


if __name__ == "__main__":
    main()
