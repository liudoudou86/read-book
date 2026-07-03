#!/usr/bin/env python3
"""
PDF 书籍解析工具 — 多层回退链版本
回退顺序：docling (技术类) → pdftotext (poppler) → pypdf → pdfminer.six
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def extract_pdftotext(pdf_path):
    """方式1: pdftotext (poppler)"""
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def extract_pypdf(pdf_path):
    """方式2: pypdf"""
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        parts = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                parts.append(f"--- 第 {i + 1} 页 ---\n{text}")
        return "\n".join(parts)
    except Exception:
        pass
    return None


def extract_pdfminer(pdf_path):
    """方式3: pdfminer.six (回退)"""
    try:
        from pdfminer.high_level import extract_text
        return extract_text(pdf_path)
    except Exception:
        pass
    return None


def extract_docling(pdf_path):
    """方式0: docling (技术类书籍专用)"""
    try:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        return result.document.export_to_markdown()
    except Exception:
        pass
    return None


def extract_text_from_pdf(pdf_path, output_path=None, start_page=1, end_page=None, technical=False):
    """多层回退链提取 PDF 文本"""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"文件不存在：{pdf_path}")
        return None

    total_pages = 0
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        total_pages = len(reader.pages)
    except Exception:
        pass

    print(f"正在读取：{pdf_path}")

    if total_pages:
        print(f"  总页数：{total_pages}")
        end_page = end_page or total_pages
        start_page = max(1, start_page)
        end_page = min(total_pages, end_page)
    else:
        start_page = 1

    # 回退链
    extractors = []
    if technical:
        extractors.append(("docling (技术类)", extract_docling))
    extractors += [
        ("pdftotext (poppler)", extract_pdftotext),
        ("pypdf", extract_pypdf),
        ("pdfminer.six", extract_pdfminer),
    ]

    text = None
    used = None
    for name, extractor in extractors:
        print(f"  尝试：{name}...")
        result = extractor(pdf_path)
        if result and result.strip():
            text = result
            used = name
            print(f"  成功：{name}")
            break

    if not text:
        print("所有 PDF 引擎均提取失败")
        return None

    # 分页截取
    if start_page > 1 or end_page and total_pages:
        pages = text.split("--- 第 ")
        kept = [pages[0]] if pages else []
        for p in pages[1:]:
            try:
                page_num = int(p.split(" ")[0].split("---")[0].strip())
                if start_page <= page_num <= (end_page or total_pages or page_num):
                    kept.append(f"--- 第 {p}")
            except ValueError:
                kept.append(p)
        text = "\n".join(kept)

    # 写入输出
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(f"已保存到：{output_path}")
    else:
        output_path = pdf_path.with_suffix(".txt")
        output_path.write_text(text, encoding="utf-8")
        print(f"已保存到：{output_path}")

    print(f"  字符数：{len(text)}")
    print(f"  使用引擎：{used}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="PDF 书籍解析工具（多层回退链）")
    parser.add_argument("--file", "-f", type=str, required=True, help="PDF 文件路径")
    parser.add_argument("--output", "-o", type=str, help="输出文本文件路径")
    parser.add_argument("--start", "-s", type=int, default=1, help="起始页码")
    parser.add_argument("--end", "-e", type=int, help="结束页码")
    parser.add_argument("--technical", action="store_true", help="技术类书籍（优先使用 docling）")

    args = parser.parse_args()
    result = extract_text_from_pdf(
        args.file, args.output, args.start, args.end, technical=args.technical
    )
    if result:
        print("\n下一步：使用 Read 工具读取生成的文本文件")


if __name__ == "__main__":
    main()
