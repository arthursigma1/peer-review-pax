# Agent Instructions For Consulting Context

## Global Rule
- Use consulting and industry-report sources only for market context, distribution context, operating model context, and supporting context.
- Do not use consulting or industry-report sources as the primary basis for firm-specific facts, firm-specific metrics, or firm-specific actions.
- Do not let consulting sources override filings, earnings materials, investor presentations, or direct peer disclosures.
- If a consulting source conflicts with peer evidence, peer evidence wins and the consulting source may only be cited as broader market framing.

## Which File To Read
- Read `/Users/arthurhrk/Documents/GitHub/peer-review-pax/data/processed/pax/2026-03-09-run2/2-data/consulting_context.json` instead of the raw consulting crawl outputs.

## Agent-Specific Guidance
- Source Cataloger: keep consulting sources tagged as `industry-report` and conceptually separate from peer-primary evidence.
- Data Collectors: ignore consulting sources for firm-level quantitative extraction; only use them for contextual metrics or market-structure notes.
- Strategy Researcher: use consulting context only inside `contextual_market_factors` or to frame distribution / operating-model trends; do not use it to assert a peer strategic action.
- Sector Specialist: this is the main consumer; use consulting context to explain vertical trends such as retailization, private credit growth, consolidation, and wealth-channel expansion.
- Insight Synthesizer: use consulting context to answer why a theme matters now, but tie recommendations back to peer evidence.
- Target Company Lens: use consulting context only to strengthen `why_this_matters_for_pax`, never as the sole support for a recommendation.
- Fact Checker: block any claim where an `industry-report` citation is used as proof of a firm-specific action, metric, or causal statement about a single peer.

## Recommended Context Themes
- wealth_distribution: `8` sources
- democratization: `8` sources
- fundraising_lp_demand: `7` sources
- margin_operating_model: `4` sources
- mna_consolidation: `2` sources
- private_credit: `1` sources
