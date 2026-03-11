# Repository Drift Audit

This document records the key mismatches found in the partially-updated VDA repository and the fix applied in the PAX-first upgrade.

## 1. Mismatch Log

| File / location | Methodology said | Implementation / output did | Why it mattered | Severity | Exact fix required |
|---|---|---|---|---|---|
| `docs/valuation-driver-methodology.md`, statistical sections | Bonferroni was the primary discovery framework | Run artifacts switched to BH FDR q=0.10 | Statistical governance could silently drift between runs and reports | critical | Promote BH FDR q=0.10 to the single discovery framework, preserve Bonferroni only as confirmatory badge, and encode the rule in methodology, prompts, schemas, and report metadata |
| `docs/valuation-driver-methodology.md`, stable-driver language | `rho > 0.5` across all three multiples | Outputs treated partially-supported drivers as stable or allowed ad hoc exceptions | Driver labels could change between files without rule changes | critical | Define one exact stable-driver rule (`stable_v1_two_of_three`) and hard-fail any report that violates it |
| `src/tauri/src/components/AgentsOrg.tsx`, playbook instructions | Required operational realism fields existed in methodology | Runtime prompt only asked for metric impact, prerequisites, and risks | The strongest requested upgrade, execution realism, never actually entered the generator contract | critical | Rewrite playbook and target-lens instructions to require all PAX-first fields |
| `prompts/vda/claim_auditor.md` and `audit_cp3_playbook.json` | CP-3 should block missing mandatory fields and audit all claims | CP-3 sampled claims and passed outputs that omitted required fields | The audit looked stricter than it was | critical | Expand CP-3 scope, require exhaustive claim enumeration, and block schema failures |
| `src/tauri/src/components/AgentsOrg.tsx`, target-lens and report-builder inputs | Downstream agents should consume audit results | Neither agent received CP-3 audit artifacts | Corrected language could regress in the final report and target lens | critical | Feed `audit_cp3_playbook.json` and metadata into target-lens and report-builder |
| `docs/valuation-driver-methodology.md`, playbook neutrality | Final synthesis was neutral and target-company-specific only in an overlay | Actual outputs were already advisory for PAX | Repo language understated the real use case and caused design tension | major | Move to a PAX-first methodology with peer evidence preserved underneath |
| `src/tauri/src/components/AgentsOrg.tsx`, convergence logic | Top quartile peer logic dominated inclusion | Mega-cap peers could dominate conclusions without transferability penalties | PAX conclusions risked becoming a diluted mega-cap playbook | major | Add peer archetypes, matched-sample views, and transferability-aware convergence rules |
| `docs/valuation-driver-methodology.md`, FX handling | FX treatment was only partly specified | Outputs mixed translated and local-currency interpretations inconsistently | Cross-border growth and per-share comparisons could be misread | major | Add local-currency-first growth logic, `fx_delta`, `fx_material_flag`, and comparability notes |
| `docs/valuation-driver-methodology.md`, operational prerequisites | Operational prerequisites were mentioned but not consistently captured in source collection | Strategic actions mostly captured the visible action, not the hidden build work | Tech/ops burden and execution realism remained under-modeled | major | Add operational prerequisite fields, evidence class, source-bias tag, and inference flag to strategic actions |
| `docs/valuation-driver-methodology.md`, vertical analysis | Broad verticals were acceptable | Outputs still treated PE, Credit, and Solutions too monolithically | PAX-specific transferability depends on strategy sub-type, not headline asset class | major | Require strategy sub-type, thematic focus, economic model, and scaling constraints in every vertical analysis |
| `docs/valuation-driver-methodology.md`, validation | Quality gates were described narratively | No explicit JSON schemas or contract validator existed | Missing fields and metadata disagreement could pass silently | major | Add JSON schemas plus a local validator with cross-file checks |
| `README.md` and `CLAUDE.md` | VDA was described as reusable and neutral | Actual behavior and use case were PAX-heavy | New contributors would optimize for the wrong design center | minor | Update repository-level documentation to describe a PAX-first methodology with generic reuse as secondary |

## 2. Patch Plan

1. Update the authoritative methodology and repository-level docs.
   Files: `docs/methodology/pax-first-valuation-driver-methodology.md`, `README.md`, `CLAUDE.md`, `docs/valuation-driver-methodology.md`
2. Rewrite runtime agent instructions to one PAX-first contract.
   Files: `src/tauri/src/components/AgentsOrg.tsx`, `src/tauri/src/types/pipeline.ts`, `src/tauri/src/lib/ptyParser.ts`
3. Tighten statistical governance and metadata.
   Files: `archive/schemas/vda/statistics_metadata.schema.json`, `src/validation/vda_contracts.py`
4. Rebuild playbook and decision-layer contracts.
   Files: `archive/schemas/vda/playbook_entry.schema.json`, `archive/schemas/vda/pax_lens.schema.json`, `archive/schemas/vda/report_metadata.schema.json`, `src/validation/vda_contracts.py`
5. Add operational-prerequisite and strategy-subtype contracts.
   Files: `archive/schemas/vda/strategic_action.schema.json`, `archive/schemas/vda/strategy_subtype_analysis.schema.json`, `src/validation/vda_contracts.py`
6. Add tests for validation and metadata consistency.
   Files: `tests/test_vda_contracts.py`

## 3. Short Changelog

- Reframed VDA from a reusable-neutral playbook to a PAX-first decision methodology.
- Unified statistical governance around BH FDR q=0.10 plus Bonferroni confirmatory badge.
- Added an explicit stable-driver rule, sensitivity protocol, and mechanical-overlap flag.
- Added required PAX relevance, transferability, execution burden, tech/ops prerequisites, and margin-risk fields to the playbook contract.
- Introduced peer archetypes and strategy sub-type segmentation to stop mega-cap peers from dominating PAX conclusions mechanically.
- Added JSON schemas and a local validator to make methodology drift visible and enforceable.
