# Stage P0 — Peer Group Identification

## Objective

Systematically identify and classify a group of publicly listed peers for {COMPANY} ({TICKER}) within the alternative asset management industry. The peer group must be defensible, balanced between "scale peers" (similar AUM) and "strategy peers" (similar asset class mix), and sufficient for meaningful benchmarking.

## Inputs

- Company identity: {COMPANY} ({TICKER})
- Industry: Alternative asset management
- Public information: SEC filings, investor relations, industry databases

## Method

### Step 1: Candidate Discovery

Search for publicly listed alternative asset managers. Consider:

- Pure-play alternative asset managers
- Diversified asset managers with significant alternatives AUM
- Regional specialists with comparable strategy focus

### Step 2: Selection Criteria

**Primary criteria (all required):**
- Same industry (alternative asset management)
- Publicly listed (on major exchange)
- AUM within 0.1x–10x of {COMPANY}'s AUM
- Sufficient public data for analysis

**Secondary criteria (at least 2 of 4):**
- Geographic overlap (similar markets)
- Strategy similarity (similar asset class mix)
- Similar business model (fee structure, fund types)
- Similar growth stage / maturity

**Exclusion criteria:**
- No public financial data available
- AUM difference > 10x (not comparable)
- Different industry entirely (traditional asset management, banking)
- Insufficient English-language disclosures

### Step 3: Peer Classification

Classify each peer as:

- **Scale peer**: Similar AUM / revenue scale to {COMPANY}
- **Strategy peer**: Similar asset class mix / investment strategy focus
- **Both**: Peers that qualify on both dimensions

### Step 4: Peer Group Validation

Verify:

- [ ] 5-7 peers identified (minimum 5 for statistical relevance)
- [ ] At least 2 scale peers and 2 strategy peers
- [ ] No single geography or sub-sector dominates the group (>60%)
- [ ] All peers have adequate English-language public disclosures

## Output Format

Produce JSON file `data/processed/{ticker}/peer_p0_identification.json`:

```json
{
  "metadata": {
    "stage": "P0",
    "company": "{COMPANY}",
    "ticker": "{TICKER}",
    "analysis_date": "YYYY-MM-DD",
    "methodology": "Peer selection per prompts/peer/p00_peer_identification.md",
    "limitations": "..."
  },
  "target_company": {
    "name": "{COMPANY}",
    "ticker": "{TICKER}",
    "exchange": "...",
    "aum": "...",
    "primary_strategies": ["..."],
    "geography": "..."
  },
  "peers": [
    {
      "id": "PEER-001",
      "name": "...",
      "ticker": "...",
      "exchange": "...",
      "aum": "...",
      "aum_currency": "USD",
      "primary_strategies": ["..."],
      "geography": "...",
      "classification": "scale | strategy | both",
      "selection_rationale": "...",
      "data_availability": "high | medium | low",
      "key_differences": "..."
    }
  ],
  "peer_group_summary": {
    "total_peers": 6,
    "scale_peers": 3,
    "strategy_peers": 2,
    "both": 1,
    "geographic_distribution": {},
    "aum_range": {},
    "validation_checklist": {}
  }
}
```

## Limitations

- Peer selection involves judgment; different analysts may select different peer groups.
- AUM figures are point-in-time and fluctuate with market conditions and fundraising.
- "Strategy similarity" is subjective — asset class categorizations vary across firms.
- Some peers may have significant non-alternatives businesses that complicate comparison.

## Bias Awareness

This stage is particularly susceptible to selection bias — the analyst may inadvertently favor familiar or prominent firms over more comparable but less-covered ones. Mitigations:

1. **Familiarity bias**: Deliberate candidate discovery across pure-play, diversified, and regional alternatives managers prevents over-concentration on well-known names.
2. **Survivorship bias**: Include peers across a range of AUM sizes and growth stages, not only the largest or most successful firms.
3. **Geographic bias**: Explicitly search for non-US-listed alternatives managers; note when a peer is excluded solely due to limited English-language disclosures.
4. **Size anchoring**: Very large peers (BAM, APO) may distort comparisons despite being in the same industry — the 0.1x–10x AUM filter is the primary structural mitigation.
