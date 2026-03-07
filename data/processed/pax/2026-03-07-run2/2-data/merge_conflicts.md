# Data Merge Conflicts Log

**Merge date:** 2026-03-07
**Run:** 2026-03-07-run2
**Tiers merged:** 1, 2, 3

## No Conflicts Found

All three tiers covered mutually exclusive firm sets. No overlapping firm+metric+period combinations were detected.

## Merge Notes

- Tier 1 (9 firms): Flat `data_points[]` array normalized to nested `metrics{}` dict
- Tier 2 (9 firms): Nested `firms[].metrics{}` dict — already in target format
- Tier 3 (7 firms): Nested `firms[].metrics[]` array + separate `valuation_multiples[]` — normalized
- Valuation multiples extracted into separate `valuation_multiples` dict for all tiers
- Market cap reference dates vary across tiers (see metadata)
