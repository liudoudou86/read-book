#!/usr/bin/env python3
"""
成本估算工具 — 在处理前预估 token 消耗

估算公式（cl100k_base 基准）：
- 中文：~1.5 token/字
- 英文：~0.75 token/词
- 混合：~1.2 token/字符

默认模型：GLM-5.2
  - 输入：8元/百万token → 0.008元/千token
  - 输出：28元/百万token → 0.028元/千token
  - 缓存命中：2元/百万token → 0.002元/千token
  - 上下文窗口：1M tokens

用法：
  uv run python scripts/cost_estimator.py --file "./temp/book.txt"
  uv run python scripts/cost_estimator.py --text "some text"
  uv run python scripts/cost_estimator.py --file "./temp/book.txt" --json
"""

import argparse
import re
import sys
from pathlib import Path

# GLM-5.2 默认价格（元/千token）
DEFAULT_INPUT_PRICE = 0.008
DEFAULT_OUTPUT_PRICE = 0.028
DEFAULT_CACHE_PRICE = 0.002


def estimate_tokens(text):
    """估算 token 数量（cl100k_base 近似）"""
    if not text:
        return 0

    total_chars = len(text)
    cn_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    en_words = len(re.findall(r"[a-zA-Z]+", text))
    en_chars = sum(len(w) for w in re.findall(r"[a-zA-Z]+", text))
    other_chars = total_chars - cn_chars - en_chars

    cn_ratio = cn_chars / total_chars if total_chars > 0 else 0

    if cn_ratio > 0.5:
        tokens = cn_chars * 1.5 + en_words * 0.75 + other_chars * 0.25
    else:
        tokens = en_words * 0.75 + cn_chars * 2 + other_chars * 0.25

    return int(tokens)


def estimate_cost(text, input_price=None, output_price=None, cache_price=None):
    """估算处理成本（元，按 GLM-5.2 定价）"""
    tokens = estimate_tokens(text)
    input_tokens = tokens
    output_tokens = max(500, int(tokens * 0.1))

    ip = input_price if input_price is not None else DEFAULT_INPUT_PRICE
    op = output_price if output_price is not None else DEFAULT_OUTPUT_PRICE
    cp = cache_price if cache_price is not None else DEFAULT_CACHE_PRICE

    input_cost = input_tokens / 1000 * ip
    output_cost = output_tokens / 1000 * op
    cache_cost = input_tokens / 1000 * cp

    return {
        "estimated_tokens": tokens,
        "input_tokens": input_tokens,
        "output_tokens_estimate": output_tokens,
        "input_cost_cny": round(input_cost, 4),
        "output_cost_cny": round(output_cost, 4),
        "cache_hit_cost_cny": round(cache_cost, 4),
        "total_cost_cny": round(input_cost + output_cost, 4),
        "total_with_cache_hit_cny": round(cache_cost, 4),
        "chars": len(text),
        "model": "GLM-5.2",
    }


def print_estimate(text, label="文档"):
    """打印成本估算摘要"""
    est = estimate_cost(text)
    print(f"\n{'=' * 44}")
    print(f"  成本估算：{label}")
    print(f"  模型：GLM-5.2（上下文 1M tokens）")
    print(f"{'=' * 44}")
    print(f"  字符数：          {est['chars']:>8,}")
    print(f"  预估 Token 数：   {est['estimated_tokens']:>8,}")
    print(f"  输入 Token：      {est['input_tokens']:>8,}")
    print(f"  输出 Token（估）：{est['output_tokens_estimate']:>8,}")
    print(f"  ──────────────────────────────")
    print(f"  输入成本：        ¥{est['input_cost_cny']:>8.4f}")
    print(f"  输出成本：        ¥{est['output_cost_cny']:>8.4f}")
    print(f"  缓存命中成本：    ¥{est['cache_hit_cost_cny']:>8.4f}  （{DEFAULT_CACHE_PRICE*1000:.1f}元/百万token）")
    print(f"  ──────────────────────────────")
    print(f"  预估总成本：      ¥{est['total_cost_cny']:>8.4f}")
    print(f"{'=' * 44}")
    print(f"  提示：>50K tokens 建议分章处理\n")
    return est


def main():
    parser = argparse.ArgumentParser(description="Token 成本估算工具（GLM-5.2）")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", "-f", type=str, help="文本文件路径")
    group.add_argument("--text", "-t", type=str, help="直接输入文本")
    parser.add_argument(
        "--input-price", type=float, default=None,
        help=f"每千token输入价格（元，默认 {DEFAULT_INPUT_PRICE}）",
    )
    parser.add_argument(
        "--output-price", type=float, default=None,
        help=f"每千token输出价格（元，默认 {DEFAULT_OUTPUT_PRICE}）",
    )
    parser.add_argument(
        "--cache-price", type=float, default=None,
        help=f"每千token缓存命中价格（元，默认 {DEFAULT_CACHE_PRICE}）",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")

    args = parser.parse_args()

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"文件不存在：{path}")
            sys.exit(1)
        text = path.read_text(encoding="utf-8")
        label = path.name
    else:
        text = args.text
        label = "直接输入"

    est = estimate_cost(text, args.input_price, args.output_price, args.cache_price)

    if args.json:
        import json
        print(json.dumps(est, ensure_ascii=False, indent=2))
    else:
        print_estimate(text, label)


if __name__ == "__main__":
    main()
