# Stage 2 — Strategic Pillar Synthesis and Priority Mapping

## Objective

Synthesize the individual strategy elements extracted in Stage 1A (and relevant commitments from Stage 1C) into a coherent map of Block, Inc.'s strategic pillars. Each pillar represents a distinct area of strategic emphasis, ranked by observed priority and tracked for temporal evolution. This pillar map serves as the reference structure against which all actions and commitments are evaluated in subsequent stages.

## Inputs

- Strategy elements: `data/processed/stage_1a_strategy.json` (STR-* elements)
- Commitments: `data/processed/stage_1c_commitments.json` (CMT-* elements, used to corroborate pillar identification)
- Source catalog: `data/processed/stage_0_sources.md`
- This prompt template

## Method

### Step 1: Element Clustering

Group all STR-* elements into candidate pillar clusters using the following approach:

1. **Semantic clustering:** Group elements that reference the same strategic area, product line, or organizational priority.
2. **Name extraction:** Where management has explicitly named pillars or priorities, adopt their terminology as the pillar name.
3. **Implicit pillar detection:** If a cluster of elements points to a consistent strategic area that management has not explicitly named, create a pillar and note it as "analyst-inferred" rather than "company-stated."
4. **Deduplication:** Multiple elements from different sources describing the same pillar should be consolidated under one pillar entry, with all supporting elements listed.

**Expected pillar areas for Block, Inc.** (validate against evidence; do not force-fit):
- Bitcoin / decentralized financial infrastructure (including TBD, Spiral, mining)
- Cash App ecosystem growth (direct deposit, lending, investing, commerce)
- Square / Seller ecosystem (payments, software, banking for businesses)
- Operational efficiency / cost discipline (Rule of 40, margin expansion, headcount discipline)
- TIDAL / music and creator economy (may be minor or deprecated)

These expectations should not constrain the analysis. If evidence reveals different or additional pillars, follow the evidence.

### Step 2: Priority Ranking

Rank pillars by observed strategic priority using the following weighted signals:

| Signal | Weight | Measurement |
|--------|--------|-------------|
| **Order of mention** | 20% | Position in shareholder letters, earnings scripts, and investor presentations (earlier = higher priority) |
| **C-level airtime** | 25% | Proportion of CEO/CFO commentary devoted to this pillar across all strategy sources |
| **Attached quantitative targets** | 20% | Number and specificity of quantitative goals tied to this pillar |
| **Resource allocation signals** | 25% | Stated investment commitments, capex direction, hiring priorities |
| **Commitment density** | 10% | Number of CMT-* commitments associated with this pillar area |

For each pillar, document the specific evidence supporting its priority rank.

### Step 3: Temporal Evolution Tracking

For each pillar, assess how its emphasis has changed over the analysis period:

| Trend | Definition |
|-------|------------|
| `stable` | Consistent emphasis across all time periods analyzed |
| `rising` | Increasing emphasis — more mentions, new targets, increased resource signals over time |
| `declining` | Decreasing emphasis — fewer mentions, dropped targets, reduced resource signals |
| `new` | Pillar appears in recent sources but not earlier ones |
| `deprecated` | Pillar appeared in earlier sources but is absent from recent ones |

Temporal tracking requires comparing elements across at least two time periods (e.g., consecutive annual letters, sequential quarterly calls).

### Step 4: Confidence and Limitations

For each pillar, assign a confidence score (0.0–1.0) reflecting:
- How explicitly the pillar is named by management (explicit > inferred)
- How many independent sources support the pillar
- How consistent the evidence is across sources
- Whether the sources are diverse in bias category

## Output Format

Produce a JSON file (`data/processed/stage_2_pillars.json`) with the following schema:

```json
{
  "metadata": {
    "stage": "2",
    "company": "Block, Inc.",
    "synthesis_date": "YYYY-MM-DD",
    "inputs": ["stage_1a_strategy.json", "stage_1c_commitments.json"],
    "methodology": "Semantic clustering of STR-* elements with priority ranking per prompts/02_map_pillars.md",
    "limitations": "..."
  },
  "pillars": [
    {
      "id": "PIL-001",
      "name": "Short descriptive name (e.g., 'Bitcoin and Decentralized Finance')",
      "description": "2-3 sentence description of what this pillar encompasses, in analytical language",
      "origin": "company-stated | analyst-inferred",
      "priority_rank": 1,
      "priority_evidence": {
        "order_of_mention": "Description of where this pillar appears in key documents",
        "c_level_airtime": "Estimate of proportion of leadership commentary on this topic",
        "quantitative_targets": ["List of specific targets associated with this pillar"],
        "resource_signals": ["List of resource allocation statements supporting this pillar"],
        "commitment_density": "Number and nature of commitments tied to this area"
      },
      "supporting_elements": ["STR-001", "STR-004", "STR-008", "CMT-003"],
      "temporal_trend": "stable | rising | declining | new | deprecated",
      "temporal_evidence": "Description of how emphasis has changed across the analysis period",
      "quantitative_targets": [
        {
          "metric": "e.g., 'Gross profit growth'",
          "target": "e.g., '>=25% YoY'",
          "timeline": "e.g., 'FY2025'",
          "source_id": "S-001"
        }
      ],
      "confidence": 0.90,
      "bias_note": "Note on potential bias in pillar identification (e.g., 'Pillar heavily supported by company-produced sources; limited external validation')"
    }
  ],
  "unmapped_elements": [
    {
      "element_id": "STR-012",
      "reason": "Does not clearly belong to any identified pillar; may represent emerging strategic interest"
    }
  ]
}
```

### ID Convention

- Pillar IDs use the prefix `PIL-` followed by a three-digit sequential number: `PIL-001`, `PIL-002`, etc.
- Pillars are numbered in priority rank order (PIL-001 is the highest-priority pillar).

### Quality Criteria

- Each pillar must be supported by at least 2 independent STR-* elements
- No element should be force-fit into a pillar where the connection is tenuous; use `unmapped_elements` for orphans
- Priority ranking must be justified with specific evidence, not intuition
- Temporal trends must reference specific dated sources

## Limitations

- Pillar synthesis involves analytical judgment — two analysts examining the same elements might produce slightly different pillar structures. Transparency about clustering decisions mitigates this.
- Priority ranking signals are weighted heuristically; the weights reflect analytical convention but are not empirically validated.
- Temporal evolution is constrained by the time span of available sources. If sources cover only 12 months, long-term trend assessment is inherently limited.
- Company-stated pillar names may mask internal complexity (e.g., "Cash App" encompasses lending, payments, investing, and social features with potentially different strategic weights).

## Bias Awareness

1. **Management narrative dominance:** Pillar identification is primarily driven by management's own framing. There is a risk of adopting the company's self-serving narrative structure. Mitigate by cross-referencing with resource allocation data and external analyst perspectives.
2. **Anchoring to expectations:** The "expected pillar areas" listed in Step 1 risk anchoring the analysis. If evidence does not support a listed area as a pillar, do not force it. Conversely, if evidence reveals an unlisted pillar, include it.
3. **Recency weighting in priority ranking:** More recent sources may disproportionately influence priority ranking. When possible, distinguish between stable long-term priorities and recent emphasis shifts.
4. **Missing pillars problem:** If management deliberately avoids naming a strategic area (e.g., a struggling segment they hope to quietly de-emphasize), it may not appear as a pillar despite significant resource allocation. Stage 3 (action mapping) will surface these as "unaligned actions," providing a check on this gap.
5. **Confidence score subjectivity:** Confidence assessments involve judgment. Document the reasoning for each score to enable reviewers to calibrate.
