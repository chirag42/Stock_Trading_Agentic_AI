"""
benchmarks/rule_oracle.py — Deterministic baseline for LLM comparison (Hard Stop 4).

The Strategy Agent's prompt instructs the LLM to follow strict rules:
    - BUY  only when RSI oversold (< 35)  AND MACD bullish (macd > signal)
    - SELL only when RSI overbought (> 65) AND MACD bearish (macd < signal)
    - HOLD otherwise (mixed/unclear, or when in doubt)

This module implements those exact rules as a pure, deterministic function. It is the
comparison baseline for Experiment 2: it lets us measure how often the (non-deterministic)
LLM actually agrees with the rules it was told to follow.
"""


def rule_decision(rsi: float, macd: float, signal: float) -> str:
    """Return BUY / SELL / HOLD by applying the prompt's stated rules exactly."""
    bullish = macd > signal
    bearish = macd < signal
    if rsi < 35 and bullish:
        return "BUY"
    if rsi > 65 and bearish:
        return "SELL"
    return "HOLD"
