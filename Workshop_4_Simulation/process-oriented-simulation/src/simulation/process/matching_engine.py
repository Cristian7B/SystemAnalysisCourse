"""
matching_engine.py — Single-resource serialized matching engine (SimPy Resource, capacity=1).

Design constraints (from Workshop 2 / Workshop 3):
  - FIFO + Priority queue: enforced by SimPy's default resource queue
  - Only ONE assignment processed at a time (prevents race conditions)
  - Service time ~ Normal(mean=1.0 s, σ=0.3 s), clipped to [0.1, 2.0] s
  - REQ-03: surpluses ≥ 10 kg must be offered to charities first
  - REQ-11: peripheral users (≥ 2.5 km from centre) receive fairness boost

Composite scoring:
    score = 0.50 × dist_score + 0.30 × fairness_score + 0.20 × charity_weight
    dist_score   = 1 − (dist_km / 3.0)          ← linear [0, 1]
    fairness     = 0.8 (tier 3) | 0.5 (tier 2) | 0.2 (tier 1)
    charity_weight = 1.0 if is_charity else 0.0
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import simpy

from entities import Donor, Recipient, Surplus, euclidean_distance_km

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_RETRIES: int        = 3
LARGE_SURPLUS_KG: float = 10.0

_SERVICE_MEAN_S: float  = 1.0
_SERVICE_STD_S: float   = 0.3
_SERVICE_MIN_S: float   = 0.1
_SERVICE_MAX_S: float   = 2.0

_FAIRNESS: Dict[int, float] = {1: 0.2, 2: 0.5, 3: 0.8}


# ── Engine ────────────────────────────────────────────────────────────────────

class MatchingEngine:
    """
    Wraps a SimPy Resource(capacity=1).

    Call `env.process(engine.match(..., result))` from a surplus lifecycle process.
    The result dict will have keys:
        "recipient"  → Recipient | None
        "service_s"  → float (actual service time in seconds)
    """

    def __init__(self, env: simpy.Environment, metrics: Any) -> None:
        self.env      = env
        self.resource = simpy.Resource(env, capacity=1)
        self.metrics  = metrics

    # ── Scoring ───────────────────────────────────────────────────────────────

    def _score(self, donor: Donor, recipient: Recipient) -> float:
        dist = euclidean_distance_km(donor.x, donor.y, recipient.x, recipient.y)
        if dist > 3.0:
            return -1.0
        dist_score    = 1.0 - (dist / 3.0)               # linear ∈ [0, 1]
        fairness      = _FAIRNESS.get(recipient.tier, 0.2)
        charity_weight = 1.0 if recipient.is_charity else 0.0
        return 0.50 * dist_score + 0.30 * fairness + 0.20 * charity_weight

    # ── Best-match selection ──────────────────────────────────────────────────

    def find_best_match(
        self,
        surplus:             Surplus,
        donor:               Donor,
        recipients:          List[Recipient],
        reliability_scoring: bool,
    ) -> Optional[Recipient]:
        # Filter by 3 km boundary (PostGIS ST_DWithin equivalent)
        candidates = [
            r for r in recipients
            if euclidean_distance_km(donor.x, donor.y, r.x, r.y) <= 3.0
        ]
        if not candidates:
            return None

        # REQ-03: surpluses ≥ 10 kg → restrict to charities if any are available
        if surplus.kg >= LARGE_SURPLUS_KG:
            charity_cands = [r for r in candidates if r.is_charity]
            if charity_cands:
                candidates = charity_cands

        def sort_key(r: Recipient) -> float:
            base = self._score(donor, r)
            if reliability_scoring:
                # Reliability score acts as a tiebreaker (small weight)
                base += 0.001 * (r.reliability_score / 100.0)
            return base

        return max(candidates, key=sort_key)

    # ── SimPy process ─────────────────────────────────────────────────────────

    def match(
        self,
        surplus:             Surplus,
        donor:               Donor,
        recipients:          List[Recipient],
        reliability_scoring: bool,
        result:              Dict[str, Any],
    ):
        """
        SimPy generator — must be started with env.process().

        Requests the single-capacity resource, simulates matching service time,
        then stores the best recipient (or None) in `result["recipient"]`.
        """
        with self.resource.request() as req:
            yield req

            service_s = float(
                np.clip(
                    np.random.normal(_SERVICE_MEAN_S, _SERVICE_STD_S),
                    _SERVICE_MIN_S,
                    _SERVICE_MAX_S,
                )
            )
            service_min = service_s / 60.0
            yield self.env.timeout(service_min)

            self.metrics.engine_busy_minutes += service_min

            result["recipient"] = self.find_best_match(
                surplus, donor, recipients, reliability_scoring
            )
            result["service_s"] = service_s
