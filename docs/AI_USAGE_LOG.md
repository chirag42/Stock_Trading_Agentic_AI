# AI Usage Log

Per course academic-integrity policy, all AI-assisted ideation, code-generation trials,
diagram assistance, and documentation support is logged here. The student reviews,
verifies, and owns all submitted work.

| ID | Date | Tool | Task | How AI Was Used | Student Verification |
|----|------|------|------|-----------------|----------------------|
| AI-01 | 2026-06-14 | Claude | Sprint I baseline package | Inspected the existing repo, then drafted the reproducibility + documentation set (refreshed README, requirements.txt, .env.example, architecture/known-issues/risk/reflection docs) and the offline smoke test, all mapped to the assignment rubric. | Ran the smoke test against the real repo (8/8 imports pass; real SignalFilter + RiskValidator pass); confirmed component states match the actual code; will re-run `pytest` locally before tagging. |
| AI-02 | *(fill in)* | *(tool)* | *(task)* | *(describe)* | *(how you checked it)* |

## Responsible-Use Notes
- AI was used as a drafting and structuring aid, not a substitute for engineering
  judgement. Design decisions and the project's direction are the student's own.
- All AI-drafted content was reviewed before inclusion; `TODO` / *(fill in)* markers
  indicate items the student must complete or verify directly.
- No proprietary or sensitive data was shared with any AI tool. Secrets and API keys are
  excluded from version control and were never provided.
- The planned Claude API integration is a *runtime component of the system under study*
  and is documented in the design docs; this log covers AI assistance to the student's
  *development process*.

> **For submission:** add a row for each additional AI-assisted activity during the
> sprint, with your own verification note.
