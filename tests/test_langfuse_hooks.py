"""Tests for Langfuse hook utilities."""

from __future__ import annotations

import os
import sys
from importlib import reload
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks dir to sys.path for importing langfuse_utils
_HOOKS_DIR = str(Path(__file__).resolve().parent.parent / ".claude" / "hooks")


@pytest.fixture(autouse=True)
def _hooks_path():
    """Ensure hooks dir is on sys.path and module is freshly imported."""
    if _HOOKS_DIR not in sys.path:
        sys.path.insert(0, _HOOKS_DIR)
    yield
    # Clean up module cache so each test gets a fresh import
    sys.modules.pop("langfuse_utils", None)


def _import_utils():
    """Import (or reimport) langfuse_utils with a clean module cache."""
    sys.modules.pop("langfuse_utils", None)
    import langfuse_utils
    return langfuse_utils


class TestIsTracingEnabled:
    def test_enabled_when_env_true(self):
        with patch.dict(os.environ, {"TRACE_TO_LANGFUSE": "true"}):
            utils = _import_utils()
            assert utils.is_tracing_enabled() is True

    def test_disabled_when_env_false(self):
        with patch.dict(os.environ, {"TRACE_TO_LANGFUSE": "false"}):
            utils = _import_utils()
            assert utils.is_tracing_enabled() is False

    def test_disabled_when_env_missing(self):
        env = {k: v for k, v in os.environ.items() if k != "TRACE_TO_LANGFUSE"}
        with patch.dict(os.environ, env, clear=True):
            utils = _import_utils()
            assert utils.is_tracing_enabled() is False

    def test_enabled_case_insensitive(self):
        with patch.dict(os.environ, {"TRACE_TO_LANGFUSE": "True"}):
            utils = _import_utils()
            assert utils.is_tracing_enabled() is True


class TestDetectAgentName:
    def test_detects_from_correlation_results(self):
        utils = _import_utils()
        assert utils.detect_agent_name(["3-analysis/correlation_results.json"]) == "metric-architect"

    def test_detects_from_driver_ranking(self):
        utils = _import_utils()
        assert utils.detect_agent_name(["3-analysis/driver_ranking.json"]) == "metric-architect"

    def test_detects_from_platform_playbook(self):
        utils = _import_utils()
        assert utils.detect_agent_name(["5-playbook/platform_playbook.json"]) == "playbook-synthesizer"

    def test_detects_from_target_lens(self):
        utils = _import_utils()
        assert utils.detect_agent_name(["5-playbook/target_lens.json"]) == "target-lens"

    def test_detects_from_final_report(self):
        utils = _import_utils()
        assert utils.detect_agent_name(["5-playbook/final_report.html"]) == "report-builder"

    def test_returns_unknown_for_unrecognized(self):
        utils = _import_utils()
        assert utils.detect_agent_name(["random.json"]) == "unknown"

    def test_returns_unknown_for_empty_list(self):
        utils = _import_utils()
        assert utils.detect_agent_name([]) == "unknown"

    def test_first_match_wins(self):
        utils = _import_utils()
        result = utils.detect_agent_name(["5-playbook/target_lens.json", "5-playbook/final_report.html"])
        assert result == "target-lens"


class TestGetLangfuseClient:
    def test_returns_none_when_langfuse_not_installed(self):
        utils = _import_utils()
        with patch.dict("sys.modules", {"langfuse": None}):
            assert utils.get_langfuse_client() is None
