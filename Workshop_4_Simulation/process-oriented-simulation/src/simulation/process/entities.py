"""
entities.py — Core domain objects for the Food Waste Reduction Platform simulation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ── State machine ──────────────────────────────────────────────────────────────

class SurplusState(str, Enum):
    POSTED    = "POSTED"
    IN_QUEUE  = "IN_QUEUE"
    ASSIGNED  = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    NO_SHOW   = "NO_SHOW"
    EXPIRED   = "EXPIRED"


# ── State transition log entry ─────────────────────────────────────────────────

@dataclass
class StateTransition:
    timestamp:        float           # minutes since 07:00
    state:            str             # SurplusState value
    assigned_user_id: Optional[int]
    kg:               float
    retry_count:      int = 0         # surplus.retry_count at transition time


# ── Core entities ──────────────────────────────────────────────────────────────

@dataclass
class Surplus:
    id:          int
    donor_id:    int
    kg:          float
    posted_at:   float               # minutes since 07:00
    expiry_at:   float               # posted_at + pickup window (1–3 h)
    state:       SurplusState        = SurplusState.POSTED
    retry_count: int                 = 0
    assigned_to: Optional[int]       = None
    state_log:   List[StateTransition] = field(default_factory=list)

    def log_transition(
        self,
        timestamp: float,
        state:     SurplusState,
        user_id:   Optional[int] = None,
    ) -> None:
        self.state = state
        self.state_log.append(
            StateTransition(
                timestamp=round(timestamp, 4),
                state=state.value,
                assigned_user_id=user_id,
                kg=self.kg,
                retry_count=self.retry_count,
            )
        )


@dataclass
class Donor:
    id:         int
    x:          float     # km east  of origin (Engineering Faculty, UD)
    y:          float     # km north of origin
    donor_type: str       # "cafeteria" | "restaurant"


@dataclass
class Recipient:
    id:               int
    x:                float
    y:                float
    reliability_score: float   # 0–100; +1 per pickup, -2 per no-show
    no_show_prob:      float   # sampled from scenario [no_show_min, no_show_max]
    is_charity:        bool
    tier:              int     # 1=≤0.5 km, 2=≤1 km, 3=≤3 km  (from origin)
    dist_from_center:  float   # km from origin — used for peripheral check

    @property
    def is_peripheral(self) -> bool:
        """REQ-11: peripheral = 2.5–3 km from platform centre."""
        return self.dist_from_center >= 2.5


# ── Spatial helpers ────────────────────────────────────────────────────────────

def euclidean_distance_km(ax: float, ay: float, bx: float, by: float) -> float:
    """Euclidean distance in km between two (x, y) coordinate pairs."""
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


def distance_tier(dist_km: float) -> int:
    """Map a distance from the platform centre to its notification / scoring tier.

    Tier 1: ≤ 0.5 km  (inner zone)
    Tier 2: ≤ 1.0 km  (mid zone)
    Tier 3: ≤ 3.0 km  (outer zone)
    """
    if dist_km <= 0.5:
        return 1
    elif dist_km <= 1.0:
        return 2
    return 3


def spatial_check(donor: Donor, recipient: Recipient) -> bool:
    """Returns True if donor–recipient distance is within the 3 km boundary."""
    return euclidean_distance_km(donor.x, donor.y, recipient.x, recipient.y) <= 3.0


def distance_tier(distance_km: float) -> int:
    """Classify a distance from origin into a notification tier."""
    if distance_km <= 0.5:
        return 1
    if distance_km <= 1.0:
        return 2
    return 3
