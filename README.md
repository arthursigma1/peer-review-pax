# Strategy Drift Detector

AI agent that evaluates whether a public company's actions align with its stated strategic priorities — flagging drift, contradictions, and silent priority shifts.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up your API key
cp .env.example .env
# Edit .env with your Anthropic API key

# 3. Run the analysis pipeline
python -m src.api.pipeline

# 4. Start the API
uvicorn src.api.main:app --reload

# 5. Launch the UI
streamlit run src/ui/app.py
```

## How It Works

1. **Ingest** — Fetch investor presentations, earnings transcripts, press releases
2. **Parse** — Extract strategic pillars, capital allocations, and public commitments into structured data
3. **Analyze** — LLM agent scores alignment and flags drift between stated strategy and actual actions
4. **Report** — Visual dashboard with drift scores, flagged items, and evidence

## Project Structure

See [PLAN.md](PLAN.md) for full architecture, team assignments, and build timeline.

## Team

Built at a hackathon by a team of 5 using Claude Code.
