# Merge Conflicts Log — quantitative_data.json

**Run:** 2026-03-10-run2  
**Generated:** 2026-03-10  
**Total conflicts:** 5  

Conflicts arise when the same (firm_id, metric_id, period) triple appears in multiple tier files with different values. Resolution rule: newly collected data (higher tier priority: tier3 > tier2 > tier1) is preferred over carry-forward data.

| # | Firm | Metric | Period | Winner Tier | Winner Value | Loser Tier | Loser Value | Resolution |
|---|------|--------|--------|-------------|-------------|------------|-------------|------------|
| 1 | TPG Inc. (FIRM-009) | MET-VD-007 | FY2024 | tier2 | 0.093 | tier2 | 0.88 | Duplicate within tier2 — last-seen value kept. Inspect source. |
| 2 | EQT AB (FIRM-010) | MET-VD-001 | FY2024 | tier2 | 0.56 | tier2 | None | Duplicate within tier2 — last-seen value kept. Inspect source. |
| 3 | Partners Group Holding AG (FIRM-014) | MET-VD-001 | FY2024 | tier2 | 81.6 | tier2 | None | Duplicate within tier2 — last-seen value kept. Inspect source. |
| 4 | ICG plc (FIRM-016) | MET-VD-001 | FY2024 | tier2 | 0.96 | tier2 | None | Duplicate within tier2 — last-seen value kept. Inspect source. |
| 5 | Bridgepoint Group plc (FIRM-017) | MET-VD-007 | FY2024 | tier3 | 16.5 | tier3 | 14.8 | Duplicate within tier3 — last-seen value kept. Inspect source. |

## Conflict Detail Notes

### Conflict 1: TPG Inc. — MET-VD-007 — FY2024
- **Type:** duplicate_within_tier
- **Winner:** tier2 → value = `0.093`
- **Loser:** tier2 → value = `0.88`
- **Resolution:** Duplicate within tier2 — last-seen value kept. Inspect source.

### Conflict 2: EQT AB — MET-VD-001 — FY2024
- **Type:** duplicate_within_tier
- **Winner:** tier2 → value = `0.56`
- **Loser:** tier2 → value = `None`
- **Resolution:** Duplicate within tier2 — last-seen value kept. Inspect source.

### Conflict 3: Partners Group Holding AG — MET-VD-001 — FY2024
- **Type:** duplicate_within_tier
- **Winner:** tier2 → value = `81.6`
- **Loser:** tier2 → value = `None`
- **Resolution:** Duplicate within tier2 — last-seen value kept. Inspect source.

### Conflict 4: ICG plc — MET-VD-001 — FY2024
- **Type:** duplicate_within_tier
- **Winner:** tier2 → value = `0.96`
- **Loser:** tier2 → value = `None`
- **Resolution:** Duplicate within tier2 — last-seen value kept. Inspect source.

### Conflict 5: Bridgepoint Group plc — MET-VD-007 — FY2024
- **Type:** duplicate_within_tier
- **Winner:** tier3 → value = `16.5`
- **Loser:** tier3 → value = `14.8`
- **Resolution:** Duplicate within tier3 — last-seen value kept. Inspect source.

