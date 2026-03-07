# Value Creation Principles — Valuation Driver Analysis

**Pipeline:** VDA | **Stage:** VD-P1 | **Company:** Patria Investments Limited (PAX)
**Run:** 2026-03-07-run2 | **Generated:** 2026-03-07

---

## 1. Stable Value Drivers

### 1.1 DVR-001: Fee-Earning AUM (Scale)

**Statistical Finding:** Fee-Earning AUM exhibits the strongest and most consistent positive association with valuation multiples across the alternative asset management peer universe. Spearman rho ranges from +0.63 to +0.76 across the three valuation multiples, with an average absolute rho of 0.6949. The P/FRE correlation (rho = +0.765, 95% CI [+0.333, +0.942], BH-adjusted p = 0.0255) is the only correlation in the entire dataset that survives the strictest Bonferroni correction (raw p = 0.0003). The EV/FEAUM correlation (rho = +0.629, 95% CI [+0.157, +0.839], raw p = 0.009) and P/DE correlation (rho = +0.691, raw p = 0.058, n = 8) further confirm the pattern. Confidence class: moderate confidence. Leave-one-out analysis confirms robustness — no single firm drives the result (LOO range 0.112). As the scale variable itself, FEAUM is not tested for independence; it is the benchmark against which other drivers are tested.

**Economic Mechanism:** Scale in alternative asset management generates compounding returns through multiple reinforcing channels. Larger FEAUM produces greater absolute fee revenue against a cost structure that grows sub-linearly (operating leverage). Brand recognition attracts the largest LP mandates, which fund proprietary investments that generate differentiated returns, which in turn attract more capital. Scale enables entry into distribution channels with minimum AUM thresholds (insurance partnerships, sovereign wealth fund co-investments, wirehouse platform approvals). Larger platforms can afford dedicated wealth distribution teams, technology infrastructure, and geographic expansion that smaller competitors cannot justify. The market rewards scale with higher multiples because it assigns greater confidence to the durability and growth trajectory of larger fee streams.

**Illustrative Firms:**
- **Blackstone (BX):** FEAUM $921.7B (Q1, rank 1/23). P/FRE premium reflects the industry's largest and most diversified fee base. Scale enables BREIT, BCRED, BXPE, and $43B annual wealth fundraising, which appears to represent approximately 50% of private wealth alternative revenue (company IR estimate, not independently verified). (PS-VD-001, PS-VD-002)
- **Apollo (APO):** FEAUM $709.0B (Q1, rank 2/23). Origination-led model generates $228B annual inflows — scale is self-reinforcing through the Athene closed-loop deployment channel. Apollo characterizes its origination platform as a "parallel bank" (company IR narrative, not independently verified); the verified data point is the $228B origination volume. (PS-VD-009, PS-VD-010)
- **KKR:** FEAUM $604.0B (Q1, rank 3/23). Triple-engine model (FRE + insurance + balance sheet) demonstrates that scale enables earnings diversification unavailable to smaller firms. (PS-VD-005, PS-VD-006)

**Limitations and Boundary Conditions:**
- Total AUM (DVR-004) appears as a separate stable driver (avg |rho| = 0.59) but is **confounded** by FEAUM. Partial correlation collapses from ~0.69 to ~0.12 after controlling for FEAUM (rho between Total AUM and FEAUM = 0.96). Total AUM adds no incremental explanatory power beyond FEAUM.
- The scale-valuation relationship may be concave (diminishing returns). The difference in P/FRE between a $100B and $400B platform appears larger than the difference between $400B and $900B, though the sample is too small to formally test non-linearity.
- Survivorship bias: the universe includes only currently listed firms. Firms that failed or were acquired may have had different scale-valuation dynamics.
- Reverse causality is likely present: high-valuation firms raise capital more cheaply, accelerating AUM growth.

---

### 1.2 DVR-002: Earnings per Share (GAAP)

**Statistical Finding:** Earnings per Share exhibits the highest average absolute Spearman rho (0.7286) of any driver, making it the strongest single predictor of valuation multiples. The EV/FEAUM correlation (rho = +0.750, 95% CI [+0.283, +0.911], BH-adjusted p = 0.0408) survives BH correction. The P/FRE correlation (rho = +0.665, 95% CI [+0.232, +0.927], raw p = 0.013, n = 13) and P/DE correlation (rho = +0.771, raw p = 0.072, n = 6) further support the pattern. Confidence class: moderate confidence. Leave-one-out analysis confirms robustness (LOO range 0.148). Critically, EPS retains its signal after controlling for scale: partial rho drops by only 0.04-0.07 after partialing out FEAUM, confirming that EPS captures information about valuation **independent of firm size**. This makes EPS the most robust driver in the dataset.

**Economic Mechanism:** EPS captures the per-share economic value that ultimately accrues to equity holders. Unlike FEAUM (which measures the fee base) or FRE margin (which measures efficiency), EPS integrates all earnings sources — management fees, performance fees, insurance economics, balance sheet returns, and non-fee income — into a single per-share metric. The market rewards higher EPS with higher multiples because EPS directly determines the investor's claim on the firm's economic output. The independence from scale is economically intuitive: a smaller firm with superior per-share earnings quality (through higher fee rates, better cost discipline, or diversified earnings streams) can command a premium multiple relative to a larger but less profitable competitor. EPS also implicitly penalizes dilution — firms with large share counts and low per-share economics receive lower multiples even if aggregate earnings are substantial.

**Illustrative Firms:**
- **Partners Group (PGHN):** EPS CHF 48.83 (Q1, rank 1/16). Highest EPS in the peer group by a wide margin. The direct investing model captures the full value chain, and the smaller share count concentrates economics per share. Q1 EPS is the primary contributor to PGHN's premium valuation despite Q2 FEAUM. (PS-VD-030, PS-VD-031)
- **3i Group (III):** EPS GBP 8.14 (Q1, rank 2/16). A non-obvious peer — 3i's balance sheet investing model (similar to a permanent capital vehicle) generates high EPS despite only $8.8B FEAUM (Q4). Demonstrates that per-share economics can drive valuation independent of scale.
- **Apollo (APO):** EPS $5.54 (Q1, rank 3/16). Dual-engine earnings power (FRE from asset management + SRE from Athene retirement services) generates strong per-share economics. (PS-VD-010, PS-VD-011)

**Limitations and Boundary Conditions:**
- GAAP EPS is subject to non-cash distortions (amortization of acquired intangibles, equity compensation, mark-to-market adjustments). StepStone's negative GAAP EPS (-$1.55) despite positive adjusted ANI (+$0.65/share) and record AUM growth illustrates this limitation; the FRE margin (37%, Q4) is a more reliable indicator of StepStone's structural challenge.
- Currency effects distort cross-border comparisons (PGHN reports in CHF, EQT in EUR, PAX in USD-translated BRL).
- EPS sample size is smaller (n = 6-14 across multiples) than FEAUM (n = 17-19), reducing statistical power.
- The EPS-valuation relationship may partly reflect a tautology: P/FRE and P/DE have price in the numerator, and firms with higher EPS tend to have higher prices.

---

### 1.3 DVR-003: Fee-Related Earnings Margin (Multiple-Specific Driver)

**Statistical Finding:** Fee-Related Earnings Margin is classified as a **multiple-specific driver** — it exceeds the rho > 0.5 threshold for exactly one multiple (EV/FEAUM) but not for P/FRE or P/DE. The EV/FEAUM correlation is strong (rho = +0.708, 95% CI [+0.277, +0.955], BH-adjusted p = 0.0382, n = 17). However, the P/FRE association (rho = +0.404, raw p = 0.087, n = 19) falls below the 0.5 threshold, and the P/DE association (rho = +0.515, raw p = 0.128, n = 10) is moderate but not significant. Average absolute rho: 0.5424. Confidence class: moderate confidence. FRE Margin retains an independent signal after controlling for scale, though it is partially attenuated: the EV/FEAUM partial rho drops from +0.61 to +0.41, indicating that roughly one-third of the FRE margin signal is attributable to scale (larger firms tend to have higher margins due to operating leverage). The remaining +0.41 partial correlation represents a genuine, independent efficiency signal. The multiple-specific classification means FRE Margin is most relevant when valuing the fee base (EV/FEAUM) rather than as a universal predictor of all valuation multiples.

**Economic Mechanism:** FRE margin measures how efficiently a firm converts management fee revenue into distributable earnings. Higher FRE margins indicate superior operating leverage — the ability to grow revenue faster than costs. The EV/FEAUM multiple is particularly sensitive to FRE margin because EV/FEAUM is essentially a price-per-dollar-of-AUM metric; firms that extract more earnings from each dollar of AUM naturally command a higher price per dollar. The independent efficiency signal (partial rho = +0.41) reflects structural advantages beyond scale: permanent capital models (Blue Owl, 100% permanent capital) eliminate fundraising costs; direct investing models (Partners Group) eliminate sub-advisory fees; platform businesses (Blackstone) amortize shared infrastructure across multiple strategies. The market rewards margin quality because it indicates earnings durability — high-margin firms can absorb revenue shocks without proportional earnings declines.

**Illustrative Firms:**
- **Blackstone (BX):** FRE margin 71.3% (Q1, rank 1/23). Industry-leading margin reflects operating leverage at the industry's largest scale. Perpetual capital vehicles (48% of FEAUM) provide margin stability. (PS-VD-001, PS-VD-002)
- **KKR:** FRE margin 69.0% (Q1, rank 2/23). Second-highest margin in the peer group. Multi-platform model and insurance economics contribute additional earnings streams beyond traditional fee margins. (PS-VD-005, PS-VD-006)
- **Blue Owl (OWL):** FRE margin 62.0% (Q1, rank 3/23). Remarkable given the firm's rapid M&A integration cycle. The 100% permanent capital structure eliminates fundraising costs and provides structural margin advantage. (PS-VD-018, PS-VD-019)
- **PAX:** FRE margin 58.9% (Q1, rank 5/23). **PAX's strongest competitive positioning.** Top-quartile efficiency comparable to mega-cap platforms despite Q4 scale. This is the single strongest data point supporting PAX's valuation case.

**Limitations and Boundary Conditions:**
- FRE is a non-GAAP metric with material definitional differences across firms. Pre-tax vs. after-tax treatment, inclusion/exclusion of equity-based compensation, and European equivalents (EQT's "Fee-related EBITDA," CVC's "Management Fee Earnings") introduce measurement error.
- The P/FRE partial correlation reverses sign (from +0.28 to -0.31) after controlling for FEAUM, indicating that the FRE margin-P/FRE association is driven entirely by scale confounding for that specific multiple. Only the EV/FEAUM association represents an independent efficiency signal.
- Credit-dominated platforms (Ares, 41.7%) have structurally lower FRE margins than PE-centric or direct investing models because credit management fees are lower per dollar of AUM. Low FRE margin does not necessarily indicate operational inefficiency — it may reflect business mix.

---

## 2. Moderate Signals

### 2.1 DVR-005: Distributable Earnings per Share

**Statistical Finding:** DE/share exhibits a moderate average absolute rho of 0.5505, with a notably strong EV/FEAUM association (rho = +0.833, raw p = 0.010, n = 8) that does not survive BH correction due to the small sample size. The P/FRE (rho = +0.318, n = 11) and P/DE (rho = +0.500, n = 8) associations are weaker. Confidence class: not significant after BH correction. Independence from scale is mixed due to insufficient sample sizes for partial correlation testing (n = 7-10).

**Economic Mechanism:** DE/share is an industry-specific metric that strips out non-cash items from GAAP EPS, providing a cleaner measure of cash-available-for-distribution earnings. The strong EV/FEAUM signal suggests that the market prices de facto cash generation capacity when valuing the fee base. However, the small sample and failure to survive BH correction mean this signal requires verification with larger datasets.

**Illustrative Firms:**
- **Blackstone (BX):** DE/share $5.57 (Q1). Highest distributable earnings per share, reflecting the combination of scale and margin leadership.
- **PAX:** DE/share $1.27 (Q2, rank 7/14). Mid-pack positioning — better than scale position would suggest, reflecting the high FRE margin.

### 2.2 DVR-007: FRE Growth, Year-over-Year

**Statistical Finding:** FRE Growth exhibits a weak-to-moderate average absolute rho of 0.2601. The P/FRE association (rho = +0.334, raw p = 0.162, n = 19) and P/DE association (rho = +0.430, raw p = 0.215, n = 10) are moderate but not significant. The EV/FEAUM association is near zero (rho = -0.016). Confidence class: not significant. Not tested in partial correlations.

**Economic Mechanism:** FRE growth captures the momentum of a firm's earnings trajectory. The weak signal is surprising — one might expect high-growth firms to command premium multiples. The disconnect may reflect that the market prices the *level* of earnings more than the *rate of change*, or that growth sustainability is difficult to assess from a single year's data. The Vinci Compass cautionary case (63% FRE growth, Q1 on DVR-007, but Q4 FRE margin of 30.4%) demonstrates that growth from a low base does not substitute for earnings quality.

**Illustrative Firms:**
- **Vinci Compass (VINP):** FRE growth 63% (Q1, rank 1/22). Highest growth but lowest FRE margin — growth without margin quality does not drive premium valuations.
- **PAX:** FRE growth 19% (Q2, rank 9/22). Solid growth that preserves FRE margin quality.

### 2.3 DVR-006: Credit Percentage of AUM

**Statistical Finding:** Credit % exhibits a moderate average absolute rho of 0.3948, with the strongest association in P/FRE (rho = +0.476, raw p = 0.046, n = 18). Confidence class: not significant after BH correction. Critically, Credit % is **confounded by FEAUM** — the raw positive associations disappear after controlling for scale, suggesting that credit-heavy firms tend to be larger rather than that credit exposure per se drives valuation.

**Economic Mechanism:** The apparent association between credit allocation and valuation reflects a structural correlation: the largest alternative managers (BX, APO, KKR, ARES) have systematically built large credit platforms because credit is the most scalable asset class (higher deployment velocity, larger ticket sizes, bank disintermediation tailwinds). Credit exposure is therefore a proxy for scale rather than an independent valuation driver.

**Limitation:** This finding does not imply that credit platform expansion is value-neutral — it implies that the value comes through the FEAUM channel (credit grows FEAUM) rather than through an independent credit premium.

---

## 3. Cross-Driver Synthesis

The three stable value drivers form a coherent framework:

1. **Scale (FEAUM)** establishes the fee base — the raw material from which earnings are produced. It is the dominant factor, with the strongest statistical signal.

2. **Efficiency (FRE Margin)** determines how much of the fee base converts to earnings. It provides an independent signal beyond scale, particularly for the EV/FEAUM multiple.

3. **Per-share economics (EPS)** integrates all earnings sources into the metric that ultimately determines equity value. It retains the strongest independence from scale, confirming that profitability matters beyond firm size.

For PAX specifically: the firm ranks Q1 on FRE Margin (58.9%, rank 5/23) but Q4 on FEAUM ($40.8B, rank 19/23) and Q3 on EPS ($0.54, rank 12/16). The scale disadvantage is the primary explanation for PAX's valuation discount (P/FRE 10.5x vs. peer median ~20x). The FRE margin strength is a genuine competitive advantage, but it cannot fully compensate for the scale deficit because FEAUM is the stronger driver statistically. The path to multiple expansion requires growing FEAUM while defending FRE margin.

---

## Appendix: Statistical Reference

| Driver | DVR ID | Avg |rho| | Classification | BH Significant? | Independent of Scale? | PAX Quartile |
|--------|--------|-----------|----------------|--------------|----------------------|-------------|
| EPS (GAAP) | DVR-002 | 0.729 | Stable driver | Yes (EV/FEAUM) | Yes | Q3 |
| FEAUM | DVR-001 | 0.695 | Stable driver | Yes (P/FRE) | N/A (is scale) | Q4 |
| Total AUM | DVR-004 | 0.590 | Stable driver* | Yes (P/FRE) | No (confounded) | Q4 |
| DE/share | DVR-005 | 0.550 | Moderate signal | No | Mixed | Q2 |
| FRE Margin | DVR-003 | 0.542 | Multiple-specific (EV/FEAUM only) | Yes (EV/FEAUM) | Partially | Q1 |
| Credit % | DVR-006 | 0.395 | Moderate signal | No | No (confounded) | Q2 |
| FRE Growth YoY | DVR-007 | 0.260 | Moderate signal | No | N/A | Q2 |
| Mgmt Fee Rate | DVR-008 | 0.183 | Moderate signal | No | N/A | Q3 |

*Total AUM classified as stable driver on raw correlations but confounded by FEAUM; partial rho collapses to ~0.12.

**Methodology:** Spearman rank correlations with 1,000-iteration bootstrap 95% CIs. Benjamini-Hochberg FDR correction at q = 0.10 across 51 full-sample tests. Partial correlations controlling for FEAUM. Leave-one-out robustness testing. Full methodology documented in `3-analysis/statistical_methodology.md`.
