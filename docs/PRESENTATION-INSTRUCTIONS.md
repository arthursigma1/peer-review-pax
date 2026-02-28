# Instructions for Creating the Presentation

## For Claude (Cowork or any AI assistant)

You are creating a presentation based on a Strategy Drift Analysis of Block, Inc.

### Primary Source

**The final report is at:**

```
data/processed/final_report.md
```

Read this file first — it contains the complete analysis (~3,800 words) with all findings, scores, and evidence.

### Supporting Data Files

For charts, tables, and detailed data, read these files:

| File | Use For |
|------|---------|
| `data/processed/stage_4_coherence.json` | Coherence scores per pillar (for heatmaps, bar charts) |
| `data/processed/stage_2_pillars.json` | Pillar definitions, rankings, temporal trends |
| `data/processed/stage_3_actions.json` | Resource allocation percentages, commitment fulfillment |
| `data/processed/stage_0_sources.md` | Source catalog with bias distribution |
| `docs/strategy-drift-methodology.md` | Methodology summary |

### Suggested Slide Structure (10-12 slides)

**Slide 1 — Title**
- "Strategy Drift Analysis: Block, Inc."
- Subtitle: "Evaluating Coherence Between Stated Strategy and Execution"
- Date: February 28, 2026

**Slide 2 — What Is Strategy Drift?**
- Brief definition: gap between what a company says and what it does
- Why it matters for investors, boards, and governance
- Our approach: structured, bias-aware, evidence-based

**Slide 3 — Methodology**
- 6-stage pipeline diagram (Source Mapping → Gathering → Pillars → Action Mapping → Coherence → Report)
- 50 sources analyzed across 6 bias categories
- Bias distribution pie chart (32% company-produced, 34% journalist, 14% analyst, etc.)
- Cross-cutting principles: bias qualification, methodological rigor, academic language, source sufficiency

**Slide 4 — Block's 6 Strategic Pillars**
- Table or visual showing the 6 pillars ranked by priority
- PIL-001: AI-Native Transformation (rank 1, NEW)
- PIL-002: Cash App (rank 2, RISING)
- PIL-003: Profitable Growth (rank 3, RISING)
- PIL-004: Square (rank 4, STABLE)
- PIL-005: Ecosystem Interconnection (rank 5, analyst-inferred)
- PIL-006: Bitcoin (rank 6, STABLE)

**Slide 5 — The Coherence Scorecard (HEADLINE SLIDE)**
- Heatmap or bar chart showing all 6 pillar scores
- Color-coded: green (Aligned >=4.0), yellow (Minor Drift 3.0-3.9), red (Significant Drift <3.0)
- Overall: Minor Drift (3.73)
- Visual emphasis on the inversion: #1 pillar scores 2.95, #3 pillar scores 4.85

**Slide 6 — Finding 1: The AI-Native Question**
- PIL-001 scored 2.95 (Significant Drift) despite being #1 priority
- Key tension: Is it genuine transformation or narrative framing for layoffs?
- Evidence: $450-500M restructuring, 40%+ workforce cut, zero fulfilled commitments
- External skepticism: Bloomberg, CNN, CNBC all frame as job cuts
- Counterpoint: "Goose" AI platform predates public announcement
- Verdict: needs 12 more months to prove itself

**Slide 7 — Finding 2: Profitability Is the Real Strategy**
- PIL-003 scored 4.85 (highest alignment)
- 15 commitments, 0 contradicted, 0 silently abandoned
- Conservative guidance → raise → beat pattern across 3 consecutive quarters
- Operating loss (-$279M) to $2.07B AOI in one year
- This is what Block actually executes best

**Slide 8 — Finding 3: The Hidden Lending Risk**
- Shadow strategy: Consumer Credit Scaling
- Cash App Borrow originations +223% YoY
- Lending loss expenses +89%
- Growing 3x faster than the business — not separately tracked as a strategic pillar
- Risk: if losses exceed sub-3% target persistently, impacts Cash App AND profitability

**Slide 9 — Finding 4: Bitcoin — Identity vs. Priority**
- PIL-006 scored 3.40 (Minor Drift)
- Block is literally named after blockchain, Dorsey is Bitcoin's most prominent CEO advocate
- Yet Bitcoin is rank 6, TBD/Web5 was shut down, no forward financial targets
- Resource allocation: 10% (vs 35% for Cash App)
- Interpretation: genuine but bounded commitment

**Slide 10 — Resource Allocation vs. Stated Priority**
- Side-by-side chart:
  - Left: Priority ranking (1=AI-Native, 2=Cash App, 3=Profitability...)
  - Right: Resource allocation (35% Cash App, 25% Profitability, 15% Square, 10% AI, 10% Bitcoin, 3% Ecosystem)
- Visual makes the inversion immediately obvious

**Slide 11 — Methodology Credibility**
- Agent team architecture (5 agents + lead, 4 waves)
- Quality gates between each wave
- Academic rigor: every claim cites sources, bias acknowledged per finding
- 50 sources, 22 strategy elements, 18 actions, 24 commitments analyzed
- QA review passed all 9 criteria

**Slide 12 — Conclusions & What to Watch**
- Block is a profitability and Cash App execution machine (strong alignment)
- The AI-native narrative is unproven — watch Q1-Q2 2026 for real evidence
- Consumer lending is the hidden risk no one is naming as a strategic pillar
- Bitcoin is genuine but bounded — not the existential bet it appears
- 2028 targets ($15.8B GP, $5.50 EPS) are likely conservative post-restructuring

### Design Guidelines

- Use a clean, professional design (dark background with white text works well for data)
- Emphasize the coherence heatmap as the visual centerpiece
- Use green/yellow/red color coding consistently for Aligned/Minor Drift/Significant Drift
- Include source citations on data slides (e.g., "Source: S-006, 10-K FY 2025")
- Keep text minimal on slides — the report has the detail, the presentation tells the story

### Tone

- Analytical, not sensational
- Present findings as structured assessments, not accusations
- Acknowledge limitations openly (builds credibility)
- Lead with the methodology to establish trust, then deliver the findings
