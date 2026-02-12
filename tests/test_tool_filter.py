"""Tests for strict tool safety policy."""

from stocks_fetch.agent.tool_filter import is_tool_allowed


def test_kite_blocks_risky_mutation_keywords() -> None:
    assert is_tool_allowed("place_order", "kite") is False
    assert is_tool_allowed("modify_gtt_order", "kite") is False
    assert is_tool_allowed("cancel_order", "kite") is False
    assert is_tool_allowed("squareoff_position", "kite") is False


def test_kite_allows_explicit_readonly_tools() -> None:
    assert is_tool_allowed("login", "kite") is True
    assert is_tool_allowed("get_holdings", "kite") is True
    assert is_tool_allowed("get_positions", "kite") is True
    assert is_tool_allowed("get_quote", "kite") is True


def test_stock_analyzer_tool_allowlist() -> None:
    assert is_tool_allowed("get_fundamental_ratios", "stock-analyzer") is True
    assert is_tool_allowed("get_stock_correlations", "stock-analyzer") is True
    assert is_tool_allowed("unknown_tool", "stock-analyzer") is False
