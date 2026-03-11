# VDA Consulting Evidence Hierarchy

Referenced from [CLAUDE.md](../CLAUDE.md).

Consulting and industry-report sources (PS-VD-9xx) are **market context only**. Peer evidence always wins.

## Rules

| Rule | Detail |
|---|---|
| Peer evidence > consulting | If a consulting source conflicts with a filing, earnings deck, or investor presentation, the firm source wins |
| Consulting cannot solely sustain | firm-specific metrics, firm-specific actions, causal claims about a specific firm, or final recommendations |
| Allowed usage | `market_context`, `distribution_context`, `operating_model_context`, `supporting_context` |
| Disallowed usage | `firm_specific_fact`, `firm_specific_metric`, `firm_specific_action`, `sole_basis_for_recommendation` |
| Citation rule | PS-VD-9xx may cite market-level claims; firm-specific claims require peer PS-VD sources |
| claim-auditor enforcement | Any claim where PS-VD-9xx is the sole citation AND the claim is about a specific firm → BLOCK |

## Agent Routing

**Agents that consume `consulting_context.json`:** strategy-extractor, vertical-analyst, playbook-synthesizer, target-lens, report-builder, claim-auditor.

**Agents that do NOT receive it:** data-collector-t1, data-collector-t2, data-collector-t3.

## Claim Scope Classification

Each claim in `consulting_context.json` has a `scope` field (`market`, `segment`, `multi_firm`, `single_firm`). Claims with `single_firm` scope must not be used as firm-specific evidence.
