# Value Creation Principles — VD-P1
## Run: 2026-03-10-run4 | Base Run: 2026-03-10-run2
## Generated: 2026-03-11

---

## IMPORTANT METHODOLOGICAL NOTE

No stable value driver was identified in this run. A stable driver requires avg|ρ| ≥ 0.50 on two or more multiples simultaneously. In the 23-firm cross-section (FY2024), no driver meets this threshold. This contrasts with prior runs where DE/share and G&A/FEAUM achieved stable status under different sample compositions. The broader sample (23 firms, including European and EM-based managers) reduces cross-sectional signal strength through structural heterogeneity.

Only two correlations survive Benjamini-Hochberg false discovery rate correction at q=0.10:
- AUM × P/FRE: ρ=+0.7286, p=0.000100 (Bonferroni-surviving)
- FEAUM × P/FRE: ρ=+0.6045, p=0.002882 (BH-significant)

All other findings are exploratory (nominally significant but failing BH correction) and must be communicated with explicit hedging.

---

## Principle 1: Platform Scale Commands the P/FRE Premium (DVR-001 — Total AUM)

### Statistical Finding

Total AUM is the strongest and most robustly supported value driver in this cross-section.

| Multiple | ρ (Spearman) | 95% CI | p-value | BH Significant | N |
|----------|-------------|--------|---------|----------------|---|
| P/FRE | +0.7286 | [+0.47, +0.89] | 0.000100 | YES (Bonferroni-surviving) | 22 |
| P/DE | +0.4906 | [+0.15, +0.74] | 0.028 | NO | 20 |
| EV/FEAUM | +0.1661 | [-0.25, +0.55] | 0.460 | NO | 22 |

**Classification:** Multiple-specific driver (P/FRE only, BH-significant). Average |ρ| across multiples: 0.46.

**Sensitivity:** Leave-one-out removing BX (the largest AUM outlier at $1,127B) reduces ρ from +0.73 to approximately +0.62. The relationship survives but is attenuated, indicating that while BX amplifies the pattern, it does not manufacture it. No single observation drives the result.

### Economic Mechanism

Scale in alternative asset management operates through three compounding effects. First, large platforms signal institutional durability — investors assign a lower probability of AUM attrition to managers with $300B+ AUM versus those with $20-50B AUM. Second, scale creates fee diversification across strategies, geographies, and vintages, reducing earnings volatility from any single fund cycle. Third, mega-scale managers achieve G&A efficiency through amortization of fixed infrastructure (technology, legal, compliance, portfolio monitoring) across an enormous AUM base, supporting higher FRE margins even before insurance float effects.

The P/FRE premium for scale is a confidence premium, not simply a reward for size. Investors price the probability that the platform survives LP capital cycle downturns, management succession events, and fundraising droughts. Scale reduces all three risks simultaneously.

### Illustrative Firms

**Top quartile on DVR-001 (Q4, highest AUM):** BX ($1,127B), BAM ($1,050B), APO ($751B). These firms trade at the highest absolute P/FRE multiples in the universe (20-28x range), consistent with the positive ρ. Their scale advantages are structural: insurance float capital (APO, KKR), operator heritage (BAM), and perpetual capital vehicles (BX) all reinforce AUM durability.

**Mid-scale cohort (Q2-Q3):** Firms with $100-500B AUM (ARES, TPG, CG, EQT) occupy the middle P/FRE range (15-22x). These firms are in active scale-building phases — their AUM trajectories rather than current AUM levels are the relevant signal for forward P/FRE positioning.

**Small-scale cohort (Q1, lowest AUM):** PAX ($55B), ANTIN ($33B), HLNE ($146B). PAX ranks 18/22 on this driver. Its P/FRE discount to peer median (14.9x vs 17.7x peer median, -15.8%) is partly attributable to scale gap.

### Limitations and Boundary Conditions

1. **Causation caveat:** The positive correlation does not establish that growing AUM causes P/FRE expansion. Endogeneity is plausible — firms trading at high P/FRE can raise capital more easily, mechanically expanding AUM. The relationship is bidirectional.
2. **EV/FEAUM insensitivity:** AUM is uncorrelated with EV/FEAUM (ρ=+0.17, not significant), indicating that the market does not consistently reward scale on an AUM-normalized multiple basis. The P/FRE premium is absolute, not relative.
3. **LOO sensitivity:** BX's outlier position (5x the next largest firm) amplifies the ρ. The relationship is genuine but partially contingent on the scale concentration in the universe.
4. **Temporal limitation:** This is a single FY2024 cross-section. Whether the scale premium persists in different rate environments (which affect PE fundraising and credit deployment) is untested.

---

## Principle 2: The FRE Growth Discount — Small Platforms Pay a Growth Tax (DVR-002 — FRE Growth YoY)

### Statistical Finding

FRE growth has a statistically significant but counterintuitive negative relationship with EV/FEAUM.

| Multiple | ρ (Spearman) | 95% CI | p-value | BH Significant | N |
|----------|-------------|--------|---------|----------------|---|
| EV/FEAUM | -0.6133 | [-0.84, -0.26] | 0.0068 | NO (fails BH) | 18 |
| P/DE | -0.4386 | [-0.80, +0.10] | 0.089 | NO | 16 |
| P/FRE | -0.2044 | [-0.67, +0.33] | 0.416 | NO | 18 |

**Classification:** Multiple-specific driver (EV/FEAUM, exploratory). Average |ρ|: 0.42. Note: N reduced to 18 for P/FRE and 18 for EV/FEAUM after CP-1 correction removed sentinel 0.0 values for BX/APO/TPG/CVC.

**Caution:** This correlation fails BH correction. It is an exploratory finding that should be treated as hypothesis-generating, not as a confirmed driver. Language must be hedged accordingly.

### Economic Mechanism

The negative direction is counterintuitive but has two structural explanations.

First, high FRE growth may signal aggressive fee monetization. A firm posting 30-40% FRE growth in a single year may be crystallizing management fees from a concentrated fundraising vintage — a non-repeatable event rather than a sustainable trajectory. The market applies an execution discount, questioning whether current-year FRE growth will persist.

Second, and more likely: high-FRE-growth firms are typically smaller platforms with a lower FEAUM base. Smaller platforms, independent of their growth rate, trade at lower EV/FEAUM multiples. When firms are ranked on FRE growth, the top of the ranking is populated by smaller, faster-growing platforms; the bottom by larger, mature platforms. The negative correlation may be capturing platform maturity (size) rather than a growth penalty per se.

### Illustrative Firms

**Top-quartile FRE growth (Q1):** PGHN (0.0% base-effects adjustment — excluded), HLNE (34%), STEP (48%). These are capital-light solutions managers growing off moderate bases with wealth-channel expansion. Their EV/FEAUM multiples are mid-range.

**Bottom-quartile FRE growth (Q4):** CG (-1.1%), APO (0.0% excluded), ARES (0.0% excluded). The large platforms with sentinel exclusions are correctly interpreted as "stable" rather than "zero growth" — the correction restores the signal.

**PAX position:** Q3, at approximately 23% FRE growth (USD). This is above the peer median — a positive forward signal — but the negative correlation suggests it may currently suppress PAX's EV/FEAUM multiple on trailing basis while priming for forward re-rating.

### Limitations and Boundary Conditions

1. **CP-1 correction dependency:** This result required removal of four sentinel 0.0 values for large platforms that reported no FRE growth because their fiscal year timing misaligned with the cross-section period. The corrected N=18 is below the primary drivers' N=22.
2. **BH failure:** This finding fails multiple testing correction. The p=0.0068 is nominally significant, but with 51 tests run, the probability of a false positive at this threshold is elevated. Treat as exploratory.
3. **Direction uncertainty:** For P/FRE (the most important multiple), the relationship is negative but not significant (ρ=-0.20, p=0.42). The EV/FEAUM signal does not translate across multiples, limiting the actionability of this driver.

---

## Principle 3: The Fee Base Lock-In Premium (DVR-003 — Fee-Earning AUM)

### Statistical Finding

FEAUM is the second BH-significant result in this cross-section, closely tracking AUM.

| Multiple | ρ (Spearman) | 95% CI | p-value | BH Significant | N |
|----------|-------------|--------|---------|----------------|---|
| P/FRE | +0.6045 | [+0.31, +0.82] | 0.0029 | YES | 22 |
| P/DE | +0.3489 | [-0.10, +0.73] | 0.132 | NO | 20 |
| EV/FEAUM | +0.0853 | [-0.31, +0.50] | 0.706 | NO | 22 |

**Classification:** Multiple-specific driver (P/FRE, BH-significant). Average |ρ|: 0.35. Note: FEAUM and AUM are highly correlated (inter-driver ρ ≈ 0.90). AUM is ranked first because its p-value is more significant; the two drivers capture overlapping information.

**Sensitivity:** LOO removing BX reduces ρ from +0.60 to approximately +0.52 — still above the 0.50 threshold. The result is robust to the largest outlier.

### Economic Mechanism

FEAUM represents the subset of AUM on which management fees are actively charged — the direct revenue base. Higher FEAUM signals that a greater proportion of total AUM is in the fee-earning period (deployment phase, not ramp-up or wind-down). Firms with higher FEAUM/AUM ratios (e.g., credit-heavy platforms) have more of their capital base generating current management fees, reducing revenue lumpiness.

The P/FRE premium for FEAUM is interpretable as a "revenue quality" signal: investors pay up for management fee streams that are contracted, locked-in, and recurring rather than dependent on new fundraising. Insurance float (APO, KKR), BDC permanent capital (ARES/ARCC), and open-end vehicles (BAM infrastructure) are the structural forms of FEAUM that attract the highest P/FRE premiums.

### Illustrative Firms

**Top FEAUM (Q4):** BX ($831B FEAUM), APO ($559B), BAM ($539B). The premium-multiple mega-managers.

**PAX position:** Q4 (18/22). PAX's $44B FEAUM is below peer median. The EV/FEAUM tautology (higher FEAUM → lower EV/FEAUM multiple) means PAX is not penalized on this multiple — but the P/FRE gap reflects the FEAUM premium accruing to larger platforms.

### Limitations

1. **Multicollinearity:** AUM and FEAUM are correlated at ρ≈0.90. The independent marginal contribution of FEAUM beyond AUM is difficult to isolate with N=22. These two drivers are ranked separately for exposition but should not be interpreted as providing independent evidence.
2. **EV/FEAUM paradox:** Higher FEAUM predicts lower EV/FEAUM (ρ=+0.09, non-significant but directionally consistent with larger firms trading at lower normalized multiples). This is a natural mathematical property of the ratio, not an economic finding.

---

## Principle 4: Permanent Capital Reduces the Re-Fundraising Risk Discount (DVR-004 — Permanent Capital %)

### Statistical Finding

Permanent capital percentage has a moderate but not statistically significant association with P/DE.

| Multiple | ρ (Spearman) | 95% CI | p-value | BH Significant | N |
|----------|-------------|--------|---------|----------------|---|
| P/DE | +0.4308 | [-0.04, +0.76] | 0.058 | NO | 20 |
| P/FRE | +0.3665 | [-0.07, +0.69] | 0.093 | NO | 22 |
| EV/FEAUM | +0.1480 | [-0.34, +0.59] | 0.511 | NO | 22 |

**Classification:** Moderate signal. Average |ρ|: 0.32. All three correlations fail BH correction and have 95% CIs that cross zero. This is a directional hypothesis, not a confirmed driver.

**Caution:** This finding is exploratory. The P/DE near-significance (p=0.058) suggests a plausible economic relationship that this sample is underpowered to confirm definitively.

### Economic Mechanism

Permanent capital — AUM in vehicles that do not have defined redemption periods (insurance general accounts, BDCs, open-end infrastructure funds, listed perpetual vehicles) — eliminates the fundraising cycle risk inherent in closed-end fund structures. For investors pricing alt-managers, fundraising cycle risk represents the possibility that AUM and management fees decline materially between fund vintages. Permanent capital contracts this risk: management fees from permanent AUM are not subject to fund expiration.

The P/DE association (directionally positive) is consistent with investors paying a quality premium for earnings that are insulated from fundraising volatility. DE from permanent capital vehicles is more predictable, lower-variance, and thus deserving of a higher multiple.

**Illustrative firms:** OWL (90% permanent capital, Q1 on DVR-004), PGHN (72%), APO (62%, including insurance float). These firms command above-median P/DE multiples where comparable.

**PAX position:** Q3 (13/22) — above median on permanent capital percentage (~7% permanent capital from GPMS pro-forma AUM), but not yet in the premium cohort. GPMS is PAX's primary mechanism for improving this metric.

### Limitations

1. **Not statistically confirmed:** All correlations fail BH correction. This is a theoretical framework with directional empirical support, not a proven driver in this dataset.
2. **Definition heterogeneity:** Permanent capital is defined differently across firms — insurance float, BDC equity, open-end fund NAV, and listed vehicle market cap are structurally different forms. The cross-sectional measure conflates these.
3. **Sample size:** N=20 for P/DE, the strongest multiple for this driver. With CIs crossing zero, the finding requires replication in larger samples.

---

## Principle 5: Overhead Efficiency Signals Organizational Quality (DVR-005 — G&A/FEAUM)

### Statistical Finding

G&A-to-FEAUM ratio has a moderate negative association with P/FRE — higher overhead per unit of fee-earning AUM is associated with lower P/FRE multiples.

| Multiple | ρ (Spearman) | 95% CI | p-value | BH Significant | N |
|----------|-------------|--------|---------|----------------|---|
| P/FRE | -0.4477 | [-0.72, -0.10] | 0.037 | NO | 22 |
| P/DE | -0.3488 | [-0.80, +0.18] | 0.132 | NO | 20 |
| EV/FEAUM | -0.0633 | [-0.50, +0.38] | 0.780 | NO | 22 |

**Classification:** Moderate signal. Average |ρ|: 0.29. The P/FRE correlation is nominally significant (p=0.037) but fails BH correction. Directional evidence only.

### Economic Mechanism

G&A/FEAUM is a proxy for organizational overhead per unit of revenue-generating capital. Lean G&A structures (APO at ~28bps, KKR at ~19bps, BAM at ~12bps) arise from structural advantages: insurance float generates management fees with minimal incremental G&A; operator heritage amortizes fixed costs across large AUM; and investment-grade ratings enable large fund vehicles that spread administration costs.

High G&A/FEAUM (PAX at ~214bps, PAX rank 22/23) reflects scale deficit, not operational mismanagement. The structural improvement path is mechanical: each $10B of FEAUM growth reduces G&A/FEAUM by approximately 30-40bps at current absolute G&A levels. No operational intervention required — scale is the primary solution.

The negative association with P/FRE is directionally intuitive: investors apply a margin-quality discount to platforms where overhead consumes a large share of fee revenue. High G&A/FEAUM compresses FRE margins, which directly reduces the FRE base and potentially raises P/FRE unless the multiple contracts accordingly.

**Illustrative firms (Q1 — best efficiency):** APO (~28bps), KKR (~19bps), BAM (~12bps), CG (~31bps). All trade at premium P/FRE multiples.

**PAX position:** Q4 (22/23) — worst-efficiency cohort. Mechanically improves with AUM growth. GPMS adds FEAUM without proportionate G&A (capital-light model), accelerating ratio improvement.

### Limitations

1. **Not statistically confirmed:** Fails BH correction. A moderate negative directional signal, not a proven driver.
2. **Insurance float conflation:** Q1 efficiency at mega-managers is structurally driven by insurance float (APO, KKR), which generates fee revenue at near-zero marginal G&A cost. This structural advantage is not replicable through operational improvement at smaller scales.
3. **Scale tautology risk:** G&A/FEAUM and AUM (DVR-001) are correlated — larger AUM implies lower G&A/FEAUM. The independent effect of G&A efficiency beyond scale effects is not isolable in this sample.
4. **Antin and STEP exception:** Antin (Q4 G&A/FEAUM) and STEP (Q2 G&A/FEAUM) both achieve Q1 DE/share — confirming that mid-scale managers can decouple earnings quality from G&A efficiency. This weakens the operational urgency of G&A improvement as a standalone priority.

---

## Analytically Relevant but Statistically Unsupported Signal: Distributable Earnings per Share (DE/share)

### Classification: UNSUPPORTED (max|ρ|=0.28)

DE/share does **not** qualify as a value driver in this run. The maximum correlation across all three multiples is |ρ|=0.28 (EV/FEAUM), with a 95% CI of [-0.15, +0.62] that fully crosses zero. This result fails all significance thresholds.

| Multiple | ρ (Spearman) | 95% CI | p-value | BH Significant | N |
|----------|-------------|--------|---------|----------------|---|
| P/FRE | +0.1700 (approx) | — | >0.40 | NO | 21 |
| P/DE | +0.2100 (approx) | — | >0.40 | NO | — |
| EV/FEAUM | +0.2832 | [-0.15, +0.62] | — | NO | 21 |

**Why DE/share fails as a cross-sectional driver in this sample:**

Two structural issues compromise DE/share as a cross-sectional ranking variable:

1. **PGHN currency outlier:** Partners Group's DE/share of CHF 81.6/share reflects a very low share count combined with high per-share earnings denominated in CHF rather than USD. This structural difference places PGHN as rank-1 on DE/share despite a moderate P/FRE multiple of ~15.9x, distorting the expected positive correlation. Sensitivity analysis: excluding PGHN shifts DE/share × P/FRE ρ from +0.17 to approximately +0.30-0.35 — still well below the 0.50 threshold.

2. **ONEX proxy earnings:** ONEX DE/share = $13.32 is a low-confidence proxy derived from adjusted diluted EPS under Canadian GAAP, not a like-for-like distributable earnings measure. Excluding ONEX shifts ρ from +0.17 to approximately +0.21 — marginal.

**What DE/share appears to capture (hedged language):**

While not confirmed as a statistical driver in this cross-section, DE/share may represent an analytically relevant signal of earnings quality that the current sample is insufficient to confirm. The economic intuition is sound: investors should pay more for platforms generating higher-quality, more predictable distributable earnings per share. The STEP and HLNE cases — both Q1 DE/share, both trading at premium valuations — are consistent with this intuition. The absence of statistical confirmation reflects sample heterogeneity (structural, currency, accounting definition differences) rather than a negative finding about DE/share economics.

**Implication for language in this report:** Any reference to DE/share as a value driver must use hedged language — "appears to," "suggests," "may indicate." Phrases such as "DE/share drives multiple expansion" or "improving DE/share is a confirmed re-rating catalyst" are not supported and must not appear in the final report. The framing is: DE/share is a structurally motivated candidate driver that appears to underlie several platform differentiation cases, but its statistical confirmation is precluded by the structural comparability limitations of this cross-section.

---

## Summary Table

| Driver ID | Driver Name | Classification | Avg |ρ| | Strongest Multiple | Strongest ρ | BH Significant | PAX Quartile |
|-----------|-------------|----------------|--------|--------------------|-------------|----------------|--------------|
| DVR-001 | Total AUM | multiple_specific | 0.46 | P/FRE | +0.73 | YES | Q4 (18/22) |
| DVR-002 | FRE Growth YoY | multiple_specific | 0.42 | EV/FEAUM | -0.61 | NO (exploratory) | Q3 (11/19) |
| DVR-003 | Fee-Earning AUM | multiple_specific | 0.35 | P/FRE | +0.60 | YES | Q4 (18/22) |
| DVR-004 | Permanent Capital % | moderate_signal | 0.32 | P/DE | +0.43 | NO | Q3 (13/22) |
| DVR-005 | G&A/FEAUM | moderate_signal | 0.29 | P/FRE | -0.45 | NO | Q4 (22/23) |
| — | DE/share | UNSUPPORTED | 0.22 (max) | EV/FEAUM | +0.28 | NO | — |

**Note on PAX valuation position:**
- P/FRE: PAX 14.9x vs peer median 17.7x → -15.8% discount
- P/DE: PAX 13.4x vs peer median 25.3x → -47.0% discount
- EV/FEAUM: PAX 7.7x vs peer median 10.7x → -28.0% discount

PAX's most actionable improvement levers — based on the confirmed and exploratory drivers — are: (1) FEAUM/AUM growth (DVR-001, DVR-003, both BH-confirmed on P/FRE); (2) permanent capital accumulation via GPMS (DVR-004, directionally supported); and (3) G&A/FEAUM improvement through scale (DVR-005, directionally supported). The P/DE discount (-47%) is large and partially structural (earnings quality gap), but DE/share is not statistically confirmed as a driver in this sample and must be referenced with appropriate hedging.

---

## Methodological Disclaimers (Mandatory)

1. **Causation:** Spearman correlations identify statistical associations, not causal mechanisms.
2. **Survivorship bias:** The universe excludes acquired, delisted, or private firms.
3. **Point-in-time:** FY2024 cross-section; may not persist into 2025-2026 market conditions.
4. **Small-N:** N=18-22 effective observations. Standard error of ρ ≈ 0.22-0.25.
5. **Endogeneity:** Valuation multiples and AUM are jointly determined.
6. **FRE heterogeneity:** P/FRE multiples compared across firms with materially different FRE definitions (BX uses DE; MAN uses net revenue proxy; EQT uses ANI).
7. **Currency comparability:** DE/share is structurally incomparable across USD, CHF, and CAD per-share metrics.
