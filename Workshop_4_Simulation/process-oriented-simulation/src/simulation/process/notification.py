"""
notification.py — Staggered asynchronous notification dispatch service.

Architecture (from Workshop 3):
  - Infinite capacity (async broker decouples from matching engine)
  - Three distance-based waves from the DONOR location:
      Wave 1: recipients ≤ 0.5 km  → immediate
      Wave 2: recipients ≤ 1.0 km  → +Uniform(5, 10) min
      Wave 3: recipients ≤ 3.0 km  → +Uniform(10, 15) min total from start
  - Max 50 simultaneous notifications per surplus posting
  - S04 (Risk Test): staggered=False → all recipients notified at once

Usage from lifecycle process (fire-and-forget):
    env.process(notification_svc.dispatch(surplus, donor, recipients, staggered=True))
"""

from __future__ import annotations

from typing import Any, List

import numpy as np
import simpy

from entities import Donor, Recipient, Surplus, euclidean_distance_km

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_NOTIF_PER_SURPLUS: int = 50

_TIER1_KM: float = 0.5
_TIER2_KM: float = 1.0
_TIER3_KM: float = 3.0

_WAVE2_DELAY_RANGE = (5.0, 10.0)    # minutes from dispatch start
_WAVE3_DELAY_RANGE = (10.0, 15.0)   # minutes from dispatch start (total)


# ── Service ───────────────────────────────────────────────────────────────────

class NotificationService:
    """
    Simulates async, tiered push notification dispatch.

    All operations are SimPy generators.  Fire with env.process() — the calling
    lifecycle process does NOT need to yield on the returned process.
    """

    def __init__(self, env: simpy.Environment, metrics: Any) -> None:
        self.env     = env
        self.metrics = metrics

    def dispatch(
        self,
        surplus:    Surplus,
        donor:      Donor,
        recipients: List[Recipient],
        staggered:  bool,
    ):
        """
        SimPy generator — group recipients by distance from DONOR and send waves.

        Note: notification tier grouping (donor-centric) is distinct from the
        recipient's inherent tier (origin-centric, used for scoring and REQ-11).
        """
        # Partition recipients by distance from this specific donor
        tier1: List[Recipient] = []
        tier2: List[Recipient] = []
        tier3: List[Recipient] = []

        for r in recipients:
            d = euclidean_distance_km(donor.x, donor.y, r.x, r.y)
            if d <= _TIER1_KM:
                tier1.append(r)
            elif d <= _TIER2_KM:
                tier2.append(r)
            elif d <= _TIER3_KM:
                tier3.append(r)

        if staggered:
            # ── Wave 1: immediate ────────────────────────────────────────────
            sent = self._send_wave(tier1, MAX_NOTIF_PER_SURPLUS)

            # ── Wave 2: delayed ──────────────────────────────────────────────
            delay2 = float(np.random.uniform(*_WAVE2_DELAY_RANGE))
            yield self.env.timeout(delay2)

            remaining = MAX_NOTIF_PER_SURPLUS - sent
            if remaining > 0:
                sent += self._send_wave(tier2, remaining)

            # ── Wave 3: further delayed ──────────────────────────────────────
            delay3_total = float(np.random.uniform(*_WAVE3_DELAY_RANGE))
            additional   = max(0.0, delay3_total - delay2)
            if additional > 0:
                yield self.env.timeout(additional)

            remaining = MAX_NOTIF_PER_SURPLUS - sent
            if remaining > 0:
                self._send_wave(tier3, remaining)

        else:
            # S04 — all notifications sent simultaneously (no staggering)
            all_recipients = tier1 + tier2 + tier3
            self._send_wave(all_recipients, MAX_NOTIF_PER_SURPLUS)
            yield self.env.timeout(0)   # keep this a proper generator

    def _send_wave(self, recipients: List[Recipient], max_count: int) -> int:
        """Record dispatch events for up to max_count recipients; return count sent."""
        now = self.env.now
        count = 0
        for r in recipients[:max_count]:
            self.metrics.notification_dispatch_times.append(now)
            count += 1
        return count
