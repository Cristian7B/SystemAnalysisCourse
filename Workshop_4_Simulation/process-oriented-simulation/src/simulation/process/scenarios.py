"""
scenarios.py — S01–S04 scenario configurations for Workshop 4.

S01 — Baseline   : Medium adoption, full mitigations, 25% no-show
S02 — Early Stage: Low adoption,    partial mitigations, 30% no-show
S03 — Stress Test: High adoption,   full mitigations, 15% no-show, ≥200 users
S04 — Risk Test  : Medium adoption, NO mitigations (staggered + reliability off)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ScenarioConfig:
    id:                        str
    name:                      str
    adoption:                  str    # "Low" | "Medium" | "High"
    no_show_prob:              float
    staggered_notifications:   bool   # risk mitigation tier 1 — disabled in S04
    reliability_scoring:       bool   # risk mitigation tier 2 — disabled in S04
    donor_count_range:         Tuple[int, int]
    recipient_individual_range: Tuple[int, int]
    charity_count_range:       Tuple[int, int]


S01 = ScenarioConfig(
    id="S01",
    name="Baseline",
    adoption="Medium",
    no_show_prob=0.25,
    staggered_notifications=True,
    reliability_scoring=True,
    donor_count_range=(10, 15),
    recipient_individual_range=(200, 280),
    charity_count_range=(7, 10),
)

S02 = ScenarioConfig(
    id="S02",
    name="Early Stage",
    adoption="Low",
    no_show_prob=0.30,
    staggered_notifications=True,
    reliability_scoring=False,   # partial mitigation — no reliability scoring
    donor_count_range=(5, 8),
    recipient_individual_range=(150, 200),
    charity_count_range=(5, 7),
)

S03 = ScenarioConfig(
    id="S03",
    name="Stress Test",
    adoption="High",
    no_show_prob=0.15,
    staggered_notifications=True,
    reliability_scoring=True,
    donor_count_range=(15, 20),
    recipient_individual_range=(300, 400),
    charity_count_range=(10, 12),
)

S04 = ScenarioConfig(
    id="S04",
    name="Risk Test",
    adoption="Medium",
    no_show_prob=0.25,
    staggered_notifications=False,  # mitigations DISABLED
    reliability_scoring=False,
    donor_count_range=(10, 15),
    recipient_individual_range=(200, 280),
    charity_count_range=(7, 10),
)

ALL_SCENARIOS: list = [S01, S02, S03, S04]
