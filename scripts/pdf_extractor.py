#!/usr/bin/env python3
"""
PDF 书籍解析工具 - 修复编码版本
"""

import argparse
import os
import sys
from pathlib import Path

try:
    import pypdf
except ImportError:
    print("❌ 缺少 pypdf 库")
    sys.exit(1)


def fix_encoding(text):
    """修复编码问题：从 latin-1 误解读转为 GBK"""
    if not text:
        return ""
    try:
        return text.encode("latin-1").decode("gbk", errors="ignore")
    except:
        return text


def extract_text_from_pdf(pdf_path, output_path=None, start_page=1, end_page=None):
    """从 PDF 中提取文本"""

    if not os.path.exists(pdf_path):
        print(f"❌ 文件不存在：{pdf_path}")
        return None

    print(f"📖 正在读取：{pdf_path}")

    try:
        reader = pypdf.PdfReader(pdf_path)
        total_pages = len(reader.pages)
        print(f"   总页数：{total_pages}")

        end_page = end_page or total_pages
        start_page = max(1, start_page)
        end_page = min(total_pages, end_page)

        text_parts = []

        for page_num in range(start_page - 1, end_page):
            page = reader.pages[page_num]
            text = page.extract_text()

            if text:
                fixed_text = fix_encoding(text)
                text_parts.append(f"--- 第 {page_num + 1} 页 ---\n")
                text_parts.append(fixed_text)
                text_parts.append("\n")

            if (page_num + 1) % 50 == 0:
                print(f"   已处理：{page_num + 1}/{total_pages}")

        full_text = "\n".join(text_parts)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_text)

            print(f"✅ 已保存到：{output_path}")
            print(f"   字符数：{len(full_text)}")
            return output_path
        else:
            txt_path = Path(pdf_path).with_suffix(".txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(full_text)

            print(f"✅ 已保存到：{txt_path}")
            print(f"   字符数：{len(full_text)}")
            return txt_path

    except Exception as e:
        print(f"❌ 读取失败：{e}")
        import traceback

        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(description="PDF 书籍解析工具")
    parser.add_argument("--file", "-f", type=str, required=True, help="PDF 文件路径")
    parser.add_argument("--output", "-o", type=str, help="输出文本文件路径")
    parser.add_argument("--start", "-s", type=int, default=1, help="起始页码")
    parser.add_argument("--end", "-e", type=int, help="结束页码")

    args = parser.parse_args()

    result = extract_text_from_pdf(args.file, args.output, args.start, args.end)

    if result:
        print(f"\n📝 下一步：使用 Read 工具读取生成的文本文件")


if __name__ == "__main__":
    main()
