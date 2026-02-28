# Stage 5 — Comprehensive Strategy Drift Report

## Objective

Generate a comprehensive, publication-quality analytical report synthesizing all outputs from Stages 0–4 into a coherent assessment of strategic coherence for Block, Inc. The report must be written in formal academic prose, with every factual claim traceable to a specific source identifier (S-*, STR-*, ACT-*, CMT-*, PIL-*). The report is the primary deliverable of the Strategy Drift Detector.

## Inputs

- Source catalog: `data/processed/stage_0_sources.md`
- Strategy elements: `data/processed/stage_1a_strategy.json`
- Action evidence: `data/processed/stage_1b_actions.json`
- Commitments: `data/processed/stage_1c_commitments.json`
- Pillar map: `data/processed/stage_2_pillars.json`
- Action mapping: `data/processed/stage_3_actions.json`
- Coherence analysis: `data/processed/stage_4_coherence.json`
- This prompt template

## Method

### Report Structure

The report must contain the following seven sections in order. Do not add, remove, or reorder sections.

---

### Section 1: Executive Summary (300 words maximum)

**Content requirements:**
- Headline finding: one sentence characterizing overall strategic coherence
- Overall coherence classification and composite score
- Top 3 drift flags (most significant misalignments between strategy and execution), each in one sentence
- Confidence level in the overall assessment (High / Medium / Low)
- One sentence on the primary limitation of the analysis

**Style:** Dense, precise, no filler. Every sentence must convey substantive information. A reader who reads only this section should understand the core finding.

---

### Section 2: Methodology

**Content requirements:**
- Framework description: six-stage pipeline from source identification through coherence analysis
- Source summary table: reproduce the source catalog in condensed form with bias classifications
- Analytical approach: describe the five-dimension coherence scoring system, including weights and classification thresholds
- Source sufficiency assessment: summarize the sufficiency verdict from Stage 0
- Scoring methodology: explain the 1–5 scale, composite calculation, and classification bands

**Limitations subsection (mandatory):**
- Public information constraint: analysis uses only publicly available data
- Single-analyst constraint: no inter-rater reliability check
- Temporal constraint: analysis reflects a snapshot; strategic postures evolve
- Source bias distribution: note the actual bias category percentages and their implications
- Quantification of qualitative data: acknowledge that scoring involves subjective judgment

---

### Section 3: Strategic Pillar Mapping

**Content requirements:**
- Present each identified pillar (PIL-*) with:
  - Name and description
  - Priority rank and evidence supporting the ranking
  - Temporal trend (stable / rising / declining / new / deprecated)
  - Key supporting strategy elements (STR-*) with verbatim or closely paraphrased quotes
  - Associated quantitative targets

- Include a priority ranking table:

```markdown
| Rank | Pillar | Origin | Trend | Confidence |
|------|--------|--------|-------|------------|
| 1 | PIL-001: [Name] | company-stated | stable | 0.90 |
```

- Discuss any unmapped strategy elements and their implications

**Citations:** Every pillar description must cite at least 2 STR-* elements. Every priority claim must cite specific evidence.

---

### Section 4: Execution Evidence

**Content requirements:**
- Organize evidence by pillar, presenting:
  - Key actions (ACT-*) mapped to each pillar, grouped by type (capital allocation, organizational, product, etc.)
  - Magnitude and significance of each action
  - Commitment fulfillment status for commitments (CMT-*) mapped to each pillar

- Highlight unaligned actions and their potential significance
- Present commitment fulfillment summary table:

```markdown
| Pillar | Total CMTs | Fulfilled | In Progress | Contradicted | Silently Abandoned |
|--------|-----------|-----------|-------------|--------------|-------------------|
| PIL-001 | N | N | N | N | N |
```

- Present resource allocation estimate table:

```markdown
| Pillar | Estimated Allocation % | Basis |
|--------|----------------------|-------|
| PIL-001 | X% | [evidence summary] |
```

**Citations:** Every action and commitment reference must include its ID (ACT-*, CMT-*) and source ID (S-*).

---

### Section 5: Coherence Analysis

**Content requirements:**
- Per-pillar coherence assessment presenting:
  - Five-dimension scores with brief evidence for each
  - Composite score and classification
  - Primary drift indicators

- Coherence summary table:

```markdown
| Pillar | Resource (30%) | Action (25%) | Commitment (20%) | Temporal (15%) | Contradiction (10%) | Composite | Classification |
|--------|---------------|-------------|------------------|---------------|--------------------| ----------|---------------|
| PIL-001 | 4 | 3 | 4 | 5 | 4 | 3.95 | Minor Drift |
```

- Shadow strategies section:
  - Each shadow strategy identified in Stage 4 with supporting evidence
  - Assessment of significance and interpretation

- Cross-pillar analysis:
  - Priority-execution gap analysis
  - Systemic commitment patterns
  - Bias correlation analysis

---

### Section 6: Key Findings and Drift Flags

**Content requirements:**

Present findings in a structured format. Each finding must include:

| Field | Description |
|-------|-------------|
| **Observation** | What was found (factual statement) |
| **Evidence** | Specific element IDs supporting the observation (STR-*, ACT-*, CMT-*) |
| **Classification** | Aligned / Minor Drift / Significant Drift / Strategic Disconnect |
| **Implication** | What this finding means for the company's strategic trajectory |
| **Confidence** | High / Medium / Low — based on evidence quality and diversity |
| **Bias Consideration** | How source bias may affect this finding |

Organize findings by severity (most significant first). Include both drift findings (misalignment) and alignment findings (areas of strong coherence) for a balanced assessment.

---

### Section 7: Conclusions

**Content requirements:**
- Overall coherence assessment: 2-3 paragraphs synthesizing the analysis into a holistic evaluation
- Strongest alignment: which pillar and why
- Greatest concern: which pillar and why
- Shadow strategy significance: assessment of whether unstated priorities represent meaningful strategic divergence
- Analytical confidence: overall confidence in the assessment, acknowledging key limitations
- Recommendations for further analysis: specific areas where additional evidence or deeper investigation would improve the assessment

**Style:** Measured, balanced, avoiding both false certainty and excessive hedging. Conclusions should be proportional to the evidence.

---

## Output Format

Produce a markdown file (`data/processed/final_report.md`) structured with the seven sections above, using proper markdown heading levels:

```markdown
# Strategy Drift Analysis: Block, Inc.
## Executive Summary
...
## Methodology
...
## Strategic Pillar Mapping
...
## Execution Evidence
...
## Coherence Analysis
...
## Key Findings and Drift Flags
...
## Conclusions
...
```

### Formatting Requirements

- Use markdown tables for structured data presentations
- Use blockquotes (`>`) for verbatim quotes from source documents
- Cite source IDs inline: "Block allocated $X to Bitcoin mining (ACT-007, S-003)"
- Use **bold** for key terms and findings on first reference
- Use section cross-references where relevant: "as discussed in Section 3"
- No bullet-point lists in analytical sections — use full paragraphs with academic prose
- Tables and structured summaries are appropriate for data presentation sections

### Length Guidelines

- Executive Summary: 300 words maximum (hard limit)
- Methodology: 400–600 words
- Strategic Pillar Mapping: 500–800 words
- Execution Evidence: 600–1000 words
- Coherence Analysis: 600–1000 words
- Key Findings: 400–700 words
- Conclusions: 300–500 words

Total report: approximately 3,000–5,000 words

## Limitations

- The report synthesizes upstream analyses; any errors or gaps in Stages 0–4 propagate to the final report. The methodology section must honestly characterize these inherited limitations.
- Academic prose style does not imply academic rigor in data collection — the analysis uses publicly available documents, not primary research data.
- The report is a point-in-time assessment. Strategic positions evolve, and the report's conclusions may become outdated as new information emerges.

## Bias Awareness

1. **Narrative coherence bias:** The act of writing a report creates pressure to construct a coherent narrative, which may smooth over genuine ambiguity in the evidence. Resist the temptation to resolve ambiguity artificially — flag it explicitly instead.
2. **Anchoring to coherence scores:** Quantitative scores create an anchor that subsequent prose may rationalize rather than challenge. Write analytical sections before reviewing composite scores, then reconcile.
3. **Balance imperative:** The report must present both alignment findings and drift findings. An exclusively negative or exclusively positive report is likely biased. If the evidence is genuinely one-sided, note this explicitly and consider whether the source mix may be creating the imbalance.
4. **Inherited bias amplification:** Biases in upstream stages (source selection, element extraction, action mapping) compound in the final report. The methodology section must transparently disclose the bias distribution of underlying sources.
5. **Audience awareness:** This report may be read by investors, analysts, journalists, or company representatives. Write for accuracy and fairness, not for any particular audience's preferences. Avoid language that could be construed as investment advice.
