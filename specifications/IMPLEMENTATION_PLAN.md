# Implementation Plan
## Project Name: RetailPulse AI
**Timeline:** 1-Day Accelerated Delivery (College Mini-Project Submission)

---

## 1. Development Stages & Milestones

| Stage | Focus Area | Deliverables | Target Status |
| :--- | :--- | :--- | :--- |
| **Stage 1** | Specifications & Plan | `PRD.md`, `ARCHITECTURE.md`, `DATA_MODEL.md`, `IMPLEMENTATION_PLAN.md`, `TEST_PLAN.md`, `TEAM_TASKS.md` | In Progress / Nearly Done |
| **Stage 2** | Data & Environment Setup | `data/` folder (4 CSVs), `.env.example`, `.gitignore`, `requirements.txt` | Ready to execute |
| **Stage 3** | Deterministic Python Logic | `pricing_engine.py`, `discount_engine.py`, `analytics.py`, `tests/` | Prioritized |
| **Stage 4** | NVIDIA AI & Fallback Layer | `nvidia_client.py`, `review_engine.py`, `retail_advisor.py` | Integrated with graceful fallback |
| **Stage 5** | Streamlit UI Dashboard | `app.py` with 4 distinct analytical modules, KPI cards, Plotly charts | Highly polished |
| **Stage 6** | End-to-End Testing | Unit tests execution, edge cases validation, offline fallback verification | Zero-defect |
| **Stage 7** | Handover & Viva Prep | `README.md`, Demo walk-through script, Viva preparation questions | Ready for faculty presentation |

---

## 2. Risk Matrix & Mitigation Strategy

| Risk | Impact | Likelihood | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **NVIDIA API Key Missing or Unfunded** | High | High | Implement zero-crash fallback in `nvidia_client.py` and `review_engine.py`. Local keyword & sentiment heuristics provide instant results offline. |
| **Division by Zero in Margin/Uplift** | High | Medium | Explicit mathematical guardrails: `if unit_cost == 0` or `if discounted_profit <= 0` return structured error dicts and user warnings. |
| **UI Freezing during AI Calls** | Medium | Medium | Streamlit spinner, caching where suitable, and responsive timeout defaults (15s max). |
| **Data Mismatch across CSVs** | High | Low | Automated integrity checks in `load_all_data()` verifying foreign keys and non-empty rows. |
