# Stage 0 — Source Identification and Classification

## Objective

Systematically identify, catalog, and classify all publicly available information sources pertaining to Block, Inc. (formerly Square, Inc.) that are necessary and sufficient for evaluating strategic coherence. This stage establishes the evidentiary foundation upon which all subsequent analysis depends; no downstream stage may proceed until source sufficiency criteria are satisfied.

## Inputs

- Company identity: **Block, Inc.** (NYSE: XYZ → SQ; legal name change effective December 2021)
- Public information domains: SEC filings, investor relations, press/newsroom, third-party analyst coverage, financial journalism
- No proprietary, leaked, or non-public information may be used

## Method

### Step 1: Source Discovery

Conduct a structured search across the following source categories:

**A. Strategy Sources** (documents that articulate strategic intent)
- Annual shareholder letters (Jack Dorsey / CEO communications)
- Investor Day presentations and transcripts
- Annual Reports (10-K filings, specifically MD&A and Business Overview sections)
- Investor presentations filed with the SEC or hosted on investor relations site

**B. Action/Execution Sources** (documents that reveal operational decisions and resource allocation)
- Quarterly filings (10-Q, specifically MD&A, segment reporting, and risk factors)
- Press releases from Block newsroom (product launches, acquisitions, organizational changes)
- Capital expenditure disclosures and segment financial data
- Organizational restructuring announcements (e.g., layoffs, reorgs, leadership changes)
- Earnings call transcripts (both prepared remarks and Q&A)

**C. External Validation Sources** (independent perspectives)
- Sell-side analyst reports and consensus estimates (where publicly summarized)
- Financial journalist coverage (e.g., Wall Street Journal, Bloomberg, Reuters)
- Regulatory actions or filings (CFPB, state regulators, SEC enforcement)
- Industry reports referencing Block's competitive positioning

### Step 2: Source Classification

For each identified source, record the following attributes:

| Field | Description |
|-------|-------------|
| `source_id` | Unique identifier: `S-001`, `S-002`, etc. |
| `title` | Full title of the document or article |
| `date` | Publication or filing date (YYYY-MM-DD) |
| `type` | `strategy` \| `action` \| `external-validation` |
| `bias_classification` | `company-produced` \| `regulatory-filing` \| `third-party-analyst` \| `journalist` |
| `url` | Direct URL or SEC EDGAR accession number |
| `relevance` | Brief note on what strategic question this source informs |
| `reliability` | `High` \| `Medium` \| `Low` — based on source independence, recency, and verifiability |

### Step 3: Sufficiency Assessment

After cataloging all sources, evaluate against the following minimum criteria:

**Sufficiency Checklist:**

- [ ] **Strategy coverage:** >= 2 documents that explicitly articulate strategic priorities (e.g., shareholder letter + investor day + 10-K)
- [ ] **Temporal coverage:** Sources span >= 12 months to capture evolution
- [ ] **Earnings transcripts:** >= 2 quarters of earnings call transcripts (for commitment extraction and Q&A candor analysis)
- [ ] **Action/execution sources:** >= 3 sources documenting concrete actions (filings, press releases, financial data)
- [ ] **External validation:** >= 1 independent source (analyst, journalist, or regulator) providing outside perspective
- [ ] **Bias distribution:** No single bias category accounts for > 60% of total sources
- [ ] **Segment coverage:** Sources available for all major business segments (Cash App, Square/Seller, TIDAL/music, Bitcoin/TBD)

If any criterion is unmet, flag the specific gap and indicate what additional source gathering is required before proceeding to Stage 1.

## Output Format

Produce a markdown file (`data/processed/stage_0_sources.md`) containing:

### 1. Source Catalog Table

```markdown
| Source ID | Title | Date | Type | Bias Classification | URL | Relevance | Reliability |
|-----------|-------|------|------|---------------------|-----|-----------|-------------|
| S-001 | ... | ... | ... | ... | ... | ... | ... |
```

### 2. Sufficiency Assessment

```markdown
## Sufficiency Assessment

### Checklist
- [x/✗] Strategy coverage: [count] documents — [PASS/FAIL]
- [x/✗] Temporal coverage: [date range] — [PASS/FAIL]
- ...

### Bias Distribution
| Bias Category | Count | Percentage |
|---------------|-------|------------|
| company-produced | N | X% |
| regulatory-filing | N | X% |
| third-party-analyst | N | X% |
| journalist | N | X% |

### Gaps Identified
[Description of any gaps and recommended remediation]

### Sufficiency Verdict
[SUFFICIENT / INSUFFICIENT — with justification]
```

## Limitations

- Source discovery is bounded by what is publicly accessible at the time of analysis; paywalled or restricted content may be unavailable.
- Reliability assessments are subjective and should be treated as indicative rather than definitive.
- SEC filings have inherent lag (quarterly cadence); recent actions may not yet appear in regulatory documents.
- Third-party analyst reports are often proprietary; only publicly available summaries or excerpts may be usable.

## Bias Awareness

This stage is particularly susceptible to **selection bias** — the analyst may inadvertently favor sources that are easier to find (e.g., company-produced materials dominate search results). Mitigations:

1. **Deliberate category balancing:** Search explicitly within each category (strategy, action, external) rather than relying on general search results.
2. **Bias tagging is mandatory:** Every source receives a bias classification before any content is analyzed.
3. **Sufficiency thresholds enforce diversity:** The requirement that no single bias category exceed 60% structurally prevents over-reliance on company narratives.
4. **Regulatory filings as anchor:** SEC filings (10-K, 10-Q) are legally mandated disclosures with material misstatement liability, making them the most reliable category. These should serve as the evidentiary anchor.
