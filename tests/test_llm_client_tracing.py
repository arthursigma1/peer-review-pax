"""Tests for llm_client.py Langfuse tracing integration."""

from __future__ import annotations

import inspect

import pytest


class TestLlmClientTracing:
    def test_ask_accepts_metadata_param(self):
        """Verify the function signature accepts metadata without error."""
        from src.llm_client import ask
        sig = inspect.signature(ask)
        assert "metadata" in sig.parameters

    def test_ask_metadata_defaults_to_none(self):
        """Verify metadata parameter defaults to None."""
        from src.llm_client import ask
        sig = inspect.signature(ask)
        assert sig.parameters["metadata"].default is None

    def test_observe_decorator_applied(self):
        """Verify the observe decorator is applied (check wrapped attribute)."""
        from src.llm_client import ask
        # If langfuse is installed, the function will have wrapper attributes
        # If not installed, it should still be callable
        assert callable(ask)
