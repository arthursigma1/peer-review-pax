# Merge Conflicts Log

**Date:** 2026-03-07
**Total conflicts:** 1

## Phase 1: Tier merge (tier1 + tier2 + tier3)

No conflicts detected. All tier files had unique (firm_id, metric_id, period) combinations.

## Phase 2: Multiples merge (valuation_multiples.json)

| Firm | Metric | Period | Existing Value | Existing Confidence | New Value | New Confidence | Resolution |
|------|--------|--------|---------------|---------------------|-----------|----------------|------------|
| FIRM-019 | MET-VD-028 | LTM | null | — | 0.04 | medium | Kept new value (0.04) — existing was null |

**Note:** This conflict arose because tier3 had a null placeholder for FIRM-019/MET-VD-028/LTM, while the multiples collector provided the actual value (EV/FEAUM = 4.0%). The non-null value was retained.
