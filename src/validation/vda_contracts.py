from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Optional, Sequence

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
    """Accept either mandatory_years (schema name) or actual_years (SKILL.md name)."""
    target_range: str
    # SKILL.md says actual_years; schema says mandatory_years — accept both
    mandatory_years: Optional[int] = Field(default=None, ge=2)
    actual_years: Optional[int] = Field(default=None, ge=2)
    firms_with_multi_year: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_years(self) -> "TemporalDepth":
        if self.mandatory_years is None and self.actual_years is None:
            raise ValueError("temporal_depth must include mandatory_years or actual_years")
        return self


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
    """
    Tolerant model — only the fields that carry governance meaning are strict.
    Extra fields produced by agents are silently ignored.
    """
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

    model_config = {"extra": "ignore"}

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
    tam: Optional[str] = None
    market_share: Optional[str] = None
    governance: Optional[str] = None
    regulation: Optional[str] = None


class AssetClassStrategies(BaseModel):
    private_equity: Optional[list[str]] = None
    infrastructure: Optional[list[str]] = None
    private_credit: Optional[list[str]] = None
    real_estate: Optional[list[str]] = None
    natural_resources: Optional[list[str]] = None


class OntologyMapping(BaseModel):
    geographical_reach: Optional[list[str]] = None
    business_focus: Optional[list[str]] = None
    asset_focus: Optional[list[str]] = None
    asset_class_and_investment_strategies: Optional[AssetClassStrategies] = None
    sector_orientation: Optional[list[str]] = None
    origination_engine: Optional[list[str]] = None
    fund_type: Optional[list[str]] = None
    capital_source: Optional[list[str]] = None
    distribution_strategy: Optional[list[str]] = None
    client_segment: Optional[list[str]] = None
    growth_agenda: Optional[list[str]] = None
    share_class: Optional[list[str]] = None


class StrategyProfile(BaseModel):
    firm_id: str
    firm_ticker: Optional[str] = None
    # agent may use ticker instead of firm_ticker
    ticker: Optional[str] = None
    firm_name: Optional[str] = None
    archetype: Optional[str] = None
    archetype_secondary: Optional[str] = None
    ontology_mapping: Optional[OntologyMapping] = None
    contextual_market_factors: Optional[ContextualMarketFactors] = None
    stated_strategic_priorities: list[str]
    source_ids: Optional[list[str]] = None
    missing_dimensions: list[MissingDimension] = Field(default_factory=list)

    model_config = {"extra": "ignore"}

    @model_validator(mode="before")
    @classmethod
    def unwrap_nested_profile(cls, data: Any) -> Any:
        """
        Handle the actual agent output format where profile fields are nested inside
        a 'profile' sub-object rather than at the top level.

        Example actual output:
        {
          "firm_id": "FIRM-002",
          "firm_name": "...",
          "ticker": "BX",
          "profile": {
            "stated_strategic_priorities": [...],
            "source_citations": [...]
          }
        }
        """
        if isinstance(data, dict) and "profile" in data and isinstance(data["profile"], dict):
            nested = data["profile"]
            merged = dict(data)
            # Hoist stated_strategic_priorities from nested profile if not at top level
            if "stated_strategic_priorities" not in merged and "stated_strategic_priorities" in nested:
                merged["stated_strategic_priorities"] = nested["stated_strategic_priorities"]
            # Hoist source_ids / source_citations as source_ids
            if "source_ids" not in merged:
                if "source_ids" in nested:
                    merged["source_ids"] = nested["source_ids"]
                elif "source_citations" in nested:
                    merged["source_ids"] = nested["source_citations"]
            return merged
        return data

    @model_validator(mode="after")
    def validate_archetypes(self) -> "StrategyProfile":
        if self.archetype is not None and self.archetype not in VALID_ARCHETYPES:
            raise ValueError(f"invalid archetype: {self.archetype}")
        if self.archetype_secondary is not None and self.archetype_secondary not in VALID_ARCHETYPES:
            raise ValueError(f"invalid archetype_secondary: {self.archetype_secondary}")
        if not self.stated_strategic_priorities:
            raise ValueError("stated_strategic_priorities cannot be empty")
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
    """
    Flexible playbook entry accepting both:
    - SKILL.md PascalCase field names (What_Was_Done, Observed_Metric_Impact, etc.)
    - Snake_case field names that agents actually produce (what_was_done, metric_impact, etc.)
    - Anti-pattern entries (anti_id instead of play_id)

    The only hard requirement: at least one ID field must be present.
    """
    # ID fields — play_id is the canonical name; Play_ID accepted via alias; anti_id for anti-patterns
    play_id: Optional[str] = Field(default=None)
    anti_id: Optional[str] = Field(default=None)

    # PascalCase fields (SKILL.md mandatory field names & test fixture)
    Play_ID: Optional[str] = Field(default=None)
    What_Was_Done: Optional[str] = Field(default=None)
    Observed_Metric_Impact: Optional[str] = Field(default=None)
    Prerequisites: Optional[list[str]] = Field(default=None)
    # Some test fixtures / agents use Preconditions as an alias for Prerequisites
    Preconditions: Optional[list[str]] = Field(default=None)
    Operational_And_Tech_Prerequisites: Optional[list[str]] = Field(default=None)
    Execution_Burden: Optional[str] = Field(default=None)
    Time_To_Build: Optional[str] = Field(default=None)
    Margin_Risk: Optional[str] = Field(default=None)
    Failure_Modes_And_Margin_Destroyers: Optional[list[str]] = Field(default=None)
    Transferability_Constraints: Optional[list[str]] = Field(default=None)
    Archetype_Relevance: Optional[str] = Field(default=None)
    Evidence_Strength: Optional[str] = Field(default=None)
    Recommendation_For_PAX: Optional[str] = Field(default=None)
    PAX_Relevance: Optional[PAXRelevance] = Field(default=None)

    # Snake_case fields (actual agent output)
    what_was_done: Optional[str] = Field(default=None)
    metric_impact: Optional[str] = Field(default=None)
    prerequisites: Optional[list[str]] = Field(default=None)
    risks_limitations: Optional[list[str]] = Field(default=None)

    # Common supplemental fields from actual output
    play_name: Optional[str] = None
    anti_name: Optional[str] = None
    description: Optional[str] = None
    firms_executed: Optional[list[str]] = None
    firms_attempted: Optional[list[str]] = None
    negative_outcome: Optional[str] = None
    why_it_failed: Optional[str] = None
    action_citations: Optional[list[str]] = None
    source_citations: Optional[list[str]] = None

    model_config = {"extra": "ignore"}

    def resolved_play_id(self) -> Optional[str]:
        """Return whichever ID field is populated."""
        return self.play_id or self.Play_ID or self.anti_id

    @model_validator(mode="after")
    def validate_entry(self) -> "PlaybookEntry":
        if self.resolved_play_id() is None:
            raise ValueError("PlaybookEntry must have play_id, Play_ID, or anti_id")
        if self.Evidence_Strength is not None and self.Evidence_Strength not in VALID_CONFIDENCE_LABELS:
            raise ValueError("invalid Evidence_Strength")
        return self


class RankedRecommendation(BaseModel):
    play_id: str
    priority_rank: int = Field(ge=1)
    applicability: str
    strategic_principle: str
    rationale: str
    adaptation_notes: Optional[str] = None
    why_this_matters_for_pax: str
    what_must_be_true: list[str]
    why_this_may_fail_for_pax: list[str]
    implementation_pathway: list[str]
    feasibility_horizon: str

    @model_validator(mode="after")
    def validate_recommendation(self) -> "RankedRecommendation":
        if self.applicability not in {
            "directly_applicable",
            "requires_adaptation",
            "not_applicable",
        }:
            raise ValueError("invalid applicability")
        if self.feasibility_horizon not in VALID_FEASIBILITY_HORIZONS:
            raise ValueError("invalid feasibility_horizon")
        if not self.what_must_be_true or not self.why_this_may_fail_for_pax:
            raise ValueError("recommendation arrays cannot be empty")
        if not self.implementation_pathway:
            raise ValueError("implementation_pathway cannot be empty")
        return self


class GovernanceCascade(BaseModel):
    board: list[str]
    management: list[str]
    business_units: list[str]


class PlayAssessmentEntry(BaseModel):
    """
    Flexible play/anti-pattern assessment as produced by target-lens agent.
    Fields: play_id/anti_id, applicability, rationale, adaptation_notes,
    priority, implementation_pathway (for plays); relevance_to_pax, assessment,
    defensive_actions (for anti-patterns).
    """
    play_id: Optional[str] = None
    anti_id: Optional[str] = None
    play_name: Optional[str] = None
    anti_name: Optional[str] = None
    applicability: Optional[str] = None
    rationale: Optional[str] = None
    adaptation_notes: Optional[str] = None
    priority: Optional[str] = None
    implementation_pathway: Optional[list[str]] = None
    relevance_to_pax: Optional[str] = None
    assessment: Optional[str] = None
    defensive_actions: Optional[list[str]] = None

    model_config = {"extra": "ignore"}

    def resolved_id(self) -> Optional[str]:
        return self.play_id or self.anti_id

    @model_validator(mode="after")
    def validate_has_id(self) -> "PlayAssessmentEntry":
        if self.resolved_id() is None:
            raise ValueError("PlayAssessmentEntry must have play_id or anti_id")
        return self


class PlayAssessments(BaseModel):
    """Container for the play_assessments block in actual target_company_lens output."""
    platform_plays: Optional[list[PlayAssessmentEntry]] = None
    asset_class_plays: Optional[list[PlayAssessmentEntry]] = None
    anti_pattern_assessments: Optional[list[PlayAssessmentEntry]] = None

    model_config = {"extra": "ignore"}


class PAXLensContract(BaseModel):
    """
    Accept both:
    - The SKILL.md/test-fixture structure: ranked_recommendations + decision_risks + governance_cascade
    - The actual agent output structure: play_assessments + strategic_guidance
    At least one form of play data must be present.

    Also handles the metadata-wrapped format from actual agent output where
    target_company and target_ticker are inside a 'metadata' sub-object.
    """
    target_company: str
    target_ticker: str

    # SKILL.md ideal / test-fixture structure
    ranked_recommendations: Optional[list[RankedRecommendation]] = None
    decision_risks: Optional[list[str]] = None
    governance_cascade: Optional[GovernanceCascade] = None

    # Actual agent output structure
    play_assessments: Optional[PlayAssessments] = None
    strategic_guidance: Optional[Any] = None

    model_config = {"extra": "ignore"}

    @model_validator(mode="before")
    @classmethod
    def unwrap_metadata(cls, data: Any) -> Any:
        """
        Handle actual agent output format where target_company and target_ticker
        are nested inside a 'metadata' sub-object rather than at the top level.
        """
        if isinstance(data, dict) and "metadata" in data and isinstance(data["metadata"], dict):
            meta = data["metadata"]
            merged = dict(data)
            if "target_company" not in merged and "target_company" in meta:
                merged["target_company"] = meta["target_company"]
            if "target_ticker" not in merged and "target_ticker" in meta:
                merged["target_ticker"] = meta["target_ticker"]
            return merged
        return data

    @model_validator(mode="after")
    def validate_has_play_data(self) -> "PAXLensContract":
        has_ranked = bool(self.ranked_recommendations)
        has_assessments = (
            self.play_assessments is not None
            and (
                bool(self.play_assessments.platform_plays)
                or bool(self.play_assessments.asset_class_plays)
            )
        )
        if not has_ranked and not has_assessments:
            raise ValueError(
                "PAXLensContract must have ranked_recommendations or "
                "play_assessments.platform_plays/asset_class_plays"
            )
        return self


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


class DriverRankingEntry(BaseModel):
    """
    Single entry in driver_ranking.json.

    Two valid formats:
    - Simple format (test fixture / SKILL.md contract): flat fields including
      mechanical_overlap_flag, coverage_quality, comparability_quality,
      independence_flag, p_value_method — all required when this format is used.
    - Rich format (actual agent output): nested per_multiple stats with avg_abs_rho,
      independent_signal, quartile_analysis — mechanical_overlap_flag is not required
      because governance is encoded per-multiple.

    Detection: if 'avg_abs_rho' is present, treat as rich format (optional fields).
    If 'avg_abs_rho' is absent, treat as simple format (required fields).
    """
    driver_id: str
    correlation_classification: str
    confidence_class: str

    # Fields required in simple format, optional in rich format
    coverage_quality: Optional[str] = None
    comparability_quality: Optional[str] = None
    mechanical_overlap_flag: Optional[bool] = None
    independence_flag: Optional[str] = None
    p_value_method: Optional[str] = None
    confirmatory_badge: Optional[str] = None

    # Rich format fields
    avg_abs_rho: Optional[float] = None
    independent_signal: Optional[bool] = None
    per_multiple: Optional[Any] = None

    model_config = {"extra": "ignore"}

    @model_validator(mode="after")
    def validate_governance_fields(self) -> "DriverRankingEntry":
        is_rich_format = self.avg_abs_rho is not None
        if not is_rich_format:
            # Simple format: governance fields are required
            missing = []
            if self.coverage_quality is None:
                missing.append("coverage_quality")
            if self.comparability_quality is None:
                missing.append("comparability_quality")
            if self.mechanical_overlap_flag is None:
                missing.append("mechanical_overlap_flag")
            if self.independence_flag is None:
                missing.append("independence_flag")
            if self.p_value_method is None:
                missing.append("p_value_method")
            if missing:
                raise ValueError(
                    f"driver_ranking entry {self.driver_id} is missing required statistical "
                    f"governance fields: {', '.join(missing)}"
                )
        return self


class DriverRankingContract(BaseModel):
    drivers: list[DriverRankingEntry]

    model_config = {"extra": "ignore"}


class DriverPlaybook(BaseModel):
    driver_id: str
    plays: list[PlaybookEntry]
    anti_patterns: list[PlaybookEntry] = Field(default_factory=list)

    model_config = {"extra": "ignore"}


class PlatformPlaybookContract(BaseModel):
    driver_playbooks: list[DriverPlaybook]

    model_config = {"extra": "ignore"}


class DriverPlays(BaseModel):
    """Actual agent output: plays organised by driver, nested inside a vertical."""
    driver_id: str
    plays: list[PlaybookEntry] = Field(default_factory=list)
    anti_patterns: list[PlaybookEntry] = Field(default_factory=list)

    model_config = {"extra": "ignore"}


class VerticalPlaybook(BaseModel):
    vertical_id: str
    # Test-fixture uses plays directly at the vertical level
    plays: Optional[list[PlaybookEntry]] = None
    anti_patterns: Optional[list[PlaybookEntry]] = Field(default_factory=list)
    # Actual agent output nests plays inside driver_plays
    driver_plays: Optional[list[DriverPlays]] = None

    model_config = {"extra": "ignore"}

    @model_validator(mode="after")
    def validate_has_content(self) -> "VerticalPlaybook":
        has_plays = bool(self.plays)
        has_driver_plays = bool(self.driver_plays)
        if not has_plays and not has_driver_plays:
            raise ValueError(f"vertical {self.vertical_id} must have plays or driver_plays")
        return self


class AssetClassPlaybookContract(BaseModel):
    # Test-fixture field name
    vertical_playbooks: Optional[list[VerticalPlaybook]] = None
    # Actual agent output field name
    verticals: Optional[list[VerticalPlaybook]] = None

    model_config = {"extra": "ignore"}

    @model_validator(mode="after")
    def validate_has_verticals(self) -> "AssetClassPlaybookContract":
        if not self.vertical_playbooks and not self.verticals:
            raise ValueError("asset_class_playbooks must contain at least one vertical")
        return self

    def all_verticals(self) -> list[VerticalPlaybook]:
        return (self.vertical_playbooks or []) + (self.verticals or [])


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
    """
    Validate strategy_profiles.json.
    Accepts:
    - a bare JSON array of profile objects
    - a dict with a 'profiles' key containing the array (actual agent output wraps metadata + profiles)
    """
    data = _load_json(path)
    if isinstance(data, dict):
        if "profiles" in data:
            data = data["profiles"]
        else:
            raise ValueError(f"{path}: expected a JSON array or a dict with a 'profiles' key")
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

    # statistics_metadata.json is produced by metric-architect in step 2.
    # Some runs may not include it (e.g. when only later steps are re-run).
    # When present it is strictly validated; when absent the validator skips
    # downstream cross-checks that depend on it.
    stats_metadata_path = run_dir / "3-analysis" / "statistics_metadata.json"
    stats_metadata: Optional[StatisticalGovernance] = None
    if stats_metadata_path.exists():
        stats_metadata = _validate_model(StatisticalGovernance, stats_metadata_path)

    # Validate driver_ranking.json if present — mechanical_overlap_flag and independence_flag
    # are required fields that catch statistical governance violations.
    driver_ranking_path = run_dir / "3-analysis" / "driver_ranking.json"
    if driver_ranking_path.exists():
        _validate_model(DriverRankingContract, driver_ranking_path)

    # report_metadata.json is optional — the SKILL.md does not instruct any agent to produce it.
    # If the file exists, validate it and run cross-checks; if absent, skip silently.
    report_metadata_path = run_dir / "5-playbook" / "report_metadata.json"
    report_metadata: Optional[ReportMetadata] = None
    if report_metadata_path.exists():
        report_metadata = _validate_model(ReportMetadata, report_metadata_path)

    platform_playbook = _validate_model(
        PlatformPlaybookContract, run_dir / "5-playbook" / "platform_playbook.json"
    )
    asset_playbook = _validate_model(
        AssetClassPlaybookContract, run_dir / "5-playbook" / "asset_class_playbooks.json"
    )
    pax_lens = _validate_model(PAXLensContract, run_dir / "5-playbook" / "target_company_lens.json")

    if report_metadata is not None:
        if stats_metadata is not None:
            _cross_check_statistics(stats_metadata, report_metadata)
        if report_metadata.target_ticker != pax_lens.target_ticker:
            raise ValueError("target_ticker mismatch between report metadata and PAX lens")
        if report_metadata.target_company != pax_lens.target_company:
            raise ValueError("target_company mismatch between report metadata and PAX lens")

    if not platform_playbook.driver_playbooks:
        raise ValueError("platform_playbook must contain at least one driver_playbook")
    if not asset_playbook.all_verticals():
        raise ValueError("asset_class_playbooks must contain at least one vertical")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a VDA run directory against the PAX-first contract.")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args(argv)

    validate_run_directory(args.run_dir)
    print(f"Validated {args.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
