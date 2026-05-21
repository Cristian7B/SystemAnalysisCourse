"""
matching_engine.py — Single-resource serialized matching engine (SimPy Resource, capacity=1).

Scoring formula mirrors ABM (behavior-oriented-simulation/src/model/matching_engine.py):

    score = w_proximity × dist_score
          + w_equity    × equity_term
          + w_charity   × charity_bonus

    dist_score    = 1 − (dist_km / operational_radius_km)   ← linear ∈ [0, 1]
    equity_term   = recipient.reliability_score / 100.0     when reliability_scoring=True
                  = tier_equity_score                        when reliability_scoring=False (S02)
    charity_bonus = 1.0 if is_charity else 0.0

When reliability_scoring=True  the formula is identical to the ABM.
When reliability_scoring=False (S02 — no reliability mitigation) the equity term
falls back to a tier-based equity score (0.2 / 0.5 / 0.8 by distance ring) so
peripheral recipients still receive a fairness boost (REQ-11).

REQ-03  : surpluses ≥ large_surplus_threshold_kg are offered to charities first.
REQ-09  : capacity=1 enforces serialized execution — no concurrent race conditions.
REQ-11  : peripheral recipients (dist_from_center ≥ peripheral_threshold_km) benefit
           from higher tier equity scores in S02, and from accumulated reliability
           scores in all other scenarios.

All weights, thresholds, and limits are injected from shared/params.yaml via the
`params` dict passed to the constructor — nothing is hardcoded in this module.

Service time (DES infrastructure parameter, not a business rule):
    Normal(μ=1.0 s, σ=0.3 s) clipped to [0.1, 2.0] s  ≈ 1 real second per match
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import simpy

from entities import Donor, Recipient, Surplus, euclidean_distance_km

# ── DES infrastructure constants (not business parameters) ────────────────────
# These control the SimPy service-time distribution, not the matching logic.
# Values match the time-unit convention in the Workshop 4 prompt.

_SERVICE_MEAN_S: float = 1.0    # μ = 1/60 min ≈ 1 real second
_SERVICE_STD_S:  float = 0.3    # σ = 0.005 min × 60 ≈ 0.3 s
_SERVICE_MIN_S:  float = 0.1    # lower clip
_SERVICE_MAX_S:  float = 2.0    # upper clip


# ── Engine ────────────────────────────────────────────────────────────────────

class MatchingEngine:
    """
    Wraps a SimPy Resource(capacity=1).

    Constructor injects all business parameters from shared/params.yaml so that
    this module contains zero hardcoded domain values.

    Call `env.process(engine.match(..., result))` from a surplus lifecycle process.
    After the yield, result["recipient"] holds the chosen Recipient (or None).
    """

    def __init__(self, env: simpy.Environment, metrics: Any, params: Dict) -> None:
        self.env      = env
        self.resource = simpy.Resource(
            env, capacity=int(params["matching"]["engine_capacity"])
        )
        self.metrics  = metrics

        m = params["matching"]
        s = params["surplus"]

        # Scoring weights (must sum to 1.0; identical to ABM)
        self._w_proximity = float(m["weight_proximity"])
        self._w_equity    = float(m["weight_equity"])
        self._w_charity   = float(m["weight_charity"])

        # Operational boundary
        self._radius_km   = float(m["tier_3_radius_km"])   # 3.0 km

        # Tier equity scores — used as equity_term when reliability_scoring=False
        self._tier_equity: Dict[int, float] = {
            1: float(m["tier_1_equity_score"]),   # 0.2 — inner zone
            2: float(m["tier_2_equity_score"]),   # 0.5 — mid zone
            3: float(m["tier_3_equity_score"]),   # 0.8 — outer zone (REQ-11)
        }

        # Business thresholds sourced from surplus section
        self._large_kg    = float(s["large_surplus_threshold_kg"])
        self._max_retries = int(s["max_reassignment_attempts"])

    # ── Public accessors (used by main.py lifecycle) ──────────────────────────

    @property
    def max_retries(self) -> int:
        """Maximum reassignment attempts before a surplus expires."""
        return self._max_retries

    @property
    def large_surplus_kg(self) -> float:
        """Surpluses at or above this threshold trigger REQ-03 charity-first rule."""
        return self._large_kg

    # ── Scoring ───────────────────────────────────────────────────────────────

    def _score(
        self,
        donor:               Donor,
        recipient:           Recipient,
        reliability_scoring: bool,
    ) -> float:
        """
        Composite score — mirrors ABM behavior-oriented/src/model/matching_engine.py.

        Returns -1.0 for recipients outside the operational boundary so they are
        never selected by max().
        """
        dist = euclidean_distance_km(donor.x, donor.y, recipient.x, recipient.y)
        if dist > self._radius_km:
            return -1.0

        dist_score = 1.0 - (dist / self._radius_km)   # linear [0, 1]

        if reliability_scoring:
            # ABM formula: weight_reliability × (reliability_score / 100)
            equity_term = recipient.reliability_score / 100.0
        else:
            # S02 fallback: tier-based equity score (REQ-11 fairness proxy)
            equity_term = self._tier_equity.get(recipient.tier, self._tier_equity[1])

        charity_bonus = 1.0 if recipient.is_charity else 0.0

        return (
            self._w_proximity * dist_score
            + self._w_equity  * equity_term
            + self._w_charity * charity_bonus
        )

    # ── Best-match selection ──────────────────────────────────────────────────

    def find_best_match(
        self,
        surplus:             Surplus,
        donor:               Donor,
        recipients:          List[Recipient],
        reliability_scoring: bool,
    ) -> Optional[Recipient]:
        """
        Filter candidates by operational radius, apply REQ-03 charity-first rule
        for large surpluses, then return the highest-scoring recipient.
        """
        candidates = [
            r for r in recipients
            if euclidean_distance_km(donor.x, donor.y, r.x, r.y) <= self._radius_km
        ]
        if not candidates:
            return None

        # REQ-03: surpluses ≥ large_surplus_threshold_kg → charities only
        if surplus.kg >= self._large_kg:
            charity_cands = [r for r in candidates if r.is_charity]
            if charity_cands:
                candidates = charity_cands

        return max(
            candidates,
            key=lambda r: self._score(donor, r, reliability_scoring),
        )

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

        Requests the single-capacity resource (REQ-09: serialized), simulates
        matching service time, then stores the best recipient in result["recipient"].
        """
        with self.resource.request() as req:
            yield req

            # Service time: Normal(1 s, 0.3 s) clipped to [0.1, 2.0] s
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

