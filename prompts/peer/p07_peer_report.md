# Stage P5 — Peer Comparison Report

## Objective

Generate a comprehensive, publication-quality analytical report synthesizing all outputs from Stages P0–P4 into a coherent assessment of {COMPANY}'s ({TICKER}) competitive positioning within the alternative asset management industry. The report must be written in formal academic prose, with every factual claim traceable to a specific identifier (PS-*, PEER-*, MET-*, BENCH-*, RANK-*, PIL-*).

## Inputs

- Peer identification: `data/processed/{ticker}/peer_p0_identification.json`
- Metric definitions: `data/processed/{ticker}/peer_p0_metrics.json`
- Source catalog: `data/processed/{ticker}/peer_p0_sources.md`
- Raw data: `data/processed/{ticker}/peer_p1_data.json`
- Standardized data: `data/processed/{ticker}/peer_p2_standardized.json`
- Comparative analysis: `data/processed/{ticker}/peer_p3_comparison.json`
- Strategic contextualization: `data/processed/{ticker}/peer_p4_contextualization.json`
- Drift pipeline outputs (for integration): `data/processed/{ticker}/stage_2_pillars.json`, `data/processed/{ticker}/stage_4_coherence.json`

## Method

### Report Structure

The report must contain the following seven sections in order. Do not add, remove, or reorder sections.

---

### Section 1: Executive Summary (300 words maximum)

**Content requirements:**
- Headline finding: one sentence on {COMPANY}'s overall competitive positioning
- Overall positioning classification (Leader / Above Average / Below Average / Laggard)
- Top 3 competitive strengths and top 3 competitive gaps, each in one sentence
- Connection to strategy drift findings: one sentence on how internal alignment or drift translates to competitive position
- Confidence level (High / Medium / Low) and primary limitation of the analysis

**Style:** Dense, precise, no filler. Every sentence must convey substantive information. A reader who reads only this section should understand the core finding.

---

### Section 2: Methodology

**Content requirements:**
- Framework description: peer pipeline structure (P0–P5) and integration with the drift pipeline
- Source summary: number of sources per company and bias distribution across the full source catalog
- Analytical approach: peer selection criteria, metric definition, ranking methodology, percentile calculation
- Normalization approach: currency conversion method, fiscal year alignment, accounting standard treatment
- Integration with drift analysis: how PIL-* mapping connects competitive metrics to strategic pillars

**Limitations subsection (mandatory):**
- Data availability constraint: analysis uses only publicly available disclosures
- Small sample constraint: peer group of 5-7 firms limits statistical significance
- Definitional variance: metric definitions are not perfectly standardized across firms
- Point-in-time assessment: competitive positions evolve and rankings may shift quarterly
- Inherited drift pipeline limitations: biases from the drift pipeline propagate into the strategic contextualization section

---

### Section 3: Peer Group Profile

**Content requirements:**
- For each peer (PEER-NNN): full name, ticker, AUM, primary strategies, classification (scale / strategy / both), selection rationale, and key differences from {COMPANY}
- Peer group summary statistics: AUM range, geographic distribution, strategy distribution
- Discussion of any peers excluded after initial identification and the reasons for exclusion

**Citations:** Every peer description must reference its PEER-NNN identifier. AUM figures must cite the PS-* source from which they were drawn.

---

### Section 4: Industry Metrics Framework

**Content requirements:**
- Present the eight metric categories with definitions of each metric (MET-NNN)
- Coverage matrix: which metrics are available for which companies, using the notation from Stage P0c (Y / P / N)
- Discussion of data quality and comparability issues for metrics with coverage below the sufficient threshold

**Citations:** Every metric definition must reference its MET-NNN identifier.

---

### Section 5: Comparative Performance Analysis

**Content requirements:**
- Per-category analysis: for each of the eight metric categories, present {COMPANY}'s rankings, percentile positions, and overall category classification with supporting evidence
- Summary ranking table across all metrics with sufficient coverage:

```markdown
| Metric | MET-ID | {TICKER} Value | {TICKER} Rank | Peer Median | {TICKER} vs Median | Position |
|--------|--------|---------------|---------------|-------------|-------------------|----------|
| Total AUM | MET-001 | $X.Xb | 5 of 7 | $X.Xb | -X% | Below Average |
```

- Trend analysis: for each metric with multi-period data, whether {COMPANY} is converging toward or diverging from peer benchmarks
- Competitive strengths section: 3 metrics or categories where {COMPANY} leads or outperforms
- Competitive weaknesses section: 3 metrics or categories where {COMPANY} materially lags

**Citations:** Every ranking claim must reference its RANK-NNN identifier and the underlying BENCH-* data points.

---

### Section 6: Strategic Contextualization

**Content requirements:**
- Per-pillar competitive assessment: for each PIL-*, present the relevant metric rankings and the drift-competition pattern classification (validated execution / insufficient strategy / accidental success / compounding weakness) with supporting evidence
- Drift-competition correlation analysis: a systematic assessment of whether pillars classified as drifting in the drift pipeline correspond to areas of competitive weakness
- Alignment findings: pillars where internal coherence translates to demonstrated competitive strength
- Concern findings: pillars where drift correlates with competitive weakness, or where alignment does not produce competitive advantage
- Peer strategy comparison: for each major peer, a brief characterization of apparent strategic emphasis and any lessons it suggests for {COMPANY}

**Citations:** Every pillar assessment must reference its PIL-* identifier, its coherence score from `stage_4_coherence.json`, and the RANK-* entries informing the competitive position.

---

### Section 7: Conclusions

**Content requirements:**
- Overall competitive positioning assessment: 2-3 paragraphs synthesizing the analysis into a holistic evaluation
- Strongest competitive advantage: the pillar or metric area where {COMPANY} most clearly leads peers and why
- Greatest competitive vulnerability: the pillar or metric area of most significant concern and why
- Strategic implications: specific areas where the analysis suggests focus, investment, or strategic clarification is warranted — written as analytical observations, not investment advice
- Analytical confidence: overall confidence level, primary limitations, and how those limitations affect the reliability of the conclusions
- Recommendations for further analysis: specific evidence gaps or follow-up analyses that would materially improve the assessment

**Style:** Measured, balanced, avoiding both false certainty and excessive hedging. Conclusions must be proportional to the evidence and clearly distinguish well-supported findings from provisional interpretations.

---

## Output Format

Markdown file `data/processed/{ticker}/peer_report.md` structured with the seven sections above, using proper markdown heading levels:

```markdown
# Peer Comparison Analysis: {COMPANY} ({TICKER})
## Executive Summary
...
## Methodology
...
## Peer Group Profile
...
## Industry Metrics Framework
...
## Comparative Performance Analysis
...
## Strategic Contextualization
...
## Conclusions
...
```

### Formatting Requirements

- Markdown tables for all structured data presentations
- Blockquotes (`>`) for verbatim quotes from source documents
- Inline citations: "(PEER-001, MET-003, RANK-015)"
- **Bold** for key terms and classification labels on first reference
- Section cross-references where relevant: "as discussed in Section 5"
- No bullet-point lists in analytical sections — use full paragraphs with academic prose
- Tables and structured summaries are appropriate in data presentation sections

### Length Guidelines

- Executive Summary: 300 words maximum (hard limit)
- Methodology: 400-600 words
- Peer Group Profile: 400-600 words
- Industry Metrics Framework: 300-500 words
- Comparative Performance Analysis: 600-1000 words
- Strategic Contextualization: 500-800 words
- Conclusions: 300-500 words

Total: approximately 3,000-5,000 words

## Limitations

- The report synthesizes upstream analyses from both the peer pipeline (P0-P4) and the drift pipeline (Stages 2-4); errors or gaps in either propagate to the final report.
- Academic prose style does not imply primary research rigor — the analysis uses publicly available documents, not primary data.
- Point-in-time assessment: competitive positions evolve and the report's conclusions may become outdated as new filings, fundraising announcements, or market movements emerge.
- Small peer group (5-7 firms) limits the statistical significance of all ranking and percentile claims; the report must characterize this constraint honestly.
- Integration of two analytical pipelines inherits and compounds the limitations of both; the methodology section must transparently disclose this.

## Bias Awareness

1. **Narrative coherence bias**: synthesizing two pipelines creates strong pressure to construct a unified, coherent story; resist artificially resolving genuine ambiguity between drift findings and competitive position — flag it explicitly instead.
2. **Anchoring to rankings**: quantitative rankings create an anchor that subsequent prose may rationalize rather than critically evaluate; write analytical prose before reviewing composite rankings, then reconcile.
3. **Balance imperative**: the report must present both competitive strengths and weaknesses; a report that is exclusively negative or exclusively positive is likely biased, and the source mix or peer selection should be scrutinized if this occurs.
4. **Inherited bias amplification**: biases from peer selection (P0), metric prioritization (P0b), source mapping (P0c), and the drift pipeline's source selection and scoring all compound in this report; the methodology section must disclose the bias distribution of underlying sources.
5. **Audience awareness**: write for accuracy and fairness; avoid language that could be construed as investment advice, and do not tailor the tone to any particular stakeholder's preferences.
