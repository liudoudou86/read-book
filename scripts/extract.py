#!/usr/bin/env python3
"""
统一书籍提取入口 — 自动识别格式并提取文本
支持：PDF / EPUB / DOCX / TXT / MD
"""

import argparse
import os
import sys
from pathlib import Path


SUFFIX_MAP = {
    ".pdf": ("pdf_extractor", "extract_text_from_pdf"),
    ".epub": ("epub_extractor", "extract_text_from_epub"),
    ".docx": ("docx_extractor", "extract_text_from_docx"),
    ".txt": ("text_extractor", "extract_text_from_txt"),
    ".md": ("text_extractor", "extract_text_from_txt"),
    ".markdown": ("text_extractor", "extract_text_from_txt"),
}


def extract(file_path, output_path=None, **kwargs):
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix not in SUFFIX_MAP:
        print(f"不支持的文件格式：{suffix}")
        print(f"支持格式：{', '.join(SUFFIX_MAP.keys())}")
        return None

    module_name, func_name = SUFFIX_MAP[suffix]

    try:
        import importlib
        mod = importlib.import_module(module_name)
        func = getattr(mod, func_name)

        # 合并 kwargs 和默认参数
        if suffix == ".pdf":
            result = func(
                file_path,
                output_path=output_path,
                start_page=kwargs.get("start", 1),
                end_page=kwargs.get("end"),
                technical=kwargs.get("technical", False),
            )
        else:
            result = func(file_path, output_path=output_path)

        return result
    except ImportError as e:
        print(f"导入模块失败：{e}")
        print("尝试安装依赖：uv add book-to-skill[all]")
        return None
    except Exception as e:
        print(f"提取失败：{e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="统一书籍提取工具")
    parser.add_argument("--file", "-f", type=str, required=True, help="书籍文件路径")
    parser.add_argument("--output", "-o", type=str, help="输出文本文件路径")
    parser.add_argument("--start", "-s", type=int, default=1, help="起始页码（仅 PDF）")
    parser.add_argument("--end", "-e", type=int, help="结束页码（仅 PDF）")
    parser.add_argument("--technical", action="store_true", help="技术类 PDF（优先 docling）")

    args = parser.parse_args()
    result = extract(args.file, args.output, start=args.start, end=args.end, technical=args.technical)

    if result:
        print(f"\n提取完成：{result}")
        print("下一步：使用 Read 工具读取生成的文本文件")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
