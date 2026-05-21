"""
metrics.py — KPI collection and statistical aggregation for the simulation.

MetricsCollector  — per-replication accumulator
compute_kpis()    — derive all KPIs from one replication
aggregate_replications() — mean ± 95% CI across N replications
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy import stats


# ── Per-replication collector ─────────────────────────────────────────────────

class MetricsCollector:
    """Accumulates raw counts and samples during a single simulation run."""

    SIM_DURATION_MIN: float = 900.0   # 07:00–22:00

    def __init__(self) -> None:
        # Surplus volumes
        self.kg_published:   float = 0.0
        self.kg_collected:   float = 0.0

        # Pickup outcomes
        self.successful_pickups: int = 0
        self.accepted_count:     int = 0   # ASSIGNED events
        self.expired_count:      int = 0

        # Matching engine
        self.matching_latencies:   List[float] = []   # seconds (POST→ASSIGNED)
        self.engine_busy_minutes:  float = 0.0

        # Charity / peripheral compliance
        self.total_large_offers:       int = 0   # surpluses ≥ 10 kg assigned
        self.large_offers_to_charities: int = 0
        self.total_matches:            int = 0
        self.peripheral_matches:       int = 0   # to recipients ≥ 2.5 km

        # Queue monitoring (sampled every minute)
        self.queue_length_samples: List[Tuple[float, int]] = []  # (time_min, length)
 
        # Active lifecycle counter — incremented when a surplus enters lifecycle,
        # decremented when it reaches a terminal state (PICKED_UP or EXPIRED).
        # Sampled by _queue_monitor to produce the "active surpluses" (queue depth) KPI.
        self.active_lifecycles: int = 0

        # Notification throughput
        self.notification_dispatch_times: List[float] = []   # sim time in minutes

        # Reassignment chain lengths
        self.reassignment_chain_lengths: List[int] = []

    def record_expired(self, surplus: Any) -> None:
        self.expired_count += 1

    # ── KPI derivation ────────────────────────────────────────────────────────

    def compute_kpis(self) -> Dict[str, float]:
        """Return a flat dict of all KPIs for this replication."""
        eps = 1e-9

        recovery_rate = self.kg_collected / max(self.kg_published, eps)
        pickup_completion = self.successful_pickups / max(self.accepted_count, eps)
        avg_latency_s = float(np.mean(self.matching_latencies)) if self.matching_latencies else 0.0
        max_latency_s = float(np.max(self.matching_latencies)) if self.matching_latencies else 0.0
        charity_priority = self.large_offers_to_charities / max(self.total_large_offers, eps)
        peripheral_rate = self.peripheral_matches / max(self.total_matches, eps)
        engine_utilization = self.engine_busy_minutes / self.SIM_DURATION_MIN

        # Peak-hour queue stats (12–14h = t∈[300,420), 18–20h = t∈[660,780))
        peak_q = [
            q for t, q in self.queue_length_samples
            if (300 <= t < 420) or (660 <= t < 780)
        ]
        avg_queue_peak = float(np.mean(peak_q)) if peak_q else 0.0
        max_queue_peak = float(max(peak_q)) if peak_q else 0.0

        # Overall queue
        all_q = [q for _, q in self.queue_length_samples]
        avg_queue_overall = float(np.mean(all_q)) if all_q else 0.0

        # Notification throughput: dispatches per simulated hour (mean across hours)
        by_hour: Dict[int, int] = defaultdict(int)
        for t in self.notification_dispatch_times:
            hour = int(t // 60) + 7
            by_hour[hour] += 1
        throughput_per_h = (
            float(np.mean(list(by_hour.values()))) if by_hour else 0.0
        )

        # Reassignment
        avg_reassign = (
            float(np.mean(self.reassignment_chain_lengths))
            if self.reassignment_chain_lengths else 0.0
        )
        max_reassign = (
            float(max(self.reassignment_chain_lengths))
            if self.reassignment_chain_lengths else 0.0
        )

        co2_avoided = self.kg_collected * 2.5
        throughput_per_hour = self.successful_pickups / 15.0   # 15-hour window

        return {
            # PRIMARY KPIs (targets in parentheses)
            "recovery_rate":           recovery_rate,      # ≥ 0.80
            "pickup_completion_rate":  pickup_completion,  # ≥ 0.85
            "avg_matching_latency_s":  avg_latency_s,      # < 2 s
            "max_matching_latency_s":  max_latency_s,
            "charity_priority_rate":   charity_priority,   # ≥ 0.90  (REQ-03/04)
            "peripheral_match_rate":   peripheral_rate,    # ≥ 0.15  (REQ-11)
            # PROCESS-ORIENTED KPIs
            "engine_utilization":      engine_utilization,
            "avg_queue_length":        avg_queue_peak,     # mean at peak hours
            "max_queue_length":        max_queue_peak,     # peak observed
            "avg_queue_length_overall": avg_queue_overall,
            "throughput_per_hour":     throughput_per_hour,  # completions / sim-hour
            "avg_notification_throughput_per_h": throughput_per_h,
            "avg_reassignment_chain":  avg_reassign,
            "max_reassignment_chain":  max_reassign,
            # IMPACT KPIs
            "co2_avoided_kg":          co2_avoided,
            "kg_published":            self.kg_published,
            "kg_collected":            self.kg_collected,
            # COUNTS (useful for debugging)
            "n_surpluses":             float(self.successful_pickups + self.expired_count),
            "successful_pickups":      float(self.successful_pickups),
            "accepted_count":          float(self.accepted_count),
            "expired_count":           float(self.expired_count),
        }


# ── Cross-replication aggregation ────────────────────────────────────────────

def aggregate_replications(
    kpi_list: List[Dict[str, float]],
) -> Dict[str, Dict[str, float]]:
    """
    Compute mean ± 95% CI (t-distribution) for each KPI across all replications.

    Returns a nested dict:
        { kpi_name: { "mean": ..., "ci95": ..., "min": ..., "max": ... } }
    """
    if not kpi_list:
        return {}

    n = len(kpi_list)
    result: Dict[str, Dict[str, float]] = {}

    for key in kpi_list[0]:
        values = np.array([rep[key] for rep in kpi_list], dtype=float)
        mean = float(np.mean(values))
        ci = 0.0
        if n > 1:
            se = float(stats.sem(values, ddof=1))
            t_crit = float(stats.t.ppf(0.975, df=n - 1))
            ci = t_crit * se
        result[key] = {
            "mean": mean,
            "ci95": ci,
            "min":  float(np.min(values)),
            "max":  float(np.max(values)),
            "std":  float(np.std(values, ddof=1)) if n > 1 else 0.0,
        }

    return result
