from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

from pydantic import BaseModel, Field, ValidationError, model_validator

# Shared constants — keep in sync with schemas/vda/*.schema.json
VALID_ARCHETYPES = frozenset({"north_star_peer", "near_peer", "adjacent_peer", "anti_pattern_peer"})
VALID_FEASIBILITY_HORIZONS = frozenset({"near_term_feasible", "medium_term_feasible", "aspirational"})
VALID_CONFIDENCE_LABELS = frozenset({"high", "moderate", "directional", "unsupported"})
REQUIRED_SENSITIVITY_CHECKS = frozenset({
    "leave_one_out",
    "matched_sample",
    "archetype_stratified",
    "coverage_and_comparability",
    "mechanical_overlap",
    "confounding_check",
    "panel_robustness",
})


class TemporalDepth(BaseModel):
    target_range: str
    mandatory_years: int = Field(ge=2)
    firms_with_multi_year: int = Field(ge=0)


RANKING_THRESHOLD = 12
REPORTING_THRESHOLD = 8


class MinimumSampleRule(BaseModel):
    ranking_threshold: int
    reporting_threshold: int

    @model_validator(mode="after")
    def validate_thresholds(self) -> "MinimumSampleRule":
        if self.ranking_threshold != RANKING_THRESHOLD:
            raise ValueError(f"ranking_threshold must be {RANKING_THRESHOLD}")
        if self.reporting_threshold != REPORTING_THRESHOLD:
            raise ValueError(f"reporting_threshold must be {REPORTING_THRESHOLD}")
        return self


class StatisticalGovernance(BaseModel):
    discovery_method: str = Field(pattern=r"^bh_fdr_q_0\.10$")
    discovery_q: float
    confirmatory_badge: str = Field(pattern=r"^bonferroni_survivor$")
    p_value_method_primary: str = Field(pattern=r"^permutation$")
    p_value_method_fallback: str = Field(pattern=r"^asymptotic_t_with_disclosure$")
    stable_driver_rule_id: str = Field(pattern=r"^stable_v1_two_of_three$")
    confidence_taxonomy: list[str]
    sensitivity_protocol: list[str]
    n_effective: int = Field(ge=12)
    temporal_depth: TemporalDepth
    ci_method: str
    minimum_sample_rule: MinimumSampleRule

    @model_validator(mode="after")
    def validate_constants(self) -> "StatisticalGovernance":
        if self.discovery_q != 0.10:
            raise ValueError("discovery_q must be 0.10")
        if set(self.confidence_taxonomy) != VALID_CONFIDENCE_LABELS:
            raise ValueError("confidence_taxonomy must match the repository contract")
        if not REQUIRED_SENSITIVITY_CHECKS.issubset(set(self.sensitivity_protocol)):
            raise ValueError("sensitivity_protocol is missing required checks")
        if self.ci_method not in {"bootstrap_10k", "fisher_z_with_disclosure"}:
            raise ValueError("ci_method must be bootstrap_10k or fisher_z_with_disclosure")
        return self


class MissingDimension(BaseModel):
    dimension: str
    missing_reason: str


class ContextualMarketFactors(BaseModel):
    tam: str | None = None
    market_share: str | None = None
    governance: str | None = None
    regulation: str | None = None


class AssetClassStrategies(BaseModel):
    private_equity: list[str] | None = None
    infrastructure: list[str] | None = None
    private_credit: list[str] | None = None
    real_estate: list[str] | None = None
    natural_resources: list[str] | None = None


class OntologyMapping(BaseModel):
    geographical_reach: list[str] | None = None
    business_focus: list[str] | None = None
    asset_focus: list[str] | None = None
    asset_class_and_investment_strategies: AssetClassStrategies | None = None
    sector_orientation: list[str] | None = None
    origination_engine: list[str] | None = None
    fund_type: list[str] | None = None
    capital_source: list[str] | None = None
    distribution_strategy: list[str] | None = None
    client_segment: list[str] | None = None
    growth_agenda: list[str] | None = None
    share_class: list[str] | None = None


class StrategyProfile(BaseModel):
    firm_id: str
    firm_ticker: str
    archetype: str | None = None
    archetype_secondary: str | None = None
    ontology_mapping: OntologyMapping
    contextual_market_factors: ContextualMarketFactors
    stated_strategic_priorities: list[str]
    source_ids: list[str]
    missing_dimensions: list[MissingDimension] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_archetypes(self) -> "StrategyProfile":
        if self.archetype is not None and self.archetype not in VALID_ARCHETYPES:
            raise ValueError(f"invalid archetype: {self.archetype}")
        if self.archetype_secondary is not None and self.archetype_secondary not in VALID_ARCHETYPES:
            raise ValueError(f"invalid archetype_secondary: {self.archetype_secondary}")
        if not self.stated_strategic_priorities:
            raise ValueError("stated_strategic_priorities cannot be empty")
        if not self.source_ids:
            raise ValueError("source_ids cannot be empty")
        return self


class PAXRelevance(BaseModel):
    scale_fit: int = Field(ge=1, le=5)
    geography_fit: int = Field(ge=1, le=5)
    client_distribution_fit: int = Field(ge=1, le=5)
    balance_sheet_fit: int = Field(ge=1, le=5)
    regulatory_fit: int = Field(ge=1, le=5)
    operating_model_fit: int = Field(ge=1, le=5)
    tech_readiness: int = Field(ge=1, le=5)
    data_reporting_readiness: int = Field(ge=1, le=5)
    time_to_build: int = Field(ge=1, le=5)
    capital_intensity: int = Field(ge=1, le=5)
    margin_risk: int = Field(ge=1, le=5)
    execution_complexity: int = Field(ge=1, le=5)
    feasibility_horizon: str

    @model_validator(mode="after")
    def validate_feasibility_horizon(self) -> "PAXRelevance":
        if self.feasibility_horizon not in VALID_FEASIBILITY_HORIZONS:
            raise ValueError("invalid feasibility_horizon")
        return self


class PlaybookEntry(BaseModel):
    Play_ID: str
    What_Was_Done: str
    Observed_Metric_Impact: str
    Why_It_Worked: str
    PAX_Relevance: PAXRelevance
    Preconditions: list[str]
    Operational_And_Tech_Prerequisites: list[str]
    Execution_Burden: str
    Time_To_Build: str
    Margin_Risk: str
    Failure_Modes_And_Margin_Destroyers: list[str]
    Transferability_Constraints: list[str]
    Archetype_Relevance: str
    Evidence_Strength: str
    Recommendation_For_PAX: str

    @model_validator(mode="after")
    def validate_lengths(self) -> "PlaybookEntry":
        if not self.Preconditions:
            raise ValueError("Preconditions cannot be empty")
        if not self.Operational_And_Tech_Prerequisites:
            raise ValueError("Operational_And_Tech_Prerequisites cannot be empty")
        if not self.Failure_Modes_And_Margin_Destroyers:
            raise ValueError("Failure_Modes_And_Margin_Destroyers cannot be empty")
        if not self.Transferability_Constraints:
            raise ValueError("Transferability_Constraints cannot be empty")
        if self.Evidence_Strength not in VALID_CONFIDENCE_LABELS:
            raise ValueError("invalid Evidence_Strength")
        return self


class RankedRecommendation(BaseModel):
    play_id: str
    priority_rank: int = Field(ge=1)
    why_this_matters_for_pax: str
    what_must_be_true: list[str]
    why_this_may_fail_for_pax: list[str]
    feasibility_horizon: str

    @model_validator(mode="after")
    def validate_recommendation(self) -> "RankedRecommendation":
        if self.feasibility_horizon not in VALID_FEASIBILITY_HORIZONS:
            raise ValueError("invalid feasibility_horizon")
        if not self.what_must_be_true or not self.why_this_may_fail_for_pax:
            raise ValueError("recommendation arrays cannot be empty")
        return self


class GovernanceCascade(BaseModel):
    board: list[str]
    management: list[str]
    business_units: list[str]


class PAXLensContract(BaseModel):
    target_company: str
    target_ticker: str
    ranked_recommendations: list[RankedRecommendation]
    decision_risks: list[str] = Field(min_length=1)
    governance_cascade: GovernanceCascade


class ReportMetadata(BaseModel):
    report_mode: str
    default_synthesis: str
    target_company: str
    target_ticker: str
    peer_evidence_layer_present: bool
    pax_interpretation_layer_present: bool
    pax_decision_layer_present: bool
    statistical_governance: StatisticalGovernance

    @model_validator(mode="after")
    def validate_mode(self) -> "ReportMetadata":
        if self.report_mode != "pax_decision_memo":
            raise ValueError("report_mode must be pax_decision_memo")
        if self.default_synthesis != "pax_first":
            raise ValueError("default_synthesis must be pax_first")
        if not (
            self.peer_evidence_layer_present
            and self.pax_interpretation_layer_present
            and self.pax_decision_layer_present
        ):
            raise ValueError("all report layers must be present")
        return self


class DriverPlaybook(BaseModel):
    driver_id: str
    plays: list[PlaybookEntry]
    anti_patterns: list[PlaybookEntry] = Field(default_factory=list)


class PlatformPlaybookContract(BaseModel):
    driver_playbooks: list[DriverPlaybook]


class VerticalPlaybook(BaseModel):
    vertical_id: str
    plays: list[PlaybookEntry]
    anti_patterns: list[PlaybookEntry] = Field(default_factory=list)


class AssetClassPlaybookContract(BaseModel):
    vertical_playbooks: list[VerticalPlaybook]


def _load_json(path: Path) -> Any:
    try:
        with path.open() as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise FileNotFoundError(f"Missing required artifact: {path}") from None


def _validate_model(model_cls: type[BaseModel], path: Path) -> BaseModel:
    try:
        return model_cls.model_validate(_load_json(path))
    except ValidationError as exc:
        raise ValueError(f"{path}: {exc}") from exc


def _validate_strategy_profiles(path: Path) -> list[StrategyProfile]:
    """Validate strategy_profiles.json — expects a JSON array of profile objects."""
    data = _load_json(path)
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a JSON array of strategy profiles")
    if not data:
        raise ValueError(f"{path}: strategy_profiles must contain at least one profile")
    profiles = []
    for i, item in enumerate(data):
        try:
            profiles.append(StrategyProfile.model_validate(item))
        except ValidationError as exc:
            raise ValueError(f"{path}[{i}]: {exc}") from exc
    return profiles


def _cross_check_statistics(
    stats_metadata: StatisticalGovernance,
    report_metadata: ReportMetadata,
) -> None:
    if report_metadata.statistical_governance != stats_metadata:
        raise ValueError("report_metadata statistical governance does not match statistics_metadata")


def validate_run_directory(run_dir: Path) -> None:
    # Optional: validate strategy profiles if present (step 1 output)
    strategy_profiles_path = run_dir / "2-data" / "strategy_profiles.json"
    try:
        _validate_strategy_profiles(strategy_profiles_path)
    except FileNotFoundError:
        pass

    stats_metadata = _validate_model(StatisticalGovernance, run_dir / "3-analysis" / "statistics_metadata.json")
    report_metadata = _validate_model(ReportMetadata, run_dir / "5-playbook" / "report_metadata.json")
    platform_playbook = _validate_model(PlatformPlaybookContract, run_dir / "5-playbook" / "platform_playbook.json")
    asset_playbook = _validate_model(AssetClassPlaybookContract, run_dir / "5-playbook" / "asset_class_playbooks.json")
    pax_lens = _validate_model(PAXLensContract, run_dir / "5-playbook" / "target_company_lens.json")

    _cross_check_statistics(stats_metadata, report_metadata)

    if report_metadata.target_ticker != pax_lens.target_ticker:
        raise ValueError("target_ticker mismatch between report metadata and PAX lens")
    if report_metadata.target_company != pax_lens.target_company:
        raise ValueError("target_company mismatch between report metadata and PAX lens")
    if not platform_playbook.driver_playbooks:
        raise ValueError("platform_playbook must contain at least one driver_playbook")
    if not asset_playbook.vertical_playbooks:
        raise ValueError("asset_class_playbooks must contain at least one vertical_playbook")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a VDA run directory against the PAX-first contract.")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args(argv)

    validate_run_directory(args.run_dir)
    print(f"Validated {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
