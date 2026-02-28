# Stage 1A — Strategy Element Extraction

## Objective

Extract structured strategy elements from Block, Inc. public documents that articulate the company's strategic intent, priorities, and direction. Each extracted element must be traceable to a specific source, tagged for bias, and assessed for confidence. The output of this stage feeds directly into Stage 2 (Pillar Synthesis).

## Inputs

- Source catalog from Stage 0 (`data/processed/stage_0_sources.md`), filtered to `type: strategy`
- Raw document text stored in `data/raw/block_strategy_{source_id}.txt`
- This prompt template

## Method

### Step 1: Document Retrieval

For each source in the Stage 0 catalog with `type: strategy`:
1. Retrieve the full text of the document via web fetch or SEC EDGAR
2. Save the raw text to `data/raw/block_strategy_{source_id}.txt`
3. Note any retrieval failures or partial content in the output

### Step 2: Element Extraction

Read each document carefully and extract elements falling into the following categories:

**A. Mission / Vision Statements**
- Explicit statements of company purpose, long-term aspiration, or raison d'etre
- Look for: "Our mission is...", "We exist to...", "Our purpose...", vision statements in annual letters

**B. Strategic Pillars**
- Explicitly named priorities, focus areas, or strategic themes
- Look for: numbered priorities, named initiatives, section headers in strategy presentations, "Our [N] priorities are..."
- Distinguish between explicitly named pillars and analyst-inferred themes

**C. Quantitative Targets**
- Specific numerical goals attached to strategic areas
- Look for: revenue targets, user growth goals, margin targets, market share aspirations, Rule of 40 references
- Record the metric, target value, timeline, and conditions

**D. Resource Allocation Signals**
- Statements indicating where capital, headcount, or organizational attention will be directed
- Look for: capex plans, R&D investment areas, hiring priorities, "We are investing in...", "We are doubling down on..."
- Distinguish between past allocation (fact) and future allocation (intent)

**E. C-Level Framing**
- How senior leadership frames the company's strategic narrative
- Look for: CEO letter themes, CFO capital allocation philosophy, narrative emphasis patterns
- Note the order in which topics are discussed (earlier = higher implicit priority)
- Track which leaders discuss which topics (indicates organizational ownership)

### Step 3: Aspiration vs. Operation Classification

For each extracted element, classify its language register:

- **Aspirational:** Forward-looking, vision-oriented language with no concrete operational backing ("We believe the future of finance is..."). Mark as `aspirational`.
- **Operational:** Language tied to specific actions, metrics, or resource decisions ("We are allocating $X to..."). Mark as `operational`.
- **Transitional:** Elements that bridge aspiration and operation ("We have begun to invest in... and expect to..."). Mark as `transitional`.

This classification is critical for downstream pillar mapping — operational elements carry higher weight than aspirational ones.

### Step 4: Confidence Assessment

Assign a confidence score (0.0–1.0) to each element based on:

| Factor | Higher Confidence | Lower Confidence |
|--------|-------------------|------------------|
| Source type | Regulatory filing (10-K) | Press release |
| Specificity | Named metric + target | Vague directional statement |
| Repetition | Stated across multiple sources | Mentioned once |
| Recency | Most recent filing | Older document |
| Context | Prepared, formal section | Offhand remark |

## Output Format

Produce a JSON file (`data/processed/stage_1a_strategy.json`) with the following schema:

```json
{
  "metadata": {
    "stage": "1A",
    "company": "Block, Inc.",
    "extraction_date": "YYYY-MM-DD",
    "sources_analyzed": ["S-001", "S-003", "..."],
    "methodology": "Manual extraction from strategy-type sources per prompts/01_gather_strategy.md",
    "limitations": "..."
  },
  "strategy_elements": [
    {
      "id": "STR-001",
      "type": "mission_vision | strategic_pillar | quantitative_target | resource_allocation | c_level_framing",
      "content": "Verbatim or closely paraphrased text of the strategy element",
      "language_register": "aspirational | operational | transitional",
      "source_id": "S-001",
      "source_date": "YYYY-MM-DD",
      "source_bias": "company-produced | regulatory-filing | third-party-analyst | journalist",
      "confidence": 0.85,
      "notes": "Additional context, e.g., 'Mentioned first in shareholder letter, repeated in 10-K MD&A'"
    }
  ]
}
```

### ID Convention

- Strategy elements use the prefix `STR-` followed by a three-digit sequential number: `STR-001`, `STR-002`, etc.
- Numbering is sequential across all sources (not per-source).

### Minimum Extraction Targets

- At least 2 mission/vision elements
- At least 3 strategic pillar elements
- At least 2 quantitative targets (if available in source material)
- At least 2 resource allocation signals
- At least 2 C-level framing elements

If any category yields zero elements, explicitly note this gap in the metadata limitations field.

## Limitations

- Strategy documents are inherently **company-produced** and reflect management's chosen narrative, not necessarily operational reality. Every element extracted here should be treated as a *claim* rather than a *fact*.
- Extraction from investor presentations may over-index on slide titles and key messages, which are crafted for persuasion rather than precision.
- Temporal lag: shareholder letters and 10-K filings reflect past-year strategy; the current strategic posture may have shifted.
- Language register classification (aspirational vs. operational) involves judgment and may vary between analysts.

## Bias Awareness

1. **Source bias is inherited:** Every element carries the bias classification of its source document. Company-produced sources (shareholder letters, investor day) are designed to present a favorable narrative and may emphasize areas of strength while downplaying challenges.
2. **Confirmation bias risk:** The analyst may unconsciously seek elements that confirm expected pillars (e.g., "Bitcoin" for Block). Mitigate by extracting *all* strategy-relevant statements before categorizing.
3. **Recency bias:** More recent documents are easier to recall and may receive disproportionate attention. Process documents chronologically and track element counts per source to ensure balance.
4. **Framing effects:** C-level framing may use deliberately vague language to maintain strategic flexibility. Flag vague elements explicitly rather than interpreting them into specificity.
5. **Regulatory filings as corrective:** 10-K MD&A sections carry legal liability for material misstatement, making them a more reliable (though less granular) check on company-produced narratives.
