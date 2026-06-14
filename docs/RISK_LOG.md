# Risk & Issue Register

Forward-looking risks to the CISC 699 phase (distinct from `KNOWN_ISSUES.md`, which
tracks defects that already exist). **Severity** = impact if it occurs;
**Likelihood** = probability; **Status** = Open / Mitigating / Monitoring / Closed.

| ID | Risk / Issue | Severity | Likelihood | Mitigation Action | Owner | Status |
|----|--------------|----------|------------|-------------------|-------|--------|
| R-01 | Claude migration diverges from the Ollama/FinBERT baseline (different decisions). | High | Medium | Keep Ollama path runnable; build a fixture-based comparison harness; gate migration behind verified parity. | Chirag (Lead) | Mitigating |
| R-02 | Claude API cost/quota overrun during iterative testing. | Medium | Medium | Cache responses; small fixtures for routine tests; monitor console usage. | Chirag (Lead) | Monitoring |
| R-03 | yfinance / Brave Search outage or schema change mid-project. | High | Low | Both already behind service wrappers; cache last-good payloads; offline smoke test stays green regardless. | Chirag (Lead) | Monitoring |
| R-04 | Scope creep — migration + Execution Simulator + Portfolio Agent in one phase. | Medium | Medium | Fixed sequencing; keep pipeline runnable each step; defer extras to future scope. | Chirag (Lead) | Mitigating |
| R-05 | Secret leakage (`.env` / API key committed). | High | Low | `.env` gitignored; only `.env.example` tracked; check `git status` before each commit. | Chirag (Lead) | Mitigating |
| R-06 | Local hardware can't run llama3.2 + FinBERT together during transition. | Medium | Medium | Run services sequentially; Claude migration removes the local LLM load. | Chirag (Lead) | Monitoring |
| R-07 | Academic-integrity concern over AI-assisted code/prompts. | Medium | Low | Maintain `docs/AI_USAGE_LOG.md`; disclose per course policy; confirm with supervisor. | Chirag (Lead) | Mitigating |
| R-08 | Reproducibility failure — a peer can't run the baseline from the README. | Medium | Low | Pinned `requirements.txt`; `.env.example`; offline smoke test; clean-clone self-check. | Chirag (Lead) | Mitigating |
| R-09 | Regression in the 221-test suite during refactors. | Medium | Medium | Run `pytest` before every tag; small, reviewable feature branches. | Chirag (Lead) | Monitoring |
| R-10 | Time pressure from concurrent coursework + work. | Medium | Medium | Small frequent commits; sprint-scoped deliverables; tagged baselines keep progress demonstrable. | Chirag (Lead) | Monitoring |

*Owner listed as sole maintainer; adjust if teammates join this phase.*
