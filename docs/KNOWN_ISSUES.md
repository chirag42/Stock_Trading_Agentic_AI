# Known Issues Log

Open defects, limitations, and technical debt. Severity: **High** (blocks core) /
**Medium** (degrades quality/reliability) / **Low** (minor). Resolved items move to
`CHANGELOG.md`.

| ID | Title | Severity | Component | Description | Workaround | Status |
|----|-------|----------|-----------|-------------|------------|--------|
| KI-01 | `.coverage` committed to VCS | Low | repo | A pytest coverage artifact was tracked in Git; build artifacts shouldn't be versioned. | Added to `.gitignore`; untrack via `git rm --cached .coverage`. | Resolving |
| KI-02 | No dependency lockfile (until this sprint) | Medium | env | README previously listed manual `pip install` commands; no pinned versions, so environments could drift. | `requirements.txt` added this sprint. | Resolving |
| KI-03 | Strategy Agent requires local Ollama | Medium | `agents/strategy_agent/llm_client.py` | `decide()` fails if Ollama isn't running (`LLMConnectionError`); ties the system to a local runtime. | Ensure `ollama serve` + `ollama pull llama3.2`. Claude migration removes this dependency. | Open |
| KI-04 | Risk thresholds hardcoded | Medium | `agents/risk_validator.py` | 5% stop / 20% position max are constructor defaults, not driven by a user profile. | Acceptable for single-ticker runs; Portfolio Agent will inject dynamic values. | Open |
| KI-05 | Brave Search rate limiting | Medium | `services/sentiment_analysis/fetcher.py` | Free-tier throttling can thin the headline set under rapid calls. | Cache recent results; backoff on `BraveAPIRateLimitError`. | Open |
| KI-06 | Execution Simulator absent | High | (planned) | The trade-execution + P&L feedback loop is not yet built, so the agentic learning loop isn't closed. | Pipeline runs through Risk Validator; execution is the next deliverable. | Open |
| KI-07 | Portfolio Agent absent | Medium | (planned) | No profile-to-allocation logic yet. | N/A — planned CISC 699 work. | Open |
| KI-08 | FinBERT memory footprint | Low | `services/sentiment_analysis/classifier.py` | torch + FinBERT is memory-heavy alongside Ollama on the dev machine. | Run services sequentially when constrained; Claude migration relieves this. | Open |
| KI-09 | No automated CI | Low | repo | Tests run locally via `pytest`; nothing runs on push. | Run `pytest` before tagging; consider a GitHub Actions workflow next sprint. | Open |
