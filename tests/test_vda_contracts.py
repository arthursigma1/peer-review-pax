import json
import tempfile
import unittest
from pathlib import Path

from src.validation.vda_contracts import validate_run_directory


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


class VDAContractsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.tmp.name)

        stats = {
            "discovery_method": "bh_fdr_q_0.10",
            "discovery_q": 0.10,
            "confirmatory_badge": "bonferroni_survivor",
            "p_value_method_primary": "permutation",
            "p_value_method_fallback": "asymptotic_t_with_disclosure",
            "stable_driver_rule_id": "stable_v1_two_of_three",
            "confidence_taxonomy": ["high", "moderate", "directional", "unsupported"],
            "sensitivity_protocol": [
                "leave_one_out",
                "matched_sample",
                "archetype_stratified",
                "coverage_and_comparability",
                "mechanical_overlap",
                "confounding_check",
                "panel_robustness"
            ],
            "n_effective": 25,
            "temporal_depth": {
                "target_range": "FY2022-FY2024",
                "mandatory_years": 2,
                "firms_with_multi_year": 20
            },
            "ci_method": "bootstrap_10k",
            "minimum_sample_rule": {
                "ranking_threshold": 12,
                "reporting_threshold": 8
            }
        }
        _write(self.run_dir / "3-analysis" / "statistics_metadata.json", stats)
        _write(
            self.run_dir / "2-data" / "strategy_profiles.json",
            [
                {
                    "firm_id": "FIRM-001",
                    "firm_ticker": "BX",
                    "archetype": "north_star_peer",
                    "archetype_secondary": "adjacent_peer",
                    "ontology_mapping": {
                        "geographical_reach": ["global"],
                        "business_focus": ["alternatives-platform"],
                        "asset_focus": ["multi-asset"],
                    },
                    "contextual_market_factors": {
                        "tam": "Large institutional and wealth alternatives market",
                        "market_share": "Leading",
                        "governance": "Mature public-company governance",
                        "regulation": "Multi-jurisdictional",
                    },
                    "stated_strategic_priorities": [
                        "Expand fee-bearing perpetual capital",
                        "Improve distribution mix",
                    ],
                    "source_ids": ["PS-VD-001"],
                    "missing_dimensions": [],
                }
            ],
        )
        _write(
            self.run_dir / "2-data" / "strategic_actions.json",
            {
                "actions": [
                    {
                        "action_id": "ACT-001",
                        "firm_ticker": "BX",
                        "strategy_sub_type": "perpetual-capital",
                        "thematic_focus": "wealth-distribution",
                        "economic_model": "fee-bearing",
                        "what_was_done": "Launched an evergreen vehicle through an existing distribution channel.",
                        "observed_metric_impact": "Increased permanent capital and fee durability.",
                        "operational_prerequisites": [
                            {
                                "requirement": "Upgrade reporting controls",
                                "evidence_class": "corroborated",
                                "source_bias_tag": "regulatory-filing",
                                "confidence_level": "moderate",
                                "stated_or_inferred": "stated",
                            }
                        ],
                    }
                ]
            },
        )
        _write(
            self.run_dir / "3-analysis" / "correlations.json",
            {
                "correlations": [
                    {
                        "correlation_id": "COR-001",
                        "driver_metric_id": "MET-001",
                        "valuation_multiple": "P/FRE",
                        "spearman_rho": 0.63,
                        "p_value": 0.01,
                        "n_firms_included": 14,
                        "coverage_quality": "adequate",
                        "comparability_quality": "good",
                        "mechanical_overlap_flag": False,
                        "independence_flag": "independent",
                        "p_value_method": "permutation",
                        "confirmatory_badge": None,
                    }
                ]
            },
        )
        _write(
            self.run_dir / "3-analysis" / "driver_ranking.json",
            {
                "drivers": [
                    {
                        "driver_id": "DVR-001",
                        "correlation_classification": "stable_value_driver",
                        "confidence_class": "moderate",
                        "coverage_quality": "adequate",
                        "comparability_quality": "good",
                        "mechanical_overlap_flag": False,
                        "independence_flag": "independent",
                        "p_value_method": "permutation",
                        "confirmatory_badge": "bonferroni_survivor",
                    }
                ]
            },
        )
        _write(
            self.run_dir / "4-deep-dives" / "asset_class_analysis.json",
            {
                "strategy_subtype_analyses": [
                    {
                        "vertical": "Credit",
                        "strategy_sub_type": "Direct Lending",
                        "thematic_focus": "Upper middle market",
                        "economic_model": "Recurring management fees with episodic performance fees",
                        "value_creation_mechanics": "Origination scale and underwriting discipline support durable fee-bearing AUM.",
                        "fee_model": "Management fees plus incentive economics on selected vehicles.",
                        "operating_model": "Centralized underwriting with local origination coverage.",
                        "tech_data_reporting_requirements": [
                            "Borrower monitoring stack",
                            "LP reporting controls",
                        ],
                        "scaling_constraints": [
                            "Origination talent capacity",
                            "Credit-cycle discipline",
                        ],
                        "margin_sensitivities": [
                            "Comp ratio for deal teams",
                            "Servicing complexity",
                        ],
                        "pax_transferability_barriers": [
                            "Requires scaled credit underwriting and reporting controls",
                        ],
                    }
                ]
            },
        )
        _write(
            self.run_dir / "5-playbook" / "report_metadata.json",
            {
                "report_mode": "pax_decision_memo",
                "default_synthesis": "pax_first",
                "target_company": "Patria Investments Limited",
                "target_ticker": "PAX",
                "peer_evidence_layer_present": True,
                "pax_interpretation_layer_present": True,
                "pax_decision_layer_present": True,
                "statistical_governance": stats,
            },
        )
        play = {
            "Play_ID": "PLAY-001",
            "What_Was_Done": "Built a permanent capital credit vehicle.",
            "Observed_Metric_Impact": "Improved fee durability and margin resilience.",
            "Why_It_Worked": "Matched product structure to client liquidity needs.",
            "PAX_Relevance": {
                "scale_fit": 3,
                "geography_fit": 4,
                "client_distribution_fit": 4,
                "balance_sheet_fit": 3,
                "regulatory_fit": 3,
                "operating_model_fit": 4,
                "tech_readiness": 3,
                "data_reporting_readiness": 3,
                "time_to_build": 3,
                "capital_intensity": 3,
                "margin_risk": 2,
                "execution_complexity": 3,
                "feasibility_horizon": "medium_term_feasible",
            },
            "Preconditions": ["A credit platform with repeat issuance capacity"],
            "Operational_And_Tech_Prerequisites": ["Daily or periodic valuation controls"],
            "Execution_Burden": "Moderate multi-year build.",
            "Time_To_Build": "18-24 months",
            "Margin_Risk": "Medium due to channel economics.",
            "Failure_Modes_And_Margin_Destroyers": ["Fee-rate dilution"],
            "Transferability_Constraints": ["Requires stronger reporting stack"],
            "Archetype_Relevance": "near_peer",
            "Evidence_Strength": "moderate",
            "Recommendation_For_PAX": "Pursue only after Solis reporting integration is stable."
        }
        _write(
            self.run_dir / "5-playbook" / "platform_playbook.json",
            {"driver_playbooks": [{"driver_id": "DVR-001", "plays": [play], "anti_patterns": [play]}]},
        )
        _write(
            self.run_dir / "5-playbook" / "asset_class_playbooks.json",
            {"vertical_playbooks": [{"vertical_id": "VERT-001", "plays": [play], "anti_patterns": []}]},
        )
        _write(
            self.run_dir / "5-playbook" / "target_company_lens.json",
            {
                "target_company": "Patria Investments Limited",
                "target_ticker": "PAX",
                "ranked_recommendations": [
                    {
                        "play_id": "PLAY-001",
                        "priority_rank": 1,
                        "applicability": "requires_adaptation",
                        "strategic_principle": "Durable fee-bearing capital tends to support stronger valuation outcomes.",
                        "rationale": "The principle is relevant, but PAX would need to adapt distribution and reporting infrastructure.",
                        "adaptation_notes": "Use a phased launch and upgrade reporting before broad distribution.",
                        "why_this_matters_for_pax": "Improves fee durability.",
                        "what_must_be_true": ["Reporting stack upgraded"],
                        "why_this_may_fail_for_pax": ["Distribution channel adoption too slow"],
                        "implementation_pathway": ["Upgrade reporting controls", "Pilot vehicle design", "Phase distribution rollout"],
                        "feasibility_horizon": "medium_term_feasible",
                    }
                ],
                "decision_risks": ["Execution complexity"],
                "governance_cascade": {
                    "board": ["Approve sequencing"],
                    "management": ["Build underwriting controls"],
                    "business_units": ["Launch product design work"],
                },
            },
        )
        (
            self.run_dir / "5-playbook" / "final_report.html"
        ).write_text(
            "<html><body><h1>Patria Investments Limited (PAX)</h1><p>PAX decision memo.</p></body></html>"
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_validate_run_directory_passes_for_valid_contract(self) -> None:
        validate_run_directory(self.run_dir)

    def test_validate_run_directory_fails_on_metadata_drift(self) -> None:
        report_metadata = json.loads((self.run_dir / "5-playbook" / "report_metadata.json").read_text())
        report_metadata["statistical_governance"]["discovery_method"] = "bonferroni"
        (self.run_dir / "5-playbook" / "report_metadata.json").write_text(json.dumps(report_metadata))
        with self.assertRaises(ValueError):
            validate_run_directory(self.run_dir)

    def test_minimum_sample_rule_ranking_threshold_must_be_12(self) -> None:
        stats = json.loads((self.run_dir / "3-analysis" / "statistics_metadata.json").read_text())
        stats["minimum_sample_rule"]["ranking_threshold"] = 10
        report = json.loads((self.run_dir / "5-playbook" / "report_metadata.json").read_text())
        report["statistical_governance"]["minimum_sample_rule"]["ranking_threshold"] = 10
        _write(self.run_dir / "3-analysis" / "statistics_metadata.json", stats)
        _write(self.run_dir / "5-playbook" / "report_metadata.json", report)
        with self.assertRaises(ValueError):
            validate_run_directory(self.run_dir)

    def test_n_effective_must_be_at_least_12(self) -> None:
        stats = json.loads((self.run_dir / "3-analysis" / "statistics_metadata.json").read_text())
        stats["n_effective"] = 8
        report = json.loads((self.run_dir / "5-playbook" / "report_metadata.json").read_text())
        report["statistical_governance"]["n_effective"] = 8
        _write(self.run_dir / "3-analysis" / "statistics_metadata.json", stats)
        _write(self.run_dir / "5-playbook" / "report_metadata.json", report)
        with self.assertRaises(ValueError):
            validate_run_directory(self.run_dir)

    def test_panel_robustness_required_in_sensitivity_protocol(self) -> None:
        stats = json.loads((self.run_dir / "3-analysis" / "statistics_metadata.json").read_text())
        stats["sensitivity_protocol"] = [
            "leave_one_out", "matched_sample", "archetype_stratified",
            "coverage_and_comparability", "mechanical_overlap", "confounding_check"
        ]  # missing panel_robustness
        report = json.loads((self.run_dir / "5-playbook" / "report_metadata.json").read_text())
        report["statistical_governance"]["sensitivity_protocol"] = stats["sensitivity_protocol"]
        _write(self.run_dir / "3-analysis" / "statistics_metadata.json", stats)
        _write(self.run_dir / "5-playbook" / "report_metadata.json", report)
        with self.assertRaises(ValueError):
            validate_run_directory(self.run_dir)

    def test_driver_ranking_missing_statistical_flags_fails(self) -> None:
        ranking = json.loads((self.run_dir / "3-analysis" / "driver_ranking.json").read_text())
        del ranking["drivers"][0]["mechanical_overlap_flag"]
        _write(self.run_dir / "3-analysis" / "driver_ranking.json", ranking)
        with self.assertRaises(ValueError):
            validate_run_directory(self.run_dir)

    def test_legacy_strategy_profiles_wrapper_fails(self) -> None:
        wrapped = {
            "metadata": {"legacy": True},
            "profiles": json.loads((self.run_dir / "2-data" / "strategy_profiles.json").read_text()),
        }
        _write(self.run_dir / "2-data" / "strategy_profiles.json", wrapped)
        with self.assertRaises(ValueError):
            validate_run_directory(self.run_dir)

    def test_legacy_target_lens_shape_fails(self) -> None:
        _write(
            self.run_dir / "5-playbook" / "target_company_lens.json",
            {
                "target_company": "Patria Investments Limited",
                "target_ticker": "PAX",
                "play_assessments": {
                    "platform_plays": [
                        {
                            "play_id": "PLAY-001",
                            "applicability": "requires_adaptation",
                            "rationale": "Legacy shape should be rejected by the strict contract.",
                        }
                    ]
                },
                "strategic_guidance": {},
            },
        )
        with self.assertRaises(ValueError):
            validate_run_directory(self.run_dir)


if __name__ == "__main__":
    unittest.main()
