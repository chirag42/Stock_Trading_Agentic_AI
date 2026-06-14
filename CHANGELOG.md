# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/);
versioning per [SemVer](https://semver.org/).

## [Unreleased]
### Planned (CISC 699)
- Add Claude-backed client in `agents/strategy_agent/llm_client.py`; comparison harness vs Ollama/FinBERT.
- Implement Execution Simulator (entry/exit, P&L, feedback to Strategy Agent).
- Implement Portfolio Agent (user profile → watchlist + dynamic risk thresholds).

## [0.1.0] — 2026-06-14
**CISC 699 Implementation Sprint I — Engineering Baseline**

### Added
- `requirements.txt` (pinned dependencies) and `.env.example`.
- `tests/smoke_test.py` — offline baseline check (imports all core modules; exercises
  real SignalFilter + RiskValidator).
- Documentation set under `docs/`: architecture notes, known-issues log, risk register,
  sprint reflection, AI usage log; refreshed `README.md`; this changelog.

### Changed
- `README.md` updated to reflect the modular subpackage structure and corrected status
  (Risk Validator, Signal Filter, Strategy Agent all complete + tested).

### Fixed
- Untracked the accidentally committed `.coverage` test artifact; added to `.gitignore`.

### Baseline (pre-existing, verified — GRAD 695)
- Modular `services/data_ingestion/` and `services/sentiment_analysis/`.
- `agents/signal_filter.py`, `agents/risk_validator.py`, `agents/strategy_agent/`.
- `core/scheduler.py`, `pipeline.py`, `scripts/run_*.py`.
- **221 passing unit tests** mirrored per component under `tests/`.

### Notes
- Tagged reference point `release-2026-sprint1-v0.1.0` for future-sprint comparison.
- LLM migration to Claude begins next sprint; Ollama/llama3.2 remains the default
  until parity is verified.
