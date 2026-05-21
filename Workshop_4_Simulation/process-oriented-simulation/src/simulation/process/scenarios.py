"""
scenarios.py — S01–S05 scenario configurations for Workshop 4.

S01 — Baseline     : Medium adoption, full mitigations,    no-show 10–25%
S02 — Early Stage  : Low adoption,    partial mitigations, no-show 10–30%
S03 — Stress Test  : High adoption,   full mitigations,    no-show 10–15%
S04 — Risk Test    : Medium adoption, NO staggered notif., no-show 25–45%
S05 — Sensitivity  : Medium adoption, full mitigations,    no-show 35–55%

Mitigation flags:
  staggered_notifications : True  in S01, S02, S03, S05 — False in S04
  reliability_scoring     : True  in S01, S03, S04, S05 — False in S02
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ScenarioConfig:
    id:                         str
    name:                       str
    adoption:                   str    # "Low" | "Medium" | "High"
    no_show_min:                float  # lower bound of per-recipient no-show prob
    no_show_max:                float  # upper bound of per-recipient no-show prob
    staggered_notifications:    bool   # wave-based dispatch — disabled in S04
    reliability_scoring:        bool   # score-adjusted no-show — disabled in S02
    donor_count_range:          Tuple[int, int]
    recipient_individual_range: Tuple[int, int]
    charity_count_range:        Tuple[int, int]


S01 = ScenarioConfig(
    id="S01",
    name="Baseline",
    adoption="Medium",
    no_show_min=0.10,
    no_show_max=0.25,
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
    no_show_min=0.10,
    no_show_max=0.30,
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
    no_show_min=0.10,
    no_show_max=0.15,
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
    no_show_min=0.25,
    no_show_max=0.45,
    staggered_notifications=False,  # staggered notifications DISABLED
    reliability_scoring=True,       # reliability scoring ON (isolates staggered value)
    donor_count_range=(10, 15),
    recipient_individual_range=(207, 290),
    charity_count_range=(7, 10),
)

S05 = ScenarioConfig(
    id="S05",
    name="Sensitivity",
    adoption="Medium",
    no_show_min=0.35,
    no_show_max=0.55,
    staggered_notifications=True,
    reliability_scoring=True,
    donor_count_range=(10, 15),
    recipient_individual_range=(207, 290),
    charity_count_range=(7, 10),
)

ALL_SCENARIOS: list = [S01, S02, S03, S04, S05]
