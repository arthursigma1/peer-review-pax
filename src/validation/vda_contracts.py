from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Sequence

from pydantic import BaseModel, Field, ValidationError, model_validator


VALID_ARCHETYPES = frozenset({"north_star_peer", "near_peer", "adjacent_peer", "anti_pattern_peer"})
VALID_FEASIBILITY_HORIZONS = frozenset({"near_term_feasible", "medium_term_feasible", "aspirational"})
VALID_CONFIDENCE_LABELS = frozenset({"high", "moderate", "directional", "unsupported"})
VALID_DRIVER_CLASSES = frozenset({"stable_value_driver", "multiple_specific_driver", "contextual_driver", "unsupported"})
VALID_COVERAGE_QUALITY = frozenset({"adequate", "thin", "poor"})
VALID_COMPARABILITY_QUALITY = frozenset({"good", "mixed", "poor"})
VALID_INDEPENDENCE_FLAGS = frozenset({"independent", "partially_confounded", "confounded"})
VALID_P_VALUE_METHODS = frozenset({"permutation", "asymptotic_t_with_disclosure"})
VALID_SOURCE_BIAS_TAGS = frozenset({
    "regulatory-filing",
    "company-produced",
    "third-party-analyst",
    "journalist",
    "industry-report",
    "peer-disclosure",
    "supporting-low-trust",
})
VALID_PREREQ_EVIDENCE_CLASSES = frozenset({"directly_stated", "corroborated", "inferred"})
VALID_PREREQ_CONFIDENCE = frozenset({"high", "moderate", "low"})
VALID_STATED_OR_INFERRED = frozenset({"stated", "inferred"})
REQUIRED_SENSITIVITY_CHECKS = frozenset({
    "leave_one_out",
    "matched_sample",
    "archetype_stratified",
    "coverage_and_comparability",
    "mechanical_overlap",
    "confounding_check",
    "panel_robustness",
})
VALID_ADAPTATION_DISTANCES = frozenset({"low", "medium", "high"})
SOURCE_CITATION_RE = re.compile(r"^PS-VD-\d+$")
RANKING_THRESHOLD = 12
REPORTING_THRESHOLD = 8


class TemporalDepth(BaseModel):
    target_range: str = Field(min_length=1)
    mandatory_years: int = Field(ge=2)
    firms_with_multi_year: int = Field(ge=0)

    model_config = {"extra": "forbid"}


class MinimumSampleRule(BaseModel):
    ranking_threshold: int
    reporting_threshold: int

    model_config = {"extra": "forbid"}

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

    model_config = {"extra": "forbid"}

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
    dimension: str = Field(min_length=1)
    missing_reason: str = Field(min_length=1)

    model_config = {"extra": "forbid"}


class ContextualMarketFactors(BaseModel):
    tam: str | None = None
    market_share: str | None = None
    governance: str | None = None
    regulation: str | None = None

    model_config = {"extra": "forbid"}


class AssetClassStrategies(BaseModel):
    private_equity: list[str] | None = None
    infrastructure: list[str] | None = None
    private_credit: list[str] | None = None
    real_estate: list[str] | None = None
    natural_resources: list[str] | None = None

    model_config = {"extra": "forbid"}


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

    model_config = {"extra": "forbid"}


class StrategyProfile(BaseModel):
    firm_id: str = Field(min_length=1)
    firm_ticker: str = Field(min_length=1)
    archetype: str | None = None
    archetype_secondary: str | None = None
    ontology_mapping: OntologyMapping
    contextual_market_factors: ContextualMarketFactors
    stated_strategic_priorities: list[str] = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)
    missing_dimensions: list[MissingDimension] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_archetypes(self) -> "StrategyProfile":
        if self.archetype is not None and self.archetype not in VALID_ARCHETYPES:
            raise ValueError(f"invalid archetype: {self.archetype}")
        if self.archetype_secondary is not None and self.archetype_secondary not in VALID_ARCHETYPES:
            raise ValueError(f"invalid archetype_secondary: {self.archetype_secondary}")
        return self


class OperationalPrerequisite(BaseModel):
    requirement: str = Field(min_length=1)
    evidence_class: str
    source_bias_tag: str
    confidence_level: str
    stated_or_inferred: str

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_contract_fields(self) -> "OperationalPrerequisite":
        if self.evidence_class not in VALID_PREREQ_EVIDENCE_CLASSES:
            raise ValueError("invalid evidence_class")
        if self.source_bias_tag not in VALID_SOURCE_BIAS_TAGS:
            raise ValueError("invalid source_bias_tag")
        if self.confidence_level not in VALID_PREREQ_CONFIDENCE:
            raise ValueError("invalid confidence_level")
        if self.stated_or_inferred not in VALID_STATED_OR_INFERRED:
            raise ValueError("invalid stated_or_inferred")
        return self


class StrategicActionRecord(BaseModel):
    action_id: str = Field(min_length=1)
    firm_ticker: str = Field(min_length=1)
    strategy_sub_type: str = Field(min_length=1)
    thematic_focus: str = Field(min_length=1)
    economic_model: str = Field(min_length=1)
    what_was_done: str = Field(min_length=1)
    observed_metric_impact: str = Field(min_length=1)
    operational_prerequisites: list[OperationalPrerequisite] = Field(min_length=1)

    model_config = {"extra": "forbid"}


class StrategicActionsContract(BaseModel):
    actions: list[StrategicActionRecord] = Field(min_length=1)

    model_config = {"extra": "forbid"}


class CorrelationRecord(BaseModel):
    correlation_id: str = Field(min_length=1)
    driver_metric_id: str = Field(min_length=1)
    valuation_multiple: str = Field(min_length=1)
    spearman_rho: float
    p_value: float = Field(ge=0.0, le=1.0)
    n_firms_included: int = Field(ge=REPORTING_THRESHOLD)
    coverage_quality: str
    comparability_quality: str
    mechanical_overlap_flag: bool
    independence_flag: str
    p_value_method: str
    confirmatory_badge: str | None = None

    model_config = {"extra": "ignore"}

    @model_validator(mode="after")
    def validate_correlation_flags(self) -> "CorrelationRecord":
        if self.coverage_quality not in VALID_COVERAGE_QUALITY:
            raise ValueError("invalid coverage_quality")
        if self.comparability_quality not in VALID_COMPARABILITY_QUALITY:
            raise ValueError("invalid comparability_quality")
        if self.independence_flag not in VALID_INDEPENDENCE_FLAGS:
            raise ValueError("invalid independence_flag")
        if self.p_value_method not in VALID_P_VALUE_METHODS:
            raise ValueError("invalid p_value_method")
        if self.confirmatory_badge not in {None, "bonferroni_survivor"}:
            raise ValueError("invalid confirmatory_badge")
        return self


class CorrelationsContract(BaseModel):
    correlations: list[CorrelationRecord] = Field(min_length=1)

    model_config = {"extra": "ignore"}


class DriverRankingEntry(BaseModel):
    driver_id: str = Field(min_length=1)
    correlation_classification: str
    confidence_class: str
    coverage_quality: str
    comparability_quality: str
    mechanical_overlap_flag: bool
    independence_flag: str
    p_value_method: str
    confirmatory_badge: str | None = None

    model_config = {"extra": "ignore"}

    @model_validator(mode="after")
    def validate_driver_fields(self) -> "DriverRankingEntry":
        if self.correlation_classification not in VALID_DRIVER_CLASSES:
            raise ValueError("invalid correlation_classification")
        if self.confidence_class not in VALID_CONFIDENCE_LABELS:
            raise ValueError("invalid confidence_class")
        if self.coverage_quality not in VALID_COVERAGE_QUALITY:
            raise ValueError("invalid coverage_quality")
        if self.comparability_quality not in VALID_COMPARABILITY_QUALITY:
            raise ValueError("invalid comparability_quality")
        if self.independence_flag not in VALID_INDEPENDENCE_FLAGS:
            raise ValueError("invalid independence_flag")
        if self.p_value_method not in VALID_P_VALUE_METHODS:
            raise ValueError("invalid p_value_method")
        if self.confirmatory_badge not in {None, "bonferroni_survivor"}:
            raise ValueError("invalid confirmatory_badge")
        return self


class DriverRankingContract(BaseModel):
    drivers: list[DriverRankingEntry] = Field(min_length=1)

    model_config = {"extra": "ignore"}


class StrategySubtypeAnalysis(BaseModel):
    vertical: str = Field(min_length=1)
    strategy_sub_type: str = Field(min_length=1)
    thematic_focus: str = Field(min_length=1)
    economic_model: str = Field(min_length=1)
    value_creation_mechanics: str = Field(min_length=1)
    fee_model: str = Field(min_length=1)
    operating_model: str = Field(min_length=1)
    tech_data_reporting_requirements: list[str] = Field(min_length=1)
    scaling_constraints: list[str] = Field(min_length=1)
    margin_sensitivities: list[str] = Field(min_length=1)
    pax_transferability_barriers: list[str] = Field(min_length=1)

    model_config = {"extra": "forbid"}


class AssetClassAnalysisContract(BaseModel):
    strategy_subtype_analyses: list[StrategySubtypeAnalysis] = Field(min_length=1)

    model_config = {"extra": "forbid"}


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

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_feasibility_horizon(self) -> "PAXRelevance":
        if self.feasibility_horizon not in VALID_FEASIBILITY_HORIZONS:
            raise ValueError("invalid feasibility_horizon")
        return self


class PlaybookEntry(BaseModel):
    Play_ID: str | None = None
    Anti_ID: str | None = None
    What_Was_Done: str = Field(min_length=1)
    Observed_Metric_Impact: str = Field(min_length=1)
    Why_It_Worked: str = Field(min_length=1)
    PAX_Relevance: PAXRelevance
    Preconditions: list[str] = Field(min_length=1)
    Operational_And_Tech_Prerequisites: list[str] = Field(min_length=1)
    Execution_Burden: str = Field(min_length=1)
    Time_To_Build: str = Field(min_length=1)
    Margin_Risk: str = Field(min_length=1)
    Failure_Modes_And_Margin_Destroyers: list[str] = Field(min_length=1)
    Transferability_Constraints: list[str] = Field(min_length=1)
    Archetype_Relevance: str = Field(min_length=1)
    Evidence_Strength: str
    Recommendation_For_PAX: str = Field(min_length=1)
    source_citations: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_entry(self) -> "PlaybookEntry":
        if not self.Play_ID and not self.Anti_ID:
            raise ValueError("playbook entry must have Play_ID or Anti_ID")
        if self.Evidence_Strength not in VALID_CONFIDENCE_LABELS:
            raise ValueError("invalid Evidence_Strength")
        for cit in self.source_citations:
            if not SOURCE_CITATION_RE.match(cit):
                raise ValueError(f"source_citations entry does not match PS-VD-NNN: {cit!r}")
        return self


class DriverPlaybook(BaseModel):
    driver_id: str = Field(min_length=1)
    plays: list[PlaybookEntry] = Field(min_length=1)
    anti_patterns: list[PlaybookEntry] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PlatformPlaybookContract(BaseModel):
    driver_playbooks: list[DriverPlaybook] = Field(min_length=1)

    model_config = {"extra": "forbid"}


class VerticalPlaybook(BaseModel):
    vertical_id: str = Field(min_length=1)
    plays: list[PlaybookEntry] = Field(min_length=1)
    anti_patterns: list[PlaybookEntry] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class AssetClassPlaybookContract(BaseModel):
    vertical_playbooks: list[VerticalPlaybook] = Field(min_length=1)

    model_config = {"extra": "forbid"}


class RankedRecommendation(BaseModel):
    play_id: str = Field(min_length=1)
    priority_rank: int = Field(ge=1)
    applicability: str
    strategic_principle: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    adaptation_notes: str | None = None
    why_this_matters_for_pax: str = Field(min_length=1)
    what_must_be_true: list[str] = Field(min_length=1)
    why_this_may_fail_for_pax: list[str] = Field(min_length=1)
    implementation_pathway: list[str] = Field(min_length=1)
    feasibility_horizon: str
    transferability_score: int = Field(default=3, ge=1, le=5)
    adaptation_distance: str = Field(default="medium")
    copycat_risk: str | None = None
    principle_extracted: str | None = None

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_recommendation(self) -> "RankedRecommendation":
        if self.applicability not in {"directly_applicable", "requires_adaptation", "not_applicable"}:
            raise ValueError("invalid applicability")
        if self.feasibility_horizon not in VALID_FEASIBILITY_HORIZONS:
            raise ValueError("invalid feasibility_horizon")
        if self.adaptation_distance not in VALID_ADAPTATION_DISTANCES:
            raise ValueError("invalid adaptation_distance")
        return self


class GovernanceCascade(BaseModel):
    board: list[str]
    management: list[str]
    business_units: list[str]

    model_config = {"extra": "forbid"}


class PAXLensContract(BaseModel):
    target_company: str = Field(min_length=1)
    target_ticker: str = Field(min_length=1)
    ranked_recommendations: list[RankedRecommendation] = Field(min_length=1)
    decision_risks: list[str] = Field(min_length=1)
    governance_cascade: GovernanceCascade

    model_config = {"extra": "forbid"}


class ReportMetadata(BaseModel):
    report_mode: str
    default_synthesis: str
    target_company: str = Field(min_length=1)
    target_ticker: str = Field(min_length=1)
    peer_evidence_layer_present: bool
    pax_interpretation_layer_present: bool
    pax_decision_layer_present: bool
    statistical_governance: StatisticalGovernance

    model_config = {"extra": "forbid"}

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
    data = _load_json(path)
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a JSON array of strategy profiles")
    if not data:
        raise ValueError(f"{path}: strategy_profiles must contain at least one profile")
    profiles: list[StrategyProfile] = []
    for i, item in enumerate(data):
        try:
            profiles.append(StrategyProfile.model_validate(item))
        except ValidationError as exc:
            raise ValueError(f"{path}[{i}]: {exc}") from exc
    return profiles


def _validate_final_report(path: Path, target_company: str, target_ticker: str) -> None:
    try:
        content = path.read_text()
    except FileNotFoundError:
        raise FileNotFoundError(f"Missing required artifact: {path}") from None

    lowered = content.lower()
    if "<html" not in lowered:
        raise ValueError(f"{path}: expected an HTML document")
    if target_company.lower() not in lowered:
        raise ValueError(f"{path}: target_company not mentioned in final_report.html")
    if target_ticker.lower() not in lowered:
        raise ValueError(f"{path}: target_ticker not mentioned in final_report.html")
    if not re.search(r'class=["\']fn["\']', content):
        raise ValueError(f"{path}: no footnote markers found (expected <sup class=\"fn\"> elements)")
    if "sources & references" not in lowered and not re.search(r"<h[1-6][^>]*>.*?sources.*?references.*?</h[1-6]>", lowered, re.DOTALL):
        raise ValueError(f"{path}: missing 'Sources & References' section")


def _cross_check_statistics(stats_metadata: StatisticalGovernance, report_metadata: ReportMetadata) -> None:
    if report_metadata.statistical_governance != stats_metadata:
        raise ValueError("report_metadata statistical governance does not match statistics_metadata")


def validate_run_directory(run_dir: Path) -> None:
    _validate_strategy_profiles(run_dir / "2-data" / "strategy_profiles.json")
    _validate_model(StrategicActionsContract, run_dir / "2-data" / "strategic_actions.json")

    stats_metadata = _validate_model(StatisticalGovernance, run_dir / "3-analysis" / "statistics_metadata.json")
    _validate_model(CorrelationsContract, run_dir / "3-analysis" / "correlations.json")
    _validate_model(DriverRankingContract, run_dir / "3-analysis" / "driver_ranking.json")

    _validate_model(AssetClassAnalysisContract, run_dir / "4-deep-dives" / "asset_class_analysis.json")

    platform_playbook = _validate_model(PlatformPlaybookContract, run_dir / "5-playbook" / "platform_playbook.json")
    asset_playbook = _validate_model(AssetClassPlaybookContract, run_dir / "5-playbook" / "asset_class_playbooks.json")
    pax_lens = _validate_model(PAXLensContract, run_dir / "5-playbook" / "target_company_lens.json")
    report_metadata = _validate_model(ReportMetadata, run_dir / "5-playbook" / "report_metadata.json")

    _cross_check_statistics(stats_metadata, report_metadata)

    if report_metadata.target_ticker != pax_lens.target_ticker:
        raise ValueError("target_ticker mismatch between report metadata and PAX lens")
    if report_metadata.target_company != pax_lens.target_company:
        raise ValueError("target_company mismatch between report metadata and PAX lens")

    if not platform_playbook.driver_playbooks:
        raise ValueError("platform_playbook must contain at least one driver_playbook")
    if not asset_playbook.vertical_playbooks:
        raise ValueError("asset_class_playbooks must contain at least one vertical_playbook")

    _validate_final_report(
        run_dir / "5-playbook" / "final_report.html",
        target_company=report_metadata.target_company,
        target_ticker=report_metadata.target_ticker,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a VDA run directory against the PAX-first contract.")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args(argv)

    validate_run_directory(args.run_dir)
    print(f"Validated {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
