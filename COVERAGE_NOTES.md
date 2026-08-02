# Research repo — coverage improvements (Sprint 7)

Result: ~75% → 95% line coverage; 221 → 280 tests.

## New test files (drop into your repo, preserving these paths)
- tests/risk_validator/test_risk_validator.py   — risk_validator.py 0% → 100%
- tests/strategy_agent/test_claude_client.py     — claude_client.py 39% → 100%
- tests/fundamentals/test_fundamentals.py        — fundamentals.py 18% → 86%
- tests/pipeline/test_pipeline.py                — pipeline.py 30% → 100%
- tests/scheduler/test_scheduler_run_once.py     — scheduler.py 77% → 90% (FinBERT-safe)
- tests/strategy_agent/test_prompt_builder.py    — MODIFIED: appended fundamentals-branch tests → 100%
  (this file replaces your existing one; it keeps all prior tests and adds a class at the end)

## .coveragerc
Excludes entry points, demo `__main__` blocks, scripts, benchmarks, and the
infinite `start()` loop so the number reflects real logic. Run coverage with:

    pytest --cov=agents --cov=services --cov=core --cov=pipeline --cov-report=term-missing

## Notes
- All new tests mock yfinance / the Anthropic SDK — no network, no FinBERT download.
- api_server.py is omitted from the metric for now (new HTTP layer); it's the
  natural next target if you want it measured.
- Add `pytest-cov==5.0.0` to requirements.txt so the coverage run is reproducible.
