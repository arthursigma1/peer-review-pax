# Stage P0c — Peer Source Mapping

## Objective

Catalog all publicly available information sources for {COMPANY} ({TICKER}) and each identified peer that are necessary for quantitative benchmarking. This stage extends the source mapping framework from the drift pipeline (`prompts/drift/00_source_mapping.md`) to cover multiple companies simultaneously.

## Inputs

- Target company: {COMPANY} ({TICKER})
- Peer list: `data/processed/{ticker}/peer_p0_identification.json`
- Metric definitions: `data/processed/{ticker}/peer_p0_metrics.json`

## Method

### Step 1: Source Discovery (per company)

For {COMPANY} and each PEER-NNN, search the following source categories:

**A. Regulatory Filings**
- {COMPANY}: 20-F (annual, foreign private issuer), 6-K (interim)
- US peers: 10-K (annual), 10-Q (quarterly)
- All companies: proxy statements, 8-K material event filings

**B. Investor Relations**
- Earnings call transcripts (last 2-4 quarters)
- Investor presentations / supplemental financial data packages
- Annual reports (if published separately from regulatory filing)
- Earnings press releases

**C. Industry Sources**
- Preqin alternative assets data
- PitchBook market reports
- Bain Global Private Equity Reports
- McKinsey Global Private Markets Reviews

**D. External Analysis**
- Sell-side analyst reports (publicly available summaries only)
- Financial journalism (Bloomberg, FT, Reuters)
- Industry conferences and panels featuring management

### Step 2: Source Classification

For each source identified, record:

| Field | Description |
|-------|-------------|
| `source_id` | Unique identifier: `PS-001`, `PS-002`, etc. |
| `company` | PEER-NNN identifier or {TICKER} |
| `title` | Full title of the document |
| `date` | Publication or filing date (YYYY-MM-DD) |
| `type` | `filing` \| `transcript` \| `presentation` \| `industry-report` \| `news` |
| `bias_classification` | `company-produced` \| `regulatory-filing` \| `third-party-analyst` \| `journalist` \| `industry-report` \| `peer-disclosure` |
| `url` | Direct URL or filing reference (SEC EDGAR accession number) |
| `metrics_covered` | List of MET-NNN identifiers this source can inform |
| `reliability` | `High` \| `Medium` \| `Low` |

### Step 3: Sufficiency Assessment (per company)

Evaluate each company against the following minimum requirements:

- [ ] >= 1 annual filing (20-F or 10-K) available
- [ ] >= 1 earnings transcript or investor presentation available
- [ ] >= 1 source containing quantitative financial metrics
- [ ] Sources span >= 12 months to enable YoY calculations

Companies that do not meet the minimum threshold must be flagged for potential exclusion from specific metrics or from the peer group entirely.

### Step 4: Cross-Company Coverage Matrix

After completing Steps 1-3, construct a matrix showing which metrics (MET-NNN columns) can be populated for which companies (rows), using the following notation:

- `Y` — source confirmed, data expected
- `P` — partial source only; data may be incomplete
- `N` — no source identified; metric cannot be populated for this company

## Output Format

Markdown file `data/processed/{ticker}/peer_p0_sources.md` containing the following sections:

### 1. Source Catalog (per company)

```markdown
| Source ID | Company | Title | Date | Type | Bias Classification | URL | Metrics Covered | Reliability |
|-----------|---------|-------|------|------|---------------------|-----|-----------------|-------------|
| PS-001 | {TICKER} | ... | ... | ... | ... | ... | MET-001, MET-003 | High |
```

### 2. Sufficiency Assessment

```markdown
## Sufficiency Assessment

| Company | Annual Filing | Transcript/Presentation | Financial Metrics | >= 12 Months | Verdict |
|---------|---------------|-------------------------|-------------------|--------------|---------|
| {TICKER} | [Y/N] | [Y/N] | [Y/N] | [Y/N] | SUFFICIENT / INSUFFICIENT |
| PEER-001 | ... | ... | ... | ... | ... |
```

### 3. Coverage Matrix

```markdown
## Coverage Matrix

|          | MET-001 | MET-002 | MET-003 | ... |
|----------|---------|---------|---------|-----|
| {TICKER} | Y | Y | P | ... |
| PEER-001 | Y | N | Y | ... |
```

### 4. Gaps and Recommendations

Description of any coverage gaps, peers flagged for exclusion from specific metrics, and recommended additional source gathering before proceeding to Stage P1.

## Limitations

- Foreign private issuers (20-F filers) have different disclosure timing and format compared to domestic 10-K filers; period alignment may be imperfect.
- Some peers may have limited English-language disclosures, restricting data availability.
- Industry databases (Preqin, PitchBook) are typically paywalled; only publicly available summaries may be accessible.
- Earnings transcripts may not be freely available for all companies on all platforms.

## Bias Awareness

This stage inherits all source-selection biases from the single-company pipeline and introduces additional cross-firm asymmetries. Mitigations:

1. **Data availability asymmetry**: US-listed companies have more accessible and standardized disclosures than foreign filers — document this explicitly in the sufficiency assessment rather than silently excluding foreign peers.
2. **Large-cap bias**: Larger peers attract more analyst coverage and media attention, making source discovery easier; smaller or less prominent peers require more deliberate search effort.
3. **English-language bias**: Non-English materials may be excluded due to accessibility constraints — flag when a peer's disclosures are primarily in a language other than English.
4. **Recency bias**: Recent sources are easier to locate than historical filings; ensure multi-year coverage is explicitly verified rather than assumed.
