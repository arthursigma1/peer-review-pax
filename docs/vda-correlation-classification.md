# VDA Correlation Classification

Referenced from [CLAUDE.md](../CLAUDE.md).

## Driver Classification Rules

| Classification | Criterion |
|---|---|
| Stable value driver | Satisfies repository rule `stable_v1_two_of_three` |
| Multiple-specific driver | `abs(rho) >= 0.5` on exactly one eligible multiple and fails stable rule |
| Contextual driver | Useful for decomposition or interpretation but not headline ranking |
| Unsupported | Not defensible for strategic interpretation |

## Key Findings (2026-03-09-run2)

- **DE/share** is the only stable value driver (rho >= 0.5 on 2/3 multiples)
- Top drivers: DE/share (stable), FRE growth (multiple-specific), AUM, FEAUM
