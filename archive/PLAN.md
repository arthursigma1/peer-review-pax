# Strategy Drift Detector — Hackathon Build Plan

## What We're Building

An AI agent that ingests a public company's **stated strategic pillars** (from investor decks, annual reports) and then evaluates whether their **actual actions** (capital allocation, announced projects, earnings commentary) align with those pillars — flagging drift, contradictions, and silent priority shifts.

**Target company for demo:** Pick one (e.g. Tesla, Google, or Meta) — whoever grabs this first locks it in the `data/raw/` folder.

---

## Architecture Overview

```
┌─────────────┐     ┌──────────┐     ┌────────────┐     ┌───────────┐
│  Ingestion   │────▶│  Parser  │────▶│  Analyzer  │────▶│  Output   │
│  (docs, URLs)│     │(structure)│     │ (LLM agent)│     │(report/UI)│
└─────────────┘     └──────────┘     └────────────┘     └───────────┘
       │                  │                 │                   │
   Person 1           Person 2          Person 3         Person 4 & 5
```

### Components

| Component | Directory | What it does |
|---|---|---|
| **Ingestion** | `src/ingestion/` | Fetches and stores raw documents (PDFs, transcripts, press releases) |
| **Parser** | `src/parser/` | Extracts structured data: strategic pillars, capital moves, commitments |
| **Analyzer** | `src/analyzer/` | LLM-powered agent that scores alignment & flags drift |
| **API** | `src/api/` | FastAPI backend serving analysis results |
| **UI** | `src/ui/` | Simple frontend to display the drift report |

---

## Team Assignments (5 People)

### Person 1 — Data Ingestion & Collection
**Goal:** Get raw company data into `data/raw/` and build pipelines to fetch it.

- [ ] Pick target company, gather 2-3 investor presentations (PDF/text)
- [ ] Gather last 2-4 earnings call transcripts (via public sources / SEC EDGAR)
- [ ] Gather recent press releases or major announcements
- [ ] Build `src/ingestion/fetcher.py` — script to download & store documents
- [ ] Build `src/ingestion/loader.py` — unified loader that reads PDF/text/HTML into plain text
- [ ] Store everything in `data/raw/` with clear naming (`{company}_{type}_{date}.txt`)

**Deps:** None — start immediately.

### Person 2 — Parser & Knowledge Structuring
**Goal:** Turn raw documents into structured, machine-readable strategy data.

- [ ] Define the core data schema in `src/parser/schema.py`:
  ```python
  StrategicPillar     — name, description, source_doc, date
  CapitalAllocation   — amount, target_area, date, source_doc
  PublicCommitment    — statement, area, date, source_doc
  Initiative          — name, description, linked_pillar, date, source_doc
  ```
- [ ] Build `src/parser/strategy_extractor.py` — LLM prompt chain that reads a document and extracts strategic pillars
- [ ] Build `src/parser/action_extractor.py` — extracts capital allocations, project announcements, commitments
- [ ] Write extraction prompts in `prompts/extract_pillars.md` and `prompts/extract_actions.md`
- [ ] Output structured JSON to `data/processed/`

**Deps:** Needs sample raw docs from Person 1 (coordinate early, share 1 doc ASAP).

### Person 3 — Drift Analysis Agent (Core Logic)
**Goal:** Build the LLM agent that reasons about alignment and flags drift.

- [ ] Build `src/analyzer/drift_scorer.py` — takes pillars + actions, scores alignment per pillar (0-100)
- [ ] Build `src/analyzer/drift_detector.py` — flags specific inconsistencies:
  - Capital going to non-strategic areas
  - Announced projects that don't map to any stated pillar
  - Pillars with zero or declining resource allocation
  - Contradictions between stated priorities and actions
- [ ] Build `src/analyzer/report_generator.py` — produces a structured drift report (JSON + narrative)
- [ ] Write analysis prompts in `prompts/analyze_drift.md` and `prompts/score_alignment.md`
- [ ] Include confidence scores and evidence citations in output

**Deps:** Needs schema from Person 2. Can start with mock data and swap in real data later.

### Person 4 — API & Orchestration
**Goal:** Wire everything together into a runnable pipeline with an API.

- [ ] Build `src/api/main.py` — FastAPI app with endpoints:
  - `POST /analyze` — trigger full pipeline for a company
  - `GET /report/{company}` — get latest drift report
  - `GET /pillars/{company}` — get extracted pillars
  - `GET /health` — health check
- [ ] Build `src/api/pipeline.py` — orchestrator that runs ingestion → parsing → analysis in sequence
- [ ] Add `requirements.txt` or `pyproject.toml` with all dependencies
- [ ] Add basic error handling and logging
- [ ] Write a `Makefile` or scripts in `scripts/` for common tasks (`run`, `analyze`, `test`)

**Deps:** Needs interfaces from Persons 1-3. Can scaffold with stubs early.

### Person 5 — Output, UI & Demo Polish
**Goal:** Make the output readable and demo-ready.

- [ ] Build `src/ui/` — simple Streamlit or HTML dashboard showing:
  - Company strategic pillars (with sources)
  - Alignment heatmap (pillar × time period)
  - Flagged drift items with evidence
  - Overall drift score
- [ ] Build `src/ui/report_renderer.py` — turns JSON report into formatted markdown/HTML
- [ ] Create sample output in `data/processed/sample_report.json` for development
- [ ] Prepare demo script / walkthrough
- [ ] Write final `README.md` with setup instructions and project description

**Deps:** Needs report JSON format from Person 3. Can mock it and build UI in parallel.

---

## Shared Conventions

### Git Workflow
- **Branch per person:** `feat/ingestion`, `feat/parser`, `feat/analyzer`, `feat/api`, `feat/ui`
- Merge to `main` via PR — at least one other person reviews
- Commit often, push often — don't sit on code

### Code Conventions
- Python 3.11+
- Use type hints
- Keep functions small and focused
- Every LLM prompt lives in `prompts/` as a markdown file — not hardcoded in Python
- Environment variables for API keys (`.env` file, never committed)

### LLM Usage
- Use Claude API (Anthropic SDK) as the primary LLM
- All prompts are in `prompts/` directory — version controlled and reviewable
- Wrap LLM calls in a thin utility (`src/llm_client.py`) so we can swap models easily

---

## File Structure

```
hackathon-1/
├── PLAN.md                  ← you are here
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── src/
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── fetcher.py       ← download docs
│   │   └── loader.py        ← read docs into text
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── schema.py        ← data models
│   │   ├── strategy_extractor.py
│   │   └── action_extractor.py
│   ├── analyzer/
│   │   ├── __init__.py
│   │   ├── drift_scorer.py
│   │   ├── drift_detector.py
│   │   └── report_generator.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py          ← FastAPI app
│   │   └── pipeline.py      ← orchestrator
│   ├── ui/
│   │   └── app.py           ← Streamlit dashboard
│   └── llm_client.py        ← shared LLM wrapper
├── prompts/
│   ├── extract_pillars.md
│   ├── extract_actions.md
│   ├── analyze_drift.md
│   └── score_alignment.md
├── data/
│   ├── raw/                 ← original documents
│   └── processed/           ← structured JSON output
└── tests/
    ├── test_parser.py
    └── test_analyzer.py
```

---

## Timeline (Assuming ~6-8 hour hackathon)

| Hour | Milestone |
|------|-----------|
| 0-1 | Everyone reads plan, sets up env, Person 1 starts gathering data, others scaffold their modules |
| 1-2 | Person 1 has raw docs, Person 2 starts extracting, Person 3 builds with mock data, Person 4 scaffolds API, Person 5 mocks UI |
| 2-4 | Core extraction and analysis working end-to-end with at least 1 document |
| 4-5 | Integration — connect pipeline, API serves real results |
| 5-6 | UI shows real data, bug fixes, edge cases |
| 6-7 | Demo polish, README, walkthrough prep |
| 7-8 | Buffer / demo practice |

---

## Definition of Done (Demo-Ready)

1. Feed in a real company's investor deck + 2 earnings transcripts
2. System extracts strategic pillars automatically
3. System maps actions/spending to pillars
4. System produces a drift report with scores, flags, and evidence
5. Report is viewable in a simple UI
6. Whole pipeline runs with one command
