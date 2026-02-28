# Stage 0 — Source Map for Block, Inc.

**Subject Entity:** Block, Inc. (NYSE: XYZ, formerly Square, Inc.)
**Date Compiled:** 2026-02-28
**Analyst:** source-scout (automated)

---

## 1. Methodology

### 1.1 Inputs

- Block, Inc. investor relations portal (investors.block.xyz)
- SEC EDGAR database (CIK 0001512673)
- Block corporate newsroom (block.xyz/news)
- Financial journalism outlets (CNBC, Bloomberg, Reuters, WSJ, Motley Fool, Seeking Alpha)
- Analyst rating services (Morgan Stanley, various consensus aggregators)

### 1.2 Method

A systematic web search was conducted across five source categories: (a) company-produced strategy documents (shareholder letters, investor day presentations), (b) regulatory filings (10-K, 10-Q, 8-K), (c) earnings call transcripts and supplemental materials, (d) corporate press releases and newsroom items, and (e) third-party analyst and journalist coverage. Each source was evaluated for recency (preference for the trailing 12-18 months ending February 2026), relevance to strategic direction or execution evidence, and bias classification. Sources were deduplicated and assigned sequential identifiers.

### 1.3 Outputs

A structured source catalog (Section 2) containing 25 entries spanning January 2025 through February 2026, with bias classification, reliability assessment, and relevance annotations.

### 1.4 Limitations

- Earnings call transcripts were identified by reference but full-text content was not ingested; downstream stages must retrieve transcript text from Seeking Alpha, Motley Fool, or BamSEC.
- Analyst reports from sell-side firms (e.g., Morgan Stanley) are paywalled; only publicly available summaries and rating actions are cataloged.
- TIDAL and Spiral (formerly TBD) received limited standalone coverage; most information is embedded within broader Block filings.
- The 10-K for fiscal year 2025 was filed on or around February 26, 2026; its full text may not yet be indexed in all secondary databases.

---

## 2. Source Catalog

### Strategy-Defining Documents

| Source ID | Title | Date | Type | Bias Classification | URL / Location | Relevance | Reliability |
|-----------|-------|------|------|---------------------|---------------|-----------|-------------|
| S-001 | Q4 2025 Shareholder Letter | 2026-02-26 | strategy | company-produced | [PDF](https://s29.q4cdn.com/628966176/files/doc_financials/2025/q4/Q4-2025-Shareholder-Letter_Block.pdf) | Primary strategy document; contains Dorsey's vision for AI-native restructuring, workforce reduction rationale, 2026 guidance, and Bitcoin ecosystem priorities. | High — official CEO communication to shareholders |
| S-002 | Block Investor Day 2025 — Multi-Year Financial Outlook | 2025-11-19 | strategy | company-produced | [Webcast & Materials](https://block.xyz/investor-day-2025) | Three-year financial outlook (through 2028), $5B buyback authorization, gross profit growth trajectory of mid-teens annually, operating leverage targets. | High — formal investor event with audited forward guidance |
| S-003 | Block Investor Day 2025 — Press Release | 2025-11-19 | strategy | company-produced | [BusinessWire](https://www.businesswire.com/news/home/20251119841382/en/Block-to-Outline-Multi-Year-Outlook-and-Stock-Repurchase-Plan-at-Investor-Day) | Summary of multi-year outlook and $5B stock repurchase authorization. | High — official press release |
| S-004 | Q3 2025 Shareholder Letter | 2025-11-06 | strategy | company-produced | [PDF](https://s29.q4cdn.com/628966176/files/doc_financials/2025/q3/Block_3Q25_Shareholder-Letter.pdf) | Quarterly strategy update; performance narrative for Cash App, Square, Bitcoin mining progress. | High — official quarterly communication |
| S-005 | Q1 2025 Shareholder Letter | 2025-05 (est.) | strategy | company-produced | [PDF](https://s29.q4cdn.com/628966176/files/doc_financials/2025/q1/Block_1Q25_Shareholder-Letter.pdf) | Early-2025 strategy framing; Square market share gains, growth acceleration expectations for H2 2025. | High — official quarterly communication |

### Regulatory Filings

| Source ID | Title | Date | Type | Bias Classification | URL / Location | Relevance | Reliability |
|-----------|-------|------|------|---------------------|---------------|-----------|-------------|
| S-006 | Block, Inc. Form 10-K (FY 2025) | 2026-02-26 | strategy | regulatory-filing | [SEC EDGAR](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001512673&type=10-K&dateb=&owner=include&count=10) / [StockTitan Summary](https://www.stocktitan.net/sec-filings/XYZ/10-k-block-inc-files-annual-report-97739237536a.html) | Comprehensive annual disclosure: business segments (Commerce Enablement, Financial Solutions, Bitcoin Ecosystem), risk factors, $10.36B gross profit, workforce restructuring disclosure, Bitcoin treasury of 8,883 BTC. | High — audited SEC filing with legal liability |
| S-007 | Block, Inc. Form 10-K (FY 2024) | 2025-02-22 | strategy | regulatory-filing | [SEC EDGAR](https://www.sec.gov/Archives/edgar/data/1512673/000162828024006354/0001628280-24-006354-index.htm) | Prior-year baseline for year-over-year drift analysis; business model description, risk factors, revenue of $24.1B. | High — audited SEC filing |
| S-008 | Block, Inc. Form 10-Q (Q2 2025) | 2025-08 (est.) | action | regulatory-filing | [SEC EDGAR / Investor Relations](https://investors.block.xyz/financials/sec-filings/default.aspx) | Quarterly financial data: $2.54B gross profit, 14% YoY growth, Cash App 16% growth, Square 11% growth. | High — SEC quarterly filing |
| S-009 | Block, Inc. Form 8-K — Q4 2025 Results & Workforce Reduction | 2026-02-26 | action | regulatory-filing | [StockTitan](https://www.stocktitan.net/sec-filings/XYZ/8-k-block-inc-reports-material-event-0d8318aad5f8.html) | Material event disclosure: 40%+ workforce reduction (10,000+ to <6,000), raised 2026 guidance. | High — SEC current report |

### Earnings Call Transcripts

| Source ID | Title | Date | Type | Bias Classification | URL / Location | Relevance | Reliability |
|-----------|-------|------|------|---------------------|---------------|-----------|-------------|
| S-010 | Block Q4 2025 Earnings Call Transcript | 2026-02-27 | action | company-produced | [Motley Fool](https://www.fool.com/earnings/call-transcripts/2026/02/27/block-xyz-q4-2025-earnings-call-transcript/) / [Seeking Alpha](https://seekingalpha.com/symbol/XYZ/earnings/transcripts) | Management commentary on AI-native restructuring, workforce cuts, 2026 guidance rationale, segment performance, Bitcoin mining update. | High — verbatim transcript of public earnings call |
| S-011 | Block Q3 2025 Earnings Call Transcript | 2025-11-06 | action | company-produced | [Seeking Alpha](https://seekingalpha.com/symbol/XYZ/earnings/transcripts) / [BamSEC](https://www.bamsec.com/companies/1512673/block-inc/transcripts) | Management discussion of Q3 performance, Cash App growth drivers, Square GPV trends, Proto mining chip manufacturing update. | High — verbatim transcript |
| S-012 | Block Q2 2025 Earnings Call Transcript | 2025-08-07 | action | company-produced | [Seeking Alpha](https://seekingalpha.com/symbol/XYZ/earnings/transcripts) / [BamSEC](https://www.bamsec.com/companies/1512673/block-inc/transcripts) | Q2 performance discussion, raised 2025 guidance to $10.17B gross profit, Cash App Afterpay integration progress. | High — verbatim transcript |
| S-013 | Block Q1 2025 Earnings Call Transcript | 2025-05 (est.) | action | company-produced | [Seeking Alpha](https://seekingalpha.com/symbol/XYZ/earnings/transcripts) / [Investing.com](https://www.investing.com/news/transcripts/earnings-call-transcript-block-inc-q1-2025-misses-eps-and-revenue-forecasts-93CH-4018504) | Q1 performance miss on EPS and revenue; management response and H2 acceleration thesis. | High — verbatim transcript |
| S-014 | Block Q4 2024 Earnings Call Transcript | 2025-02 (est.) | action | company-produced | [Seeking Alpha](https://seekingalpha.com/symbol/XYZ/earnings/transcripts) / [BamSEC](https://www.bamsec.com/companies/1512673/block-inc/transcripts) | FY2024 wrap-up; baseline strategy framing entering 2025. | High — verbatim transcript |

### Investor Presentations

| Source ID | Title | Date | Type | Bias Classification | URL / Location | Relevance | Reliability |
|-----------|-------|------|------|---------------------|---------------|-----------|-------------|
| S-015 | Block Q3 2025 Investor Presentation | 2025-11-06 | strategy | company-produced | [PDF](https://s29.q4cdn.com/628966176/files/doc_financials/2025/q3/Block_Investor-Presentation-3Q25.pdf) | Slide deck with segment breakdown, KPI trends, strategic priorities visualization. | High — official supplemental materials |
| S-016 | Block Q2 2025 Investor Presentation | 2025-08-07 | strategy | company-produced | [PDF](https://s29.q4cdn.com/628966176/files/doc_financials/2025/q2/Block_Investor-Presentation-2Q25.pdf) | Mid-year strategy and financial performance slides. | High — official supplemental materials |

### Corporate Press Releases & Newsroom

| Source ID | Title | Date | Type | Bias Classification | URL / Location | Relevance | Reliability |
|-----------|-------|------|------|---------------------|---------------|-----------|-------------|
| S-017 | Block Unveils Proto Rig and Proto Fleet | 2025-08-14 | action | company-produced | [BusinessWire](https://www.businesswire.com/news/home/20250814809089/en/Block-Unveils-Proto-Rig-and-Proto-Fleet-Marking-a-New-Era-in-Bitcoin-Mining) / [Investors.block.xyz](https://investors.block.xyz/investor-news/news-details/2025/Block-Unveils-Proto-Rig-and-Proto-Fleet-Marking-a-New-Era-in-Bitcoin-Mining/default.aspx) | Concrete execution evidence for Bitcoin mining strategy: modular 819 TH/s mining system, open-source fleet software, partnership with Core Scientific. | High — official product launch announcement |
| S-018 | Block Announces Fourth Quarter 2025 Results | 2026-02-26 | action | company-produced | [BusinessWire](https://www.businesswire.com/news/home/20260226099357/en/Block-Announces-Fourth-Quarter-2025-Results) | Official earnings press release: $2.87B Q4 gross profit (+24% YoY), $10.36B full-year, workforce restructuring. | High — official press release |
| S-019 | Block Surpasses $200 Billion in Credit Provided to Customers | 2025 (est.) | action | company-produced | [block.xyz](https://block.xyz/inside/block-inc-surpasses-usd200-billion-in-credit-provided-to-customers-continuing-to-address-global-lending-gaps) | Execution milestone for lending strategy across Cash App Borrow, Afterpay, and Square Loans. | High — official corporate announcement |
| S-020 | Square BFCM 2025 — 124 Million Transactions | 2025-12 (est.) | action | company-produced | [squareup.com](https://squareup.com/us/en/press/bfcm-2025) | Commerce execution evidence: 124M transactions over Black Friday/Cyber Monday, 10% YoY increase. | Medium — marketing-oriented press release |

### Third-Party Analyst Coverage

| Source ID | Title | Date | Type | Bias Classification | URL / Location | Relevance | Reliability |
|-----------|-------|------|------|---------------------|---------------|-----------|-------------|
| S-021 | Morgan Stanley Upgrades Block Inc. (XYZ) to Overweight | 2026-02-27 | external-validation | third-party-analyst | [StreetInsider](https://www.streetinsider.com/Analyst+Comments/Morgan+Stanley+Upgrades+Block+Inc.+(XYZ)+to+Overweight/26074200.html) / [Investing.com](https://www.investing.com/news/analyst-ratings/morgan-stanley-upgrades-block-stock-rating-on-product-expansion-93CH-4530893) | Independent validation of strategy pivot; PT raised to $93 on AI-driven profitability thesis, 2026 EPS projection of $3.81. | Medium — sell-side analyst opinion with potential conflicts |
| S-022 | Block Expects Profit Growth to Accelerate Over Next 3 Years | 2025-11-19 | external-validation | journalist | [Bloomberg](https://www.bloomberg.com/news/articles/2025-11-19/block-expects-profit-growth-to-accelerate-over-next-three-years) | Independent journalist coverage of Investor Day outlook; provides third-party framing of management claims. | Medium — major financial news outlet, editorial standards |
| S-023 | Block's Stock Pops 9% on Gross Profit Forecast, 3-Year Financial Outlook | 2025-11-19 | external-validation | journalist | [CNBC](https://www.cnbc.com/2025/11/19/block-unveils-3-year-outlook-sees-gross-profit-in-2028-of-15point8b.html) | Market reaction and independent analysis of Investor Day announcements, $15.8B 2028 gross profit target. | Medium — major financial news outlet |
| S-024 | Block Shares Soar as Much as 24% as Company Slashes Workforce by Nearly Half | 2026-02-26 | external-validation | journalist | [CNBC](https://www.cnbc.com/2026/02/26/block-laying-off-about-4000-employees-nearly-half-of-its-workforce.html) | Independent reporting on workforce restructuring and market response; provides external perspective on AI-native pivot credibility. | Medium — major financial news outlet |
| S-025 | Jack Dorsey's Mainstream Dream Faces Test as Block Joins S&P 500 | 2025-07-23 | external-validation | journalist | [Fortune](https://fortune.com/crypto/2025/07/23/jack-dorsey-block-square-sp-500-index-fund/) | Independent assessment of Block's maturation thesis following S&P 500 inclusion; provides external validation/skepticism lens. | Medium — major business publication |

---

## 3. Sufficiency Check

| Criterion | Threshold | Result | Status |
|-----------|-----------|--------|--------|
| Strategy-defining documents | >= 2 | 7 (S-001, S-002, S-004, S-005, S-006, S-007, S-015) | PASS |
| Quarters of earnings transcripts | >= 2 | 5 (Q4 2024 through Q4 2025: S-010, S-011, S-012, S-013, S-014) | PASS |
| Action/commitment sources | >= 3 | 9 (S-008, S-009, S-010 through S-014, S-017, S-018, S-019, S-020) | PASS |
| External validation sources | >= 1 | 5 (S-021 through S-025) | PASS |
| Temporal span >= 12 months | >= 12 months | ~14 months (Feb 2025 through Feb 2026) | PASS |
| No single bias category > 60% | <= 60% | company-produced: 16/25 (64%) | MARGINAL FAIL |

### Bias Distribution

| Bias Category | Count | Percentage |
|---------------|-------|------------|
| company-produced | 16 | 64% |
| regulatory-filing | 4 | 16% |
| third-party-analyst | 1 | 4% |
| journalist | 4 | 16% |

**Note on Bias Concentration:** Company-produced sources marginally exceed the 60% threshold at 64%. This is partly structural — shareholder letters and earnings transcripts are inherently company-produced yet contain essential strategy and execution data. The 4 regulatory filings provide legally mandated disclosures with independent audit oversight, and the 5 external validation sources (1 analyst, 4 journalist) offer independent framing. Downstream stages should weight external sources when assessing claim credibility and seek additional analyst coverage if available.

---

## 4. Limitations

1. **Transcript Access:** Earnings call transcripts (S-010 through S-014) were identified by reference only. Full-text retrieval requires access to Seeking Alpha, Motley Fool, or BamSEC; some may be behind paywalls.

2. **Analyst Report Depth:** Only one sell-side analyst action (Morgan Stanley, S-021) was cataloged with publicly available detail. A consensus of 31 analysts covers the stock, but individual reports are paywalled. Downstream stages should note that external validation of strategy is somewhat thin.

3. **10-K Full Text:** The FY 2025 10-K (S-006) was filed on February 26, 2026 — two days before this catalog was compiled. Full-text indexing in secondary databases may be incomplete.

4. **Q2 2025 Shareholder Letter:** The Q2 2025 shareholder letter was not located as a direct PDF link; its contents are reflected in the Q2 investor presentation (S-016) and earnings call transcript (S-012).

5. **TIDAL and Spiral (TBD):** Coverage of Block's decision to scale back TIDAL investment and shutter TBD/Web5 (announced November 2024) is embedded within broader Block coverage rather than cataloged as a standalone source. This strategic pivot is relevant to drift analysis.

6. **Regulatory/Legal:** CFPB oversight of BNPL providers (affecting Afterpay) is noted as contextual but not cataloged as a standalone source, as no specific enforcement action against Block was identified in the search period.

---

## 5. Recommended Retrieval Priority for Downstream Stages

For **Stage 1A (Strategy Gathering)**, prioritize:
- S-001 (Q4 2025 Shareholder Letter) — most recent strategic vision
- S-002 (Investor Day 2025) — three-year outlook and strategic pillars
- S-006 (10-K FY 2025) — comprehensive business model and risk factors
- S-004 (Q3 2025 Shareholder Letter) — mid-period strategy narrative

For **Stage 1B (Actions & Execution Evidence)**, prioritize:
- S-017 (Proto Rig launch) — Bitcoin mining execution
- S-018 (Q4 2025 results) — financial performance metrics
- S-009 (8-K workforce reduction) — organizational restructuring
- S-019 ($200B credit milestone) — lending execution
- S-010 through S-014 (Earnings call transcripts) — management commentary on execution

For **Stage 1C (Public Commitments)**, prioritize:
- S-002 (Investor Day 2025) — quantified financial targets
- S-001 (Q4 2025 Shareholder Letter) — 2026 guidance and workforce commitments
- S-003 (Investor Day press release) — $5B buyback commitment
