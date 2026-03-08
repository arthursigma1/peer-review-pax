# PAX Peer Strategy Ontology

Status: PAX-specific business-model ontology. This document captures the
minimum strategy map to use when deep-diving selected peers for Patria. It is a
required baseline for PAX runs, but it is not a closed taxonomy. Agents may add
new values or dimensions when the evidence requires it.

## 1. Purpose

The qualitative track should not analyze peers only by broad vertical labels
such as Credit or Private Equity. It should map each selected peer across a
common business-model grid so the analysis can explain which combinations of
choices appear to be associated with valuation-relevant outcomes.

Use this ontology for:

- `strategy_profiles.json`
- `asset_class_analysis.json`
- playbook generation
- transferability assessment for PAX

## 2. Mapping Principle

Every selected peer should be mapped across all dimensions below whenever
evidence is available.

Rules:

- do not force-fit a peer into a category with weak evidence
- use `null` plus missing-reason where needed
- combinations matter more than any single label
- new categories may be added when repeated evidence shows the baseline is too
  narrow

## 3. Core Dimensions

### Geographical Reach

- `global`
- `regional`
- `local`

### Business Focus

- `asset_management`
- `advisory`

### Asset Focus

- `large_caps`
- `mid_market`
- `lower_mid_market`

### Asset Class and Investment Strategies

Interpretation rule:

- treat the asset classes below as the default top-level vertical taxonomy for
  PAX runs
- treat secondaries, GP-leds, co-investments, primaries, and other
  solutions-style formats as strategy sub-types or wrappers within the relevant
  asset class unless a run-specific override is disclosed explicitly

#### Private Equity

- `vc`
- `growth`
- `buyout`
- `primaries`
- `secondaries`
- `co_investments`

#### Infrastructure

- `value_added`
- `core_plus`
- `core`
- `credit`
- `primaries`
- `secondaries`
- `co_investments`

#### Private Credit

- `direct_lending`
- `clo`
- `asset_backed`
- `mezzanine`
- `special_situations`
- `primaries`
- `secondaries`
- `co_investments`

#### Real Estate

- `pere`
- `core_plus`
- `core`
- `credit`
- `primaries`
- `secondaries`
- `co_investments`

#### Natural Resources

- `timo`
- `reforest`
- `climate`
- `primaries`
- `secondaries`
- `co_investments`

### Sector Orientation

- `sector_agnostic`
- `sector_focused`
- `sector_specific`

### Origination Engine

- `captive_origination`
- `primary_originator`
- `structuring`
- `syndicated_deals`

### Fund Type

- `listed`
- `sma`
- `drawdown`
- `interval`
- `evergreen`

### Capital Source

- `proprietary_capital`
- `captive_capital_pool`
- `non_captive_capital_pool`

### Distribution Strategy

- `direct`
- `consultants`
- `distributors`
- `placement_agents`

### Client Segment

Institutional:

- `pension_funds`
- `swf`
- `dfis`
- `insurance`
- `endowments_foundations`
- `corporate`
- `asset_managers`

Individuals:

- `family_offices`
- `private_banks`
- `hnwi`
- `retail`

### Growth Agenda

- `organic`
- `inorganic`

### Share Class

- `single_class`
- `dual_class`

## 4. Contextual Market Factors

These are NOT business-model choices. They are market-context data points that
may shape interpretation or transferability. Capture them separately from the
business-model grid above. Do not confuse mapping a peer's market position with
mapping its strategic decisions.

- `tam` — total addressable market estimate
- `market_share` — peer's estimated share of TAM
- `governance` — governance structure where it materially constrains strategy
- `regulation` — regulatory regime where it materially constrains transferability

## 5. Analytical Use

For each selected peer, the analysis should answer:

- which dimensions define the peer's current business model
- which dimensions appear most relevant to its KPI outcomes
- which dimensions are most transferable to PAX
- which dimensions are structurally non-transferable to PAX
- which combinations create value and which combinations create execution drag

## 6. Usage Rules

- Treat this as the minimum decomposition grid for PAX deep-dives
- Do not collapse the analysis below this baseline without explicit disclosure
- Do not treat these labels as statistically causal by themselves
- Evidence overrides the ontology when a peer's actual model does not fit neatly
- Any newly introduced dimension should be documented consistently across
  selected peers
