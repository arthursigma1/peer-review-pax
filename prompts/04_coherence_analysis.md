# Stage 4 — Multi-Dimensional Coherence Analysis

## Objective

Score the coherence between Block, Inc.'s stated strategic pillars and its observable actions and commitments across five weighted dimensions. Produce a quantitative assessment of strategic alignment for each pillar, identify patterns of drift, and surface any shadow strategies — areas receiving significant resources that are not reflected in the company's stated strategic framework.

## Inputs

- Pillar map: `data/processed/stage_2_pillars.json` (PIL-* definitions with priority rankings)
- Action mapping: `data/processed/stage_3_actions.json` (action/commitment-to-pillar mappings, resource allocation estimates, commitment tracker)
- Strategy elements: `data/processed/stage_1a_strategy.json` (STR-* for reference)
- Actions: `data/processed/stage_1b_actions.json` (ACT-* for reference)
- Commitments: `data/processed/stage_1c_commitments.json` (CMT-* for reference)
- Source catalog: `data/processed/stage_0_sources.md`
- This prompt template

## Method

### Step 1: Per-Pillar Scoring Across Five Dimensions

For each pillar (PIL-*), score on a 1–5 scale across five dimensions:

#### Dimension 1: Resource Alignment (Weight: 30%)

*Does capital and organizational resource allocation match the pillar's stated priority?*

| Score | Criteria |
|-------|----------|
| 5 | Resource allocation clearly proportional to or exceeding stated priority rank. High-magnitude capital actions directly support this pillar. |
| 4 | Resource allocation generally consistent with priority. Minor gaps between rhetoric and spending. |
| 3 | Moderate mismatch — pillar is stated as high priority but receives mid-tier resources, or vice versa. |
| 2 | Significant mismatch — stated as a top priority but receiving minimal observable resources, or receiving heavy resources despite low stated priority. |
| 1 | No observable resource allocation to a stated pillar, or massive resources to an unstated area. |

**Evidence required:** Reference specific ACT-* capital allocation items, resource allocation percentages from Stage 3, and priority rank from Stage 2.

#### Dimension 2: Action Consistency (Weight: 25%)

*Do concrete operational actions advance this pillar?*

| Score | Criteria |
|-------|----------|
| 5 | Multiple high-magnitude actions directly advance this pillar. Product launches, organizational decisions, and investments all point in the same direction. |
| 4 | Majority of pillar-related actions are supportive. Minor inconsistencies present but explainable. |
| 3 | Mixed signals — some actions support the pillar, others are neutral or tangential. |
| 2 | Few actions support the pillar. Actions in this area are low-magnitude or infrequent. |
| 1 | Actions actively undermine or contradict the pillar (e.g., shutting down pillar-related products, divesting from the area). |

**Evidence required:** Reference specific ACT-* items mapped to this pillar, their magnitudes, and any contradicting actions.

#### Dimension 3: Commitment Fulfillment (Weight: 20%)

*Are promises related to this pillar being kept?*

| Score | Criteria |
|-------|----------|
| 5 | All or nearly all commitments related to this pillar are fulfilled or on track. No contradictions. |
| 4 | Most commitments fulfilled or in progress. Minor shortfalls present. |
| 3 | Mixed fulfillment — some commitments met, others silently abandoned or partially fulfilled. |
| 2 | Majority of commitments unmet. Evidence of silent abandonment or significant downgrade. |
| 1 | Commitments actively contradicted. Guidance repeatedly missed. Major promises broken. |

**Evidence required:** Reference commitment tracker data from Stage 3 (per-pillar fulfillment rates) and specific CMT-* items.

#### Dimension 4: Temporal Consistency (Weight: 15%)

*Is emphasis on this pillar stable over time?*

| Score | Criteria |
|-------|----------|
| 5 | Consistently emphasized across all time periods. Priority rank stable. Quantitative targets maintained or increased. |
| 4 | Generally stable. Minor fluctuations in emphasis but no directional change. |
| 3 | Noticeable change in emphasis — rising or declining in a way that warrants monitoring but is not yet alarming. |
| 2 | Significant change — pillar was prominently featured in earlier period but notably de-emphasized recently (or vice versa). |
| 1 | Pillar appears to have been abandoned — present in earlier strategy documents but absent from recent ones, or newly introduced with no historical precedent. |

**Evidence required:** Reference temporal_trend from Stage 2 pillars and compare element dates from Stage 1A.

#### Dimension 5: Absence of Contradiction (Weight: 10%)

*Are there actions or statements that directly undermine this pillar?*

| Score | Criteria |
|-------|----------|
| 5 | No contradicting actions or statements identified. All evidence is directionally consistent. |
| 4 | One minor contradicting signal, but it has a plausible explanation (e.g., short-term tactical retreat for long-term strategic gain). |
| 3 | Multiple contradicting signals that collectively raise questions about commitment to this pillar. |
| 2 | Significant contradictions — major actions or decisions that directly undermine the pillar's objectives. |
| 1 | Fundamental contradiction — the company's actions are diametrically opposed to the stated pillar. |

**Evidence required:** Reference specific ACT-* or CMT-* items that contradict the pillar, with explanation of the nature of contradiction.

### Step 2: Weighted Composite Score

Calculate the weighted composite coherence score for each pillar:

```
Composite = (Resource Alignment * 0.30) + (Action Consistency * 0.25) +
            (Commitment Fulfillment * 0.20) + (Temporal Consistency * 0.15) +
            (Absence of Contradiction * 0.10)
```

### Step 3: Drift Classification

Classify each pillar based on its composite score:

| Classification | Score Range | Interpretation |
|----------------|-------------|----------------|
| **Aligned** | >= 4.0 | Strategy and execution are coherent. The company is doing what it says. |
| **Minor Drift** | 3.0 – 3.9 | Broadly aligned but with notable gaps. Warrants monitoring. |
| **Significant Drift** | 2.0 – 2.9 | Material disconnect between stated strategy and execution. Requires investigation. |
| **Strategic Disconnect** | < 2.0 | Strategy and execution are fundamentally misaligned. The stated pillar may be performative or abandoned. |

### Step 4: Shadow Strategy Identification

A shadow strategy is a significant area of resource allocation that is **not** reflected as a named strategic pillar. Identify shadow strategies by:

1. Reviewing "unaligned actions" from Stage 3 — do they cluster into a coherent theme?
2. Reviewing resource allocation summary — is there a significant allocation percentage to the "unaligned" category?
3. Reviewing actions classified as "ambiguous" — do they suggest an unstated priority area?

For each candidate shadow strategy:
- Name it descriptively
- List the supporting actions (ACT-*)
- Estimate its resource allocation relative to stated pillars
- Assess whether it is a legacy commitment, an emerging priority, or a deliberate omission from the stated framework
- Evaluate its significance — does it represent genuine strategic drift or simply operational noise?

### Step 5: Cross-Pillar Analysis

Beyond per-pillar scoring, assess systemic patterns:

1. **Priority-execution gap:** Is the highest-priority pillar also the highest-scoring on coherence? If lower-priority pillars score higher, this suggests the stated priority ranking does not reflect actual execution priorities.
2. **Commitment follow-through pattern:** Is there a systemic tendency toward certain commitment outcomes (e.g., consistently making bold commitments but achieving modest results)?
3. **Bias pattern:** Are coherence scores correlated with source bias — e.g., do pillars supported primarily by company-produced sources score artificially higher?

## Output Format

Produce a JSON file (`data/processed/stage_4_coherence.json`) with the following schema:

```json
{
  "metadata": {
    "stage": "4",
    "company": "Block, Inc.",
    "analysis_date": "YYYY-MM-DD",
    "inputs": ["stage_2_pillars.json", "stage_3_actions.json", "stage_1a_strategy.json", "stage_1b_actions.json", "stage_1c_commitments.json"],
    "methodology": "Five-dimension weighted coherence scoring per prompts/04_coherence_analysis.md",
    "scoring_weights": {
      "resource_alignment": 0.30,
      "action_consistency": 0.25,
      "commitment_fulfillment": 0.20,
      "temporal_consistency": 0.15,
      "absence_of_contradiction": 0.10
    },
    "limitations": "..."
  },
  "pillar_coherence": [
    {
      "pillar_id": "PIL-001",
      "pillar_name": "...",
      "priority_rank": 1,
      "dimensions": {
        "resource_alignment": {
          "score": 4,
          "evidence": "Specific evidence supporting this score, referencing ACT-* and allocation data",
          "key_observations": "..."
        },
        "action_consistency": {
          "score": 3,
          "evidence": "...",
          "key_observations": "..."
        },
        "commitment_fulfillment": {
          "score": 4,
          "evidence": "...",
          "key_observations": "..."
        },
        "temporal_consistency": {
          "score": 5,
          "evidence": "...",
          "key_observations": "..."
        },
        "absence_of_contradiction": {
          "score": 4,
          "evidence": "...",
          "key_observations": "..."
        }
      },
      "composite_score": 3.95,
      "classification": "Minor Drift",
      "summary": "2-3 sentence analytical summary of coherence findings for this pillar",
      "primary_drift_indicators": ["List of specific indicators that lower the coherence score"],
      "bias_consideration": "Note on how source bias may affect this pillar's scoring"
    }
  ],
  "shadow_strategies": [
    {
      "name": "Descriptive name for the shadow strategy",
      "description": "2-3 sentence description of this unstated strategic area",
      "supporting_actions": ["ACT-015", "ACT-022", "ACT-031"],
      "estimated_resource_allocation_pct": 10,
      "interpretation": "legacy_commitment | emerging_priority | deliberate_omission | operational_noise",
      "significance": "high | medium | low",
      "analysis": "Detailed assessment of what this shadow strategy reveals about actual vs. stated priorities"
    }
  ],
  "overall_assessment": {
    "average_coherence_score": 3.5,
    "overall_classification": "Minor Drift",
    "priority_execution_gap": "Analysis of whether execution priorities match stated priorities",
    "commitment_pattern": "Systemic observation about commitment follow-through",
    "bias_pattern": "Observation about whether source bias correlates with coherence scores",
    "highest_coherence_pillar": { "pillar_id": "PIL-003", "score": 4.2 },
    "lowest_coherence_pillar": { "pillar_id": "PIL-001", "score": 2.8 },
    "top_drift_flags": [
      {
        "flag": "Concise description of the drift indicator",
        "severity": "high | medium | low",
        "evidence_summary": "Brief evidence summary with element IDs",
        "confidence": 0.85
      }
    ]
  }
}
```

## Limitations

- Coherence scoring involves quantifying qualitative assessments, which introduces subjectivity. Two analysts may assign different scores to the same evidence. The detailed evidence documentation in each dimension is intended to make scoring transparent and reviewable.
- The 1–5 scale and dimension weights are analytical conventions, not empirically derived measures. They provide a structured framework for comparison but should not be treated as precise measurements.
- Shadow strategy identification relies on the completeness of action extraction. If significant actions were missed in Stage 1B, shadow strategies may go undetected.
- Coherence analysis at a point in time may not capture strategic inflection points where management has intentionally pivoted but not yet updated public communications.
- The analysis cannot assess the *quality* of strategic alignment — a company may be perfectly aligned to a flawed strategy.

## Bias Awareness

1. **Score inflation risk:** When evidence is ambiguous, there is a tendency to assign mid-range scores (3), which compresses the distribution and may mask genuine drift. Apply scores at the extremes when evidence warrants it.
2. **Company narrative coherence:** Management-produced sources are designed to present a coherent narrative. If coherence scores are high, consider whether this reflects genuine alignment or effective narrative management. Cross-reference with action data (which is harder to fabricate) to validate.
3. **Confirming the null hypothesis:** There may be an unconscious bias toward finding alignment (the "everything is fine" default). Actively look for contradictions and drift signals rather than waiting for them to emerge.
4. **Single-analyst limitation:** This analysis is performed by one analyst (the LLM). In a research setting, inter-rater reliability checks would be standard. Acknowledge this limitation explicitly in the output.
5. **Temporal bias in weighting:** The 15% weight on temporal consistency may underweight genuine strategic pivots that are appropriate responses to changing conditions. Note in the analysis when declining temporal consistency may reflect intentional, adaptive strategy change rather than drift.
