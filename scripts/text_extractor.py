#!/usr/bin/env python3
"""
纯文本/Markdown 读取工具 — BOM 感知解码
"""

import argparse
from pathlib import Path


def extract_text_from_txt(txt_path, output_path=None):
    txt_path = Path(txt_path)
    if not txt_path.exists():
        print(f"文件不存在：{txt_path}")
        return None

    print(f"正在读取：{txt_path}")

    # BOM 感知解码
    raw = txt_path.read_bytes()
    text = None
    for encoding in ["utf-8-sig", "utf-16-le", "utf-16-be", "utf-32-le", "utf-32-be", "cp1252", "latin-1"]:
        try:
            text = raw.decode(encoding)
            break
        except (UnicodeDecodeError, LookupError):
            continue

    if text is None:
        text = raw.decode("utf-8", errors="replace")

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(f"已保存到：{output_path}")
    else:
        output_path = txt_path
        print(f"直接读取：{txt_path}")

    print(f"  字符数：{len(text)}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="文本文件读取工具")
    parser.add_argument("--file", "-f", type=str, required=True, help="文本文件路径")
    parser.add_argument("--output", "-o", type=str, help="输出文件路径")
    args = parser.parse_args()
    result = extract_text_from_txt(args.file, args.output)
    if result:
        print("\n完成")


if __name__ == "__main__":
    main()
