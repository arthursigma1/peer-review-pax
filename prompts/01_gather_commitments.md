# Stage 1C — Forward-Looking Commitment Extraction

## Objective

Extract structured forward-looking commitments, guidance statements, and public promises made by Block, Inc. leadership from earnings calls, presentations, and public communications. These commitments form the basis for evaluating whether management follows through on stated intentions, serving as a critical input to commitment fulfillment tracking in Stage 3 and coherence scoring in Stage 4.

## Inputs

- Source catalog from Stage 0 (`data/processed/stage_0_sources.md`), filtered to earnings transcripts, shareholder letters, and press releases containing forward-looking language
- Raw document text stored in `data/raw/block_commitments_{source_id}.txt`
- This prompt template

## Method

### Step 1: Document Retrieval

For each relevant source in the Stage 0 catalog:
1. Retrieve the full text of the document via web fetch or SEC EDGAR
2. Save the raw text to `data/raw/block_commitments_{source_id}.txt`
3. For earnings transcripts, clearly delineate **prepared remarks** from **Q&A** sections

### Step 2: Commitment Extraction

Read each document and extract forward-looking statements falling into the following categories:

**A. Guidance Statements**
- Formal financial guidance: revenue expectations, margin targets, adjusted EBITDA guidance, gross profit growth expectations
- Operational guidance: user growth expectations, transaction volume forecasts, take-rate expectations
- Look for: "We expect...", "We are guiding to...", "Our outlook for...", specific numerical ranges

**B. Verbal Commitments**
- Explicit promises of future action or investment direction
- Look for: "We will...", "We are committed to...", "We plan to...", "We intend to...", "We are going to..."
- Distinguish between firm commitments ("We will launch X in Q3") and directional statements ("We will continue to invest in...")

**C. Timeline Promises**
- Commitments with specific temporal markers
- Look for: "By the end of [year]...", "In the next [N] quarters...", "Within [timeframe]..."
- Record both the commitment and the timeline, then assess whether the timeline has passed (enabling fulfillment evaluation)

**D. Comparative Framing**
- Statements that commit to relative positioning or trajectory
- Look for: "We expect to outpace...", "We will grow faster than...", "We are targeting above-industry..."
- These are harder to verify but reveal management's competitive self-image

### Step 3: Prepared Remarks vs. Q&A Weighting

For earnings call transcripts, apply differential weighting:

| Context | Weight | Rationale |
|---------|--------|-----------|
| **Q&A responses** | Higher | Analyst questions probe specific areas; responses are less scripted and more candid. Management may reveal concerns or hedges not present in prepared remarks. |
| **Prepared remarks** | Standard | Carefully crafted narrative. Reliable for understanding management's *intended* message, but may omit inconvenient details. |
| **Analyst follow-ups** | Highest | Second-round questions on a topic often extract the most candid management commentary. |

Mark the `context` field for each commitment to enable downstream weighting.

### Step 4: Specificity Classification

Assess the specificity of each commitment:

| Specificity Level | Criteria | Example |
|-------------------|----------|---------|
| `quantitative` | Contains a specific number, percentage, or measurable target | "We expect gross profit growth of 25% in FY2025" |
| `time-bound` | Contains a specific deadline but not a numeric target | "We will launch lending products by Q4" |
| `directional` | Indicates direction of change without specifics | "We expect continued improvement in margins" |
| `aspirational` | Expresses intent without measurable criteria | "We are committed to being the leading platform for sellers" |

Quantitative and time-bound commitments are most valuable for Stage 4 coherence analysis because they can be objectively evaluated for fulfillment.

### Step 5: Status Assessment

For each commitment, assess its current status based on available evidence:

| Status | Definition |
|--------|------------|
| `fulfilled` | Clear evidence the commitment was met (e.g., reported metric meets guidance) |
| `in_progress` | Timeline has not expired; no contradicting evidence |
| `partially_fulfilled` | Some aspects met, others not, or met at a lower level than committed |
| `contradicted` | Subsequent actions or statements directly contradict the commitment |
| `silently_abandoned` | No further mention in subsequent communications; no evidence of follow-through |
| `cannot_assess` | Insufficient evidence to determine status |

This is a preliminary assessment; Stage 3 will refine these statuses with fuller evidence.

## Output Format

Produce a JSON file (`data/processed/stage_1c_commitments.json`) with the following schema:

```json
{
  "metadata": {
    "stage": "1C",
    "company": "Block, Inc.",
    "extraction_date": "YYYY-MM-DD",
    "sources_analyzed": ["S-005", "S-006", "..."],
    "methodology": "Manual extraction from forward-looking statements per prompts/01_gather_commitments.md",
    "qa_weighting": "Q&A responses weighted higher than prepared remarks per methodology",
    "limitations": "..."
  },
  "commitments": [
    {
      "id": "CMT-001",
      "statement": "Verbatim or closely paraphrased commitment text",
      "speaker": "Name and title (e.g., 'Jack Dorsey, CEO' or 'Amrita Ahuja, CFO')",
      "type": "guidance | verbal_commitment | timeline_promise | comparative_framing",
      "context": "prepared_remarks | qa_response | analyst_followup | shareholder_letter | press_release",
      "date": "YYYY-MM-DD",
      "source_id": "S-005",
      "source_bias": "company-produced | regulatory-filing | third-party-analyst | journalist",
      "specificity": "quantitative | time_bound | directional | aspirational",
      "status": "fulfilled | in_progress | partially_fulfilled | contradicted | silently_abandoned | cannot_assess",
      "status_evidence": "Brief explanation of how status was determined, with reference to corroborating source if available",
      "notes": "Additional context, e.g., 'Made in response to analyst question about Bitcoin strategy'"
    }
  ]
}
```

### ID Convention

- Commitment elements use the prefix `CMT-` followed by a three-digit sequential number: `CMT-001`, `CMT-002`, etc.
- Numbering is sequential across all sources (not per-source).

### Minimum Extraction Targets

- At least 3 guidance statements (if earnings transcripts are available)
- At least 3 verbal commitments across different strategic areas
- At least 2 timeline promises (if available)
- At least 1 comparative framing statement (if available)

If any category yields zero elements, explicitly note this gap in the metadata limitations field.

## Limitations

- Forward-looking statements are inherently uncertain; companies include safe harbor disclaimers for this reason. A commitment should not be equated with a guarantee.
- Earnings call transcripts may contain transcription errors that alter meaning, particularly in Q&A sections where speakers may talk over each other.
- Status assessment at this stage is preliminary and based on limited evidence. Stage 3 mapping will provide fuller context for fulfillment evaluation.
- Commitments made in different macroeconomic environments may have been reasonable when stated but rendered impractical by external events. This context should be noted but does not invalidate the commitment for tracking purposes.

## Bias Awareness

1. **Optimism bias in prepared remarks:** Management's prepared commentary is crafted to inspire confidence. Forward-looking statements in prepared remarks are likely to be more optimistic than what management privately expects. Weight Q&A responses more heavily for candor.
2. **Guidance as expectation management:** Formal guidance ranges are often set conservatively to enable management to "beat" expectations. Treat guidance as a floor rather than a midpoint unless explicitly stated otherwise.
3. **Selective commitment recall:** In subsequent quarters, management will naturally highlight fulfilled commitments and may silently drop unfulfilled ones. Actively track previously stated commitments across quarters to detect silent abandonment.
4. **Speaker-specific bias:** CEOs tend to be more visionary and optimistic; CFOs tend to be more measured and quantitative. Note the speaker for each commitment to enable appropriate weighting.
5. **Analyst question framing:** Analyst questions may be leading or reflect the analyst's own thesis. Extract the management response on its own merits rather than adopting the analyst's framing.
