"""Shared data structures and utilities for VDA analyzer modules.

This module provides common building blocks used by metric_checklist.py and
delta_spec.py to avoid code duplication.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FirmRecord:
    firm_id: str
    firm_name: str
    ticker: str
    aum_usd_bn: float


def split_firms_into_tiers(
    firms: list[FirmRecord],
) -> tuple[list[FirmRecord], list[FirmRecord], list[FirmRecord]]:
    """Split a list pre-sorted by descending AUM into three roughly equal tiers."""
    n = len(firms)
    tier_size = n // 3
    extra = n % 3
    # tier1 gets extra if n not divisible by 3
    t1_end = tier_size + (1 if extra >= 1 else 0)
    t2_end = t1_end + tier_size + (1 if extra >= 2 else 0)
    return firms[:t1_end], firms[t1_end:t2_end], firms[t2_end:]


def load_firms_from_payload(payload: dict[str, object]) -> list[FirmRecord]:
    """Parse a peer_universe dict and return a list of FirmRecord sorted by AUM descending."""
    firms: list[FirmRecord] = []
    for item in payload.get("universe", []):
        if not isinstance(item, dict):
            continue
        firms.append(
            FirmRecord(
                firm_id=str(item.get("firm_id", "")).strip(),
                firm_name=str(item.get("firm_name", "")).strip(),
                ticker=str(item.get("ticker", "")).strip(),
                aum_usd_bn=float(item.get("latest_aum_usd_bn", 0.0)),
            )
        )
    firms.sort(key=lambda f: f.aum_usd_bn, reverse=True)
    return firms
