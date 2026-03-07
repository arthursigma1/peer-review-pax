---
name: review-analysis
description: Deploy review agents on any completed VDA analysis to identify improvement opportunities. Usage: /review-analysis TICKER [--report path]
---

# Review Analysis

Deploy two specialized review agents on a completed Valuation Driver Analysis to surface gaps in methodology, data coverage, and analytical conclusions.

## Usage

```
/review-analysis TICKER                      # review latest VDA run for TICKER
/review-analysis TICKER --report /path       # review a specific report file
```

## Step 0: Parse Arguments

Extract from the user's input:
- `TICKER` (required) — e.g., `PAX`, `BX`, `KKR`
- `--report /path` (optional) — override default report location

Set `TICKER_LOWER` to the lowercase version of `TICKER`.

If no TICKER is provided, ask the user for one.

## Step 1: Locate Files

Find all VDA output files for this ticker.

**Default path:** `data/processed/{TICKER}/`

If `--report path` was provided, resolve file paths relative to that path's parent directory.

Search for the following files (note: they may be in a dated subdirectory like `data/processed/{TICKER}/YYYY-MM-DD/`):

```
peer_vd_a0_universe.json
peer_vd_a1_metrics.json
peer_vd_a2_raw_data.json
peer_vd_a3_standardized.json
peer_vd_a4_correlations.json
peer_vd_a4b_methodology.md
peer_vd_a5_driver_ranking.json
peer_vd_b0_sources.json
peer_vd_b1_strategies.json
peer_vd_b2_actions.json
peer_vd_c1_final_set.json
peer_vd_d1_platform_deepdives.json
peer_vd_d2_asset_class_deepdives.json
peer_vd_p1_value_principles.md
peer_vd_p2_platform_playbook.json
peer_vd_p3_asset_class_playbooks.json
peer_vd_final_report.html
```

If the dated subdirectory format is used, use the most recent date directory (sort alphabetically descending and take the first match).

Display to the user:
- Which files were found
- Which files are missing (if any)
- The base path being reviewed

If the final report (`peer_vd_final_report.html`) is not found and no `--report` override was provided, ask: "Could not locate peer_vd_final_report.html. Please specify the report path with --report or confirm the TICKER is correct."

Set `BASE_PATH` to the directory containing the located files.

## Step 2: Spawn Review Agents

Spawn two agents in parallel:

### Agent: methodology-reviewer

Spawn with Agent tool (subagent_type: general-purpose, name: "methodology-reviewer"):

Instructions:
> You are the methodology-reviewer for the Valuation Driver Analysis review.
>
> **Your task:** Critically review the statistical methodology and data quality of a completed VDA analysis. Identify gaps, weaknesses, and improvement opportunities.
>
> **Files to read (in order):**
> 1. `{BASE_PATH}/peer_vd_a4b_methodology.md` — statistical documentation
> 2. `{BASE_PATH}/peer_vd_a4_correlations.json` — correlation results
> 3. `{BASE_PATH}/peer_vd_a3_standardized.json` — standardized data
> 4. `{BASE_PATH}/peer_vd_a0_universe.json` — peer universe
> 5. `{BASE_PATH}/peer_vd_a1_metrics.json` — metric taxonomy
> 6. `{BASE_PATH}/peer_vd_a2_raw_data.json` — raw data (check coverage)
> 7. `{BASE_PATH}/peer_vd_c1_final_set.json` — final peer set selection
> 8. Design doc: `docs/plans/2026-03-06-valuation-driver-analysis-design.md`
>
> **Review dimensions:**
>
> **1. Statistical methodology**
> - Are Spearman coefficients computed correctly? Is the sample size (N) stated for each correlation?
> - Are bootstrap confidence intervals present for all significant correlations? Do any significant correlations have CIs that include zero?
> - Is the Bonferroni correction applied to all ~45 hypothesis tests? Are corrected p-values reported?
> - Are the mandatory disclaimers from the design doc reproduced verbatim in VD-A4b?
> - Is the leave-one-out sensitivity analysis present? Are any findings flagged as driven by a single influential observation?
> - Is the temporal stability check (FY1 vs. FY2) present? Are any correlations flagged as unstable?
> - Are multicollinear driver pairs (ρ > 0.7 between drivers) identified and documented?
>
> **2. Data coverage**
> - What is the actual metric coverage rate (% of metrics populated per firm)?
> - Which firms have the lowest coverage? Is coverage < 60% for any firm included in the final set?
> - Are all three valuation multiples (P/FRE, P/DE, EV/FEAUM) populated for all final-set firms?
> - Are there any metrics marked "low coverage" (< 15 of ~25 firms) that were used as if fully reliable?
> - Are there any metrics where FRE definition heterogeneity was not flagged but should have been?
>
> **3. Metric selection**
> - Are all required metric categories present (Earnings, Scale, Organic Growth, Mix, Efficiency, Fee Quality)?
> - Are any obviously relevant metrics missing for this industry (e.g., carry/performance fee dynamics, LP retention rate)?
> - Are market structure metrics (trading volume, passive ownership, free float) correctly excluded from correlation analysis?
> - Is the Asset class HHI calculated correctly (sum of squared proportions × 10,000)?
>
> **4. Peer selection logic**
> - Does VD-C1 document clear inclusion/exclusion rationale for every candidate?
> - Are any non-obvious peers surfaced by Track A ignored without explanation?
> - Is the final set within the 9–12 firm target? If not, is the deviation documented?
> - Are cautionary cases (bottom-quartile firms) included where instructive?
>
> **Output:** Write your findings to `{BASE_PATH}/peer_vd_review_methodology.md`
>
> Structure:
> ```markdown
> # Methodology Review
>
> ## Summary
> [2–3 sentence overall assessment]
>
> ## Critical Issues
> [Issues that materially affect the validity of the findings — must be addressed before the report is shared]
>
> ## Significant Gaps
> [Issues that reduce analytical quality but do not invalidate the findings]
>
> ## Minor Observations
> [Style, completeness, or presentation issues]
>
> ## Recommended Actions
> [Numbered list of specific actions to address critical issues and significant gaps]
> ```
>
> Be specific: cite the file and field where you found the issue. Do not write generic observations.

### Agent: results-reviewer

Spawn with Agent tool (subagent_type: general-purpose, name: "results-reviewer"):

Instructions:
> You are the results-reviewer for the Valuation Driver Analysis review.
>
> **Your task:** Critically review the analytical conclusions, insights, and strategic playbook of a completed VDA analysis. Identify missed insights, weak conclusions, and untapped analytical angles.
>
> **Files to read (in order):**
> 1. `{BASE_PATH}/peer_vd_final_report.html` — final report
> 2. `{BASE_PATH}/peer_vd_p1_value_principles.md` — value creation principles
> 3. `{BASE_PATH}/peer_vd_p2_platform_playbook.json` — platform strategic menu
> 4. `{BASE_PATH}/peer_vd_p3_asset_class_playbooks.json` — asset class playbooks
> 5. `{BASE_PATH}/peer_vd_d1_platform_deepdives.json` — platform deep-dives
> 6. `{BASE_PATH}/peer_vd_d2_asset_class_deepdives.json` — asset class deep-dives
> 7. `{BASE_PATH}/peer_vd_a5_driver_ranking.json` — driver ranking
> 8. `{BASE_PATH}/peer_vd_b2_actions.json` — peer actions catalog
>
> **Review dimensions:**
>
> **1. Missed insights**
> - Are there stable value drivers in VD-A5 that are not fully developed in VD-P1? Is the economic mechanism explained for each?
> - Are there peer actions in VD-B2 that do not appear in the platform strategic menu (VD-P2)? Unexploited evidence is a gap.
> - Are there patterns across multiple firms' actions that the synthesizer did not surface as a theme?
> - Are there cautionary cases (bottom-quartile firms) that should have been analyzed as negative examples but are absent?
>
> **2. Weak conclusions**
> - Are any transferable insights in VD-D1 stated as inference without a cited action (ACT-VD-NNN) or source (PS-VD-NNN)?
> - Are any strategic plays in VD-P2/P3 lacking observable metric impact evidence? Is the gap acknowledged?
> - Are there conclusions that directly contradict the mandatory statistical disclaimers (e.g., causal claims made from correlation data)?
> - Are value creation narratives internally consistent? Do they align with the quartile positions in VD-A5?
>
> **3. Data quality issues visible in the output**
> - Are there firms in the final report with obviously thin coverage (few actions, vague strategy profiles)?
> - Are there asset class verticals in VD-D2 covered superficially (fewer than 2 concrete winning strategies documented)?
> - Are there inconsistencies between firm profiles in VD-D1 and their stated AUM/strategy in VD-A0?
>
> **4. Untapped analytical angles**
> - Are there cross-firm patterns (e.g., firms that moved from one fund type to another and saw valuation re-rating) that are not synthesized?
> - Is the temporal dimension explored — do firms that improved on a stable driver over 3 years show valuation re-rating?
> - Are there vertical-specific drivers that were not surfaced because the overall correlation analysis averaged across all verticals?
> - Is the relationship between growth model type (organic vs. M&A) and valuation premium analyzed?
>
> **Output:** Write your findings to `{BASE_PATH}/peer_vd_review_results.md`
>
> Structure:
> ```markdown
> # Results Review
>
> ## Summary
> [2–3 sentence overall assessment of analytical quality]
>
> ## Critical Issues
> [Conclusions that are unsupported or contradict stated methodology — must be addressed]
>
> ## Missed Insights
> [Patterns or findings present in the data but not surfaced in the report]
>
> ## Analytical Gaps
> [Areas where evidence exists but analysis is incomplete]
>
> ## Suggested Additions
> [Specific analytical extensions that would increase actionability for the intended consumer]
> ```
>
> Be specific: cite the file, section, or field where you found the issue. Do not write generic observations.

## Step 3: Collect and Present Results

Wait for both review agents to complete.

Verify that both output files exist:
- `{BASE_PATH}/peer_vd_review_methodology.md`
- `{BASE_PATH}/peer_vd_review_results.md`

If either file is missing, check whether the agent completed (look for error messages). If the agent timed out or produced no output, re-dispatch with a focused prompt covering only the highest-priority review dimensions (statistical documentation for methodology; missed insights + weak conclusions for results).

Display a consolidated summary:

```
## Review Complete: {TICKER} Valuation Driver Analysis

### Methodology Review
[Paste Critical Issues and Significant Gaps sections]
Full review: {BASE_PATH}/peer_vd_review_methodology.md

### Results Review
[Paste Critical Issues and Missed Insights sections]
Full review: {BASE_PATH}/peer_vd_review_results.md
```

Offer next steps:
1. "Re-run specific pipeline stages to address critical issues"
2. "Commit review files to git"
3. "No further action needed"

If the user selects option 1, identify which VDA stage produced the relevant output and describe how to re-dispatch that specific agent via the `/valuation-driver` skill or direct Agent call.
