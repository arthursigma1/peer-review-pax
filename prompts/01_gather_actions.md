# Stage 1B — Action and Execution Evidence Extraction

## Objective

Extract structured evidence of Block, Inc.'s concrete actions, operational decisions, and resource deployments from public sources. Unlike Stage 1A (which captures *stated intent*), this stage captures *revealed preferences* — what the company actually does with its capital, organizational structure, and product portfolio. The output feeds into Stage 3 (Action-to-Pillar Mapping).

## Inputs

- Source catalog from Stage 0 (`data/processed/stage_0_sources.md`), filtered to `type: action`
- Raw document text stored in `data/raw/block_actions_{source_id}.txt`
- This prompt template

## Method

### Step 1: Document Retrieval

For each source in the Stage 0 catalog with `type: action`:
1. Retrieve the full text of the document via web fetch or SEC EDGAR
2. Save the raw text to `data/raw/block_actions_{source_id}.txt`
3. Note any retrieval failures or partial content in the output

### Step 2: Evidence Extraction

Read each document carefully and extract evidence falling into the following categories:

**A. Capital Allocation**
- Acquisitions, divestitures, and strategic investments (amounts, targets, stated rationale)
- Capital expenditure disclosures (total capex, segment-level if available)
- Stock-based compensation patterns by segment (indicates talent investment priorities)
- Share repurchase programs (signals excess capital vs. reinvestment preference)
- Look for: 10-Q cash flow statements, M&A announcements, capex line items

**B. Organizational Decisions**
- Restructurings, layoffs, and headcount changes (scope, affected segments, stated rationale)
- Leadership appointments and departures (particularly C-suite and segment heads)
- Organizational structure changes (new divisions, merged units, reporting line changes)
- Look for: 8-K filings, press releases, earnings call commentary on org changes

**C. Product / Service Launches**
- New products, features, or service expansions
- Geographic market entries or exits
- Partnership announcements with strategic implications
- Look for: press releases, product announcements, 10-Q business updates

**D. Discontinued Initiatives**
- Products or services shut down, wound down, or deprioritized
- Exited markets or abandoned partnerships
- Write-downs or impairments signaling strategic retreat
- Look for: 10-Q impairment charges, press releases, earnings call Q&A admissions

**E. Segment Financial Results**
- Revenue, gross profit, and operating metrics by business segment
- Segment growth rates and margin trends (quarter-over-quarter and year-over-year)
- Inter-segment dynamics (e.g., Bitcoin revenue vs. Cash App subscription revenue)
- Look for: 10-Q segment reporting, earnings supplements, investor presentations

### Step 3: Source Hierarchy

When the same action is reported by multiple sources, prefer sources in this order:

1. **Regulatory filings** (10-K, 10-Q, 8-K) — legally mandated, highest reliability
2. **Earnings call transcripts** — management commentary with analyst scrutiny
3. **Press releases** — company-controlled messaging, moderate reliability
4. **Third-party reporting** — useful for context but may contain interpretation

Record the highest-reliability source as the primary `source_id`. Note corroborating sources in the `notes` field.

### Step 4: Magnitude Assessment

For each action, estimate its strategic magnitude:

| Magnitude | Criteria |
|-----------|----------|
| `high` | >$100M financial impact, affects >20% of workforce, or represents entry/exit from a major business line |
| `medium` | $10M–$100M impact, significant product launch, or material leadership change |
| `low` | <$10M impact, incremental feature, or minor organizational adjustment |

### Step 5: Confidence Assessment

Assign a confidence score (0.0–1.0) to each action based on:

| Factor | Higher Confidence | Lower Confidence |
|--------|-------------------|------------------|
| Source type | SEC filing with specific figures | Press release with vague language |
| Quantification | Dollar amounts, headcount, dates | "Significant investment", "meaningful" |
| Corroboration | Multiple sources confirm | Single source |
| Recency | Current quarter | >12 months old |

## Output Format

Produce a JSON file (`data/processed/stage_1b_actions.json`) with the following schema:

```json
{
  "metadata": {
    "stage": "1B",
    "company": "Block, Inc.",
    "extraction_date": "YYYY-MM-DD",
    "sources_analyzed": ["S-002", "S-004", "..."],
    "methodology": "Manual extraction from action-type sources per prompts/01_gather_actions.md",
    "source_hierarchy": "Regulatory filings > Earnings transcripts > Press releases > Third-party",
    "limitations": "..."
  },
  "actions": [
    {
      "id": "ACT-001",
      "type": "capital_allocation | organizational_decision | product_launch | discontinued_initiative | segment_financial_result",
      "description": "Concise factual description of the action or evidence",
      "magnitude": "high | medium | low",
      "date": "YYYY-MM-DD or YYYY-QN for quarterly data",
      "source_id": "S-002",
      "source_bias": "company-produced | regulatory-filing | third-party-analyst | journalist",
      "implied_strategic_area": "Brief note on which strategic area this action likely relates to (e.g., 'Bitcoin', 'Cash App growth', 'cost discipline')",
      "confidence": 0.90,
      "notes": "Corroborating sources, contextual detail, or caveats"
    }
  ]
}
```

### ID Convention

- Action elements use the prefix `ACT-` followed by a three-digit sequential number: `ACT-001`, `ACT-002`, etc.
- Numbering is sequential across all sources (not per-source).

### Minimum Extraction Targets

- At least 3 capital allocation data points
- At least 2 organizational decisions (if available)
- At least 2 product/service launches or discontinuations
- At least 2 quarters of segment financial results

If any category yields zero elements, explicitly note this gap in the metadata limitations field.

## Limitations

- Actions observable through public sources represent only a fraction of operational activity. Internal resource allocation decisions that do not rise to the level of disclosure may be invisible.
- Financial data from 10-Q filings is aggregated at the segment level; intra-segment allocation (e.g., how much of Cash App's investment goes to lending vs. direct deposit) is generally not disclosed.
- Press release language is crafted for positive reception and may overstate the significance of routine product updates.
- Timing gaps: there is typically a 30–45 day lag between quarter-end and 10-Q filing; actions in the current quarter may not yet be documented.

## Bias Awareness

1. **Survivorship bias in press releases:** Companies announce launches but rarely announce quiet shutdowns. Actively search for *absence* of previously mentioned initiatives, discontinued products, and write-downs to counterbalance.
2. **Magnitude inflation:** Company-produced sources (press releases, earnings scripts) tend to frame actions in the most favorable magnitude. Cross-reference with financial data in 10-Q filings for grounded magnitude assessment.
3. **Narrative framing in earnings calls:** Prepared remarks are scripted to present a cohesive narrative. The Q&A section, where analysts press on specifics, often reveals more candid information. Weight Q&A-sourced evidence accordingly.
4. **Regulatory filings as ground truth:** SEC filings carry legal liability and auditor review. When press releases and filings conflict, the filing should be treated as authoritative.
5. **Third-party interpretation risk:** Journalist and analyst accounts of company actions may include interpretive framing. Extract the factual action and note any interpretive overlay separately.
