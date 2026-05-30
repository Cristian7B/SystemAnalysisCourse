"""
notification.py — Staggered asynchronous notification dispatch service.

Architecture mirrors the ABM ring-based notification model:
  - Three distance-based waves measured from the DONOR location
  - Wave 1: recipients ≤ wave_1_max_km          → immediate
  - Wave 2: recipients ≤ wave_2_max_km          → +Uniform(wave_2_delay_min, wave_2_delay_max) min
  - Wave 3: recipients ≤ wave_3_max_km          → +Uniform(wave_3_delay_min, wave_3_delay_max) min total
  - Maximum notifications_per_surplus sent across all waves
  - S04 (no staggered mitigation): all recipients notified at once (no wave delays)

The notification tier grouping is donor-centric (distance from the surplus source),
which is distinct from the recipient's inherent zone tier (origin-centric, used for
scoring and REQ-11 peripheral tracking).

All thresholds and delays are injected from shared/params.yaml via the `params` dict
passed to the constructor — nothing is hardcoded in this module.

Usage (fire-and-forget from lifecycle):
    env.process(notification_svc.dispatch(surplus, donor, recipients, staggered=True))
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import simpy

from entities import Donor, Recipient, Surplus, euclidean_distance_km


# ── Service ───────────────────────────────────────────────────────────────────

class NotificationService:
    """
    Simulates async, tiered push notification dispatch.

    Constructor injects all wave parameters from shared/params.yaml so that
    this module contains zero hardcoded domain values.

    All dispatch methods are SimPy generators — fire with env.process().
    The calling lifecycle coroutine does NOT need to yield on the result.
    """

    def __init__(self, env: simpy.Environment, metrics: Any, params: Dict) -> None:
        self.env     = env
        self.metrics = metrics

        n = params["notifications"]
        self._max_notif   = int(n["max_per_surplus"])
        self._tier1_km    = float(n["wave_1_max_km"])    # 0.5 km
        self._tier2_km    = float(n["wave_2_max_km"])    # 1.0 km
        self._tier3_km    = float(n["wave_3_max_km"])    # 3.0 km
        self._wave2_delay = (
            float(n["wave_2_delay_min_minutes"]),         # 5 min
            float(n["wave_2_delay_max_minutes"]),         # 10 min
        )
        self._wave3_delay = (
            float(n["wave_3_delay_min_minutes"]),         # 10 min
            float(n["wave_3_delay_max_minutes"]),         # 15 min
        )

    def dispatch(
        self,
        surplus:    Surplus,
        donor:      Donor,
        recipients: List[Recipient],
        staggered:  bool,
    ):
        """
        SimPy generator — partition recipients by distance from DONOR and send waves.

        staggered=True  (S01/S02/S03/S05): three-wave tiered dispatch.
        staggered=False (S04 Risk Test):   all recipients notified simultaneously.
        """
        # Partition by distance from this specific donor (not from platform centre)
        tier1: List[Recipient] = []
        tier2: List[Recipient] = []
        tier3: List[Recipient] = []

        for r in recipients:
            d = euclidean_distance_km(donor.x, donor.y, r.x, r.y)
            if d <= self._tier1_km:
                tier1.append(r)
            elif d <= self._tier2_km:
                tier2.append(r)
            elif d <= self._tier3_km:
                tier3.append(r)

        if staggered:
            # ── Wave 1: immediate (≤ wave_1_max_km from donor) ───────────────
            sent = self._send_wave(tier1, self._max_notif)

            # ── Wave 2: delayed (≤ wave_2_max_km) ────────────────────────────
            delay2 = float(np.random.uniform(*self._wave2_delay))
            yield self.env.timeout(delay2)

            remaining = self._max_notif - sent
            if remaining > 0:
                sent += self._send_wave(tier2, remaining)

            # ── Wave 3: further delayed (≤ wave_3_max_km) ────────────────────
            # delay3_total is total elapsed from dispatch start; subtract delay2
            delay3_total = float(np.random.uniform(*self._wave3_delay))
            additional   = max(0.0, delay3_total - delay2)
            if additional > 0:
                yield self.env.timeout(additional)

            remaining = self._max_notif - sent
            if remaining > 0:
                self._send_wave(tier3, remaining)

        else:
            # S04: all recipients notified at once (staggered mitigation disabled)
            all_recipients = tier1 + tier2 + tier3
            self._send_wave(all_recipients, self._max_notif)
            yield self.env.timeout(0)   # keep this a proper SimPy generator

    def _send_wave(self, recipients: List[Recipient], max_count: int) -> int:
        """Record dispatch timestamps for up to max_count recipients; return count."""
        now = self.env.now
        count = 0
        for r in recipients[:max_count]:
            self.metrics.notification_dispatch_times.append(now)
            count += 1
        return count

