"""成本估算器测试"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from cost_estimator import estimate_tokens, estimate_cost


class TestEstimateTokens:
    def test_empty(self):
        assert estimate_tokens("") == 0

    def test_english(self):
        text = "hello world this is a test"
        tokens = estimate_tokens(text)
        assert tokens > 0
        assert tokens < 20

    def test_chinese(self):
        text = "这是一段中文文本用于测试"
        tokens = estimate_tokens(text)
        assert tokens > 0

    def test_mixed(self):
        text = "中文 English 混合 mixed text"
        tokens = estimate_tokens(text)
        assert tokens > 0


class TestEstimateCost:
    def test_estimate_cost_structure(self):
        text = "这是一本示例书籍的内容，用于测试成本估算功能是否正常工作。"
        cost = estimate_cost(text)
        assert "estimated_tokens" in cost
        assert "input_tokens" in cost
        assert "output_tokens_estimate" in cost
        assert "total_cost_usd" in cost
        assert "chars" in cost
        assert cost["chars"] == len(text)
