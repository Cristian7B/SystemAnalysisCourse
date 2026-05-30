"""
main.py — Food Waste Reduction Platform: Process-Oriented Simulation (Workshop 4)

Authors : Cristian Bonilla 
Tool    : Python SimPy (discrete-event / process-oriented)
Clock   : 0 min = 07:00, 900 min = 22:00 (15-hour operating window)

Entry point:
    python src/simulation/process/main.py

Outputs:
    results/logs/   — per-replication state-transition CSVs
    results/reports/ — per-scenario KPI summary CSVs (mean ± 95% CI)
    Console         — formatted KPI table via tabulate
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import simpy
from tabulate import tabulate
import yaml

# ── Sibling imports ────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from entities import (
    Donor,
    Recipient,
    Surplus,
    SurplusState,
    distance_tier,
    euclidean_distance_km,
)
from matching_engine import MatchingEngine
from metrics import MetricsCollector, aggregate_replications
from notification import NotificationService
from scenarios import ALL_SCENARIOS, ScenarioConfig

# ── Paths ─────────────────────────────────────────────────────────────────────

_ROOT       = Path(__file__).resolve().parents[3]
DATA_DIR    = _ROOT / "data"
LOGS_DIR    = _ROOT / "results" / "logs"
REPORTS_DIR = _ROOT / "results" / "reports"

# ── Parameter loader ─────────────────────────────────────────────────────────

def _load_shared_params() -> Dict:
    """Load shared/params.yaml — single source of truth for all simulations."""
    path = _ROOT.parent / "shared" / "params.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

# ── Static data loaders ───────────────────────────────────────────────────────

def _load_arrival_rates() -> Dict[str, List[float]]:
    with open(DATA_DIR / "poisson_arrival.json") as f:
        data = json.load(f)
    return {k: [float(v) for v in data[k]] for k in ("Low", "Medium", "High")}


# ── Agent generation ──────────────────────────────────────────────────────────

def _point_in_circle(radius_km: float = 3.0) -> Tuple[float, float]:
    """Uniform random point within a circle of given radius (km)."""
    theta = np.random.uniform(0.0, 2.0 * math.pi)
    r     = radius_km * math.sqrt(np.random.uniform(0.0, 1.0))
    return r * math.cos(theta), r * math.sin(theta)


def _generate_donors(scenario: ScenarioConfig) -> List[Donor]:
    n = int(np.random.randint(scenario.donor_count_range[0],
                               scenario.donor_count_range[1] + 1))
    donors = []
    for i in range(n):
        x, y = _point_in_circle()
        donors.append(Donor(
            id=i,
            x=x,
            y=y,
            donor_type="cafeteria" if i % 2 == 0 else "restaurant",
        ))
    return donors


def _generate_recipients(
    scenario: ScenarioConfig,
    rel_score_min: int,
    rel_score_max: int,
) -> List[Recipient]:
    n_ind = int(np.random.randint(scenario.recipient_individual_range[0],
                                   scenario.recipient_individual_range[1] + 1))
    n_chr = int(np.random.randint(scenario.charity_count_range[0],
                                   scenario.charity_count_range[1] + 1))
    recipients = []
    for i in range(n_ind + n_chr):
        x, y = _point_in_circle()
        dist = math.sqrt(x * x + y * y)
        # Sample per-recipient no-show probability from the scenario's range.
        # Charities receive the lower half of the range (more reliable), matching ABM.
        is_charity = (i >= n_ind)
        if is_charity:
            prob_max = scenario.no_show_min + (scenario.no_show_max - scenario.no_show_min) * 0.5
            no_show_prob = float(np.random.uniform(scenario.no_show_min, prob_max))
        else:
            no_show_prob = float(np.random.uniform(scenario.no_show_min, scenario.no_show_max))
        recipients.append(Recipient(
            id=i,
            x=x,
            y=y,
            reliability_score=float(np.random.randint(rel_score_min, rel_score_max + 1)),
            no_show_prob=no_show_prob,
            is_charity=is_charity,
            tier=distance_tier(dist),
            dist_from_center=dist,
        ))
    return recipients


# ── Simulation class ──────────────────────────────────────────────────────────

class FoodWasteSimulation:
    """
    Encapsulates one full simulation replication.

    Call run() to execute the SimPy environment and return the MetricsCollector.
    """

    def __init__(
        self,
        scenario:      ScenarioConfig,
        seed:          int,
        arrival_rates: Dict[str, List[float]],
        params:        Dict,
    ) -> None:
        np.random.seed(seed)

        self.scenario      = scenario
        self.seed          = seed
        self._hourly_rates = arrival_rates[scenario.adoption]   # 15 values

        # ── Parameters from shared/params.yaml ────────────────────────────────────
        sys_p  = params["system"]
        sur_p  = params["surplus"]
        rel_p  = params["reliability"]
        stat_p = params["statistics"]

        self._sim_end          = float(sys_p["operational_minutes"])
        self._max_retries      = int(sur_p["max_reassignment_attempts"])
        self._large_kg         = float(sur_p["large_surplus_threshold_kg"])
        self._no_show_timeout  = float(sur_p["no_show_timeout_minutes"])
        self._pickup_window    = (
            float(sur_p["pickup_window_min_minutes"]),
            float(sur_p["pickup_window_max_minutes"]),
        )
        self._pickup_response  = (
            float(sur_p["pickup_response_min_minutes"]),  # 5 min  — time recipient takes to arrive
            float(sur_p["pickup_response_max_minutes"]),  # 30 min — kept << pickup_window for retries
        )
        self._kg_mean   = float(sur_p["kg_mean"])
        self._kg_std    = float(sur_p["kg_std"])
        self._kg_min    = float(sur_p["kg_min"])
        self._kg_max    = float(sur_p["kg_max"])
        self._rel_reward  = float(rel_p["pickup_reward"])     # +1.0
        self._rel_penalty = float(rel_p["no_show_penalty"])   # −2.0 (negative value)
        self._rel_score_min = int(rel_p["initial_score_min"])
        self._rel_score_max = int(rel_p["initial_score_max"])

        self.env              = simpy.Environment()
        self.metrics          = MetricsCollector()
        self.matching_engine  = MatchingEngine(self.env, self.metrics, params)
        self.notification_svc = NotificationService(self.env, self.metrics, params)

        # Closed agent population — fixed at simulation start
        self.donors:     List[Donor]     = _generate_donors(scenario)
        self.recipients: List[Recipient] = _generate_recipients(
            scenario, self._rel_score_min, self._rel_score_max
        )

        self._surplus_counter: int      = 0
        self.surpluses:        List[Surplus] = []   # all created surpluses

    # ── Surplus factory ───────────────────────────────────────────────────────

    def _next_id(self) -> int:
        self._surplus_counter += 1
        return self._surplus_counter

    def _create_surplus(self) -> Tuple[Surplus, Donor]:
        kg = float(np.clip(
            np.random.normal(self._kg_mean, self._kg_std),
            self._kg_min,
            self._kg_max,
        ))
        posted_at     = self.env.now
        pickup_window = float(np.random.uniform(*self._pickup_window))
        expiry_at     = min(posted_at + pickup_window, self._sim_end)
        donor        = self.donors[int(np.random.randint(len(self.donors)))]

        surplus = Surplus(
            id=self._next_id(),
            donor_id=donor.id,
            kg=kg,
            posted_at=posted_at,
            expiry_at=expiry_at,
        )
        self.surpluses.append(surplus)
        return surplus, donor

    # ── Surplus lifecycle process ─────────────────────────────────────────────

    def _surplus_lifecycle(self, surplus: Surplus, donor: Donor):
        """
        SimPy process — drives a surplus through its full state machine.

        POSTED → IN_QUEUE → ASSIGNED → PICKED_UP
                          ↘ NO_SHOW (15-min timeout) → retry (≤ MAX_RETRIES)
                                                     ↘ EXPIRED
        """
        sc = self.scenario

        # Track how many surpluses are simultaneously active in the system.
        # active_lifecycles is decremented via finally no matter how lifecycle ends.
        self.metrics.active_lifecycles += 1
        try:

            # ── POSTED ────────────────────────────────────────────────────────────
            surplus.log_transition(self.env.now, SurplusState.POSTED)
            self.metrics.kg_published += surplus.kg

            while surplus.retry_count < self._max_retries:

                # Check expiry before entering queue
                if self.env.now >= surplus.expiry_at:
                    surplus.log_transition(self.env.now, SurplusState.EXPIRED)
                    self.metrics.record_expired(surplus)
                    return

                # ── IN_QUEUE ──────────────────────────────────────────────────────
                surplus.log_transition(self.env.now, SurplusState.IN_QUEUE)
                queue_entry_time = self.env.now

                # Wait for matching engine (serialized, capacity=1)
                result: Dict[str, Any] = {}
                yield self.env.process(
                    self.matching_engine.match(
                        surplus, donor, self.recipients,
                        sc.reliability_scoring, result,
                    )
                )

                latency_s: float = (self.env.now - queue_entry_time) * 60.0
                self.metrics.matching_latencies.append(latency_s)

                best_match: Optional[Recipient] = result.get("recipient")

                if best_match is None:
                    # No eligible recipient — increment retry
                    surplus.retry_count += 1
                    self.metrics.reassignment_chain_lengths.append(surplus.retry_count)
                    if surplus.retry_count >= self._max_retries:
                        break
                    # Brief cool-down before retry
                    yield self.env.timeout(5.0)
                    continue

                # ── ASSIGNED ──────────────────────────────────────────────────────
                surplus.assigned_to = best_match.id
                surplus.log_transition(self.env.now, SurplusState.ASSIGNED, best_match.id)
                self.metrics.accepted_count += 1
                self.metrics.total_matches  += 1

                # REQ-11 tracking
                if best_match.is_peripheral:
                    self.metrics.peripheral_matches += 1

                # REQ-03 tracking
                if surplus.kg >= self._large_kg:
                    self.metrics.total_large_offers += 1
                    if best_match.is_charity:
                        self.metrics.large_offers_to_charities += 1

                # Fire-and-forget notification dispatch (async broker)
                self.env.process(
                    self.notification_svc.dispatch(
                        surplus, donor, self.recipients,
                        sc.staggered_notifications,
                    )
                )

                # ── Wait for pickup ───────────────────────────────────────────────
                # pickup_response << pickup_window, so window has room for retries.
                remaining = surplus.expiry_at - self.env.now
                if remaining <= 0:
                    surplus.log_transition(self.env.now, SurplusState.EXPIRED)
                    self.metrics.record_expired(surplus)
                    return

                pickup_wait = min(float(np.random.uniform(*self._pickup_response)), remaining)
                yield self.env.timeout(pickup_wait)

                # ── No-show determination ─────────────────────────────────────────
                effective_noshow = best_match.no_show_prob
                if sc.reliability_scoring:
                    # Reliable recipients are less likely to no-show (REQ-08)
                    rel = best_match.reliability_score / 100.0
                    effective_noshow = best_match.no_show_prob * (1.0 - 0.4 * rel)

                if np.random.random() < effective_noshow:
                    # ── NO_SHOW ───────────────────────────────────────────────────
                    surplus.log_transition(self.env.now, SurplusState.NO_SHOW, best_match.id)
                    if sc.reliability_scoring:
                        best_match.reliability_score = max(
                            0.0, best_match.reliability_score + self._rel_penalty
                        )
                    # Mandatory timeout before reassignment (Risk R4)
                    yield self.env.timeout(self._no_show_timeout)
                    surplus.assigned_to  = None
                    surplus.retry_count += 1
                    self.metrics.reassignment_chain_lengths.append(surplus.retry_count)
                    if surplus.retry_count >= self._max_retries:
                        break
                    # → loop back to IN_QUEUE

                else:
                    # ── PICKED_UP ─────────────────────────────────────────────────
                    surplus.log_transition(self.env.now, SurplusState.PICKED_UP, best_match.id)
                    self.metrics.successful_pickups += 1
                    self.metrics.kg_collected       += surplus.kg
                    if sc.reliability_scoring:
                        best_match.reliability_score = min(
                            100.0, best_match.reliability_score + self._rel_reward
                        )
                    return  # terminal state — lifecycle ends

            # ── EXPIRED (max retries exhausted) ───────────────────────────────────
            surplus.log_transition(self.env.now, SurplusState.EXPIRED)
            self.metrics.record_expired(surplus)

        finally:
            self.metrics.active_lifecycles -= 1

    # ── Arrival generator ─────────────────────────────────────────────────────

    def _arrival_generator(self):
        """Time-varying Poisson surplus arrival process (07:00–22:00)."""
        while self.env.now < self._sim_end:
            hour_idx = min(int(self.env.now // 60), 14)    # clamp last partial hour
            lam      = self._hourly_rates[hour_idx]

            if lam > 0:
                inter_arrival = float(np.random.exponential(60.0 / lam))
            else:
                inter_arrival = 60.0

            yield self.env.timeout(inter_arrival)

            if self.env.now >= self._sim_end:
                break

            surplus, donor = self._create_surplus()
            self.env.process(self._surplus_lifecycle(surplus, donor))

    # ── Queue monitor ─────────────────────────────────────────────────────────

    def _queue_monitor(self):
        """
        Sample system load every minute.

        Samples `active_lifecycles` — the number of surplus lifecycle processes
        currently in flight (POSTED to terminal state). This is the meaningful
        business "queue depth": how many surpluses are simultaneously competing
        for matching and pickup resources.

        The SimPy Resource queue (`resource.queue`) is not used here because
        the matching engine's ~1-second service time means it is idle 99.8% of
        the time at 1-minute sampling intervals.
        """
        while self.env.now < self._sim_end:
            self.metrics.queue_length_samples.append(
                (self.env.now, self.metrics.active_lifecycles)
            )
            yield self.env.timeout(1.0)

    # ── Run ─────────────────────────────────────────────────────────────────────

    def run(self) -> MetricsCollector:
        self.env.process(self._arrival_generator())
        self.env.process(self._queue_monitor())
        self.env.run(until=self._sim_end)
        return self.metrics


# ── Log writer ────────────────────────────────────────────────────────────────

def _write_log(scenario_id: str, seed: int, surpluses: List[Surplus]) -> None:
    path = LOGS_DIR / f"{scenario_id}_rep{seed:03d}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["surplus_id", "timestamp", "state",
                        "assigned_user_id", "kg", "retry_count"],
        )
        writer.writeheader()
        for s in surpluses:
            for t in s.state_log:
                writer.writerow({
                    "surplus_id":       s.id,
                    "timestamp":        f"{t.timestamp:.3f}",
                    "state":            t.state,
                    "assigned_user_id": t.assigned_user_id if t.assigned_user_id is not None else "",
                    "kg":               f"{t.kg:.2f}",
                    "retry_count":      t.retry_count,
                })


# ── Replication runner ────────────────────────────────────────────────────────

def run_replication(
    scenario:      ScenarioConfig,
    seed:          int,
    arrival_rates: Dict[str, List[float]],
    params:        Dict,
    write_logs:    bool = True,
) -> Dict[str, float]:
    sim     = FoodWasteSimulation(scenario, seed, arrival_rates, params)
    metrics = sim.run()
    kpis    = metrics.compute_kpis()
    if write_logs:
        _write_log(scenario.id, seed, sim.surpluses)
    return kpis


# ── Scenario runner ───────────────────────────────────────────────────────────

def run_scenario(
    scenario:      ScenarioConfig,
    arrival_rates: Dict[str, List[float]],
    params:        Dict,
) -> Dict[str, Dict[str, float]]:
    n_reps = int(params["statistics"]["n_replications"])
    print(f"\n  [{scenario.id}] {scenario.name} — {n_reps} replications")
    kpi_list: List[Dict[str, float]] = []

    for seed in range(n_reps):
        kpis = run_replication(scenario, seed, arrival_rates, params)
        kpi_list.append(kpis)
        if (seed + 1) % 10 == 0:
            print(f"    ... completed {seed + 1}/{n_reps}")

    aggregated = aggregate_replications(kpi_list)

    # Write summary CSV
    report_path = REPORTS_DIR / f"{scenario.id}_summary.csv"
    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "mean", "ci95", "ci95_lower", "ci95_upper", "min", "max", "std"])
        for kpi, stats in aggregated.items():
            m, ci = stats["mean"], stats["ci95"]
            writer.writerow([
                kpi,
                f"{m:.6f}",
                f"{ci:.6f}",
                f"{m - ci:.6f}",
                f"{m + ci:.6f}",
                f"{stats['min']:.6f}",
                f"{stats['max']:.6f}",
                f"{stats['std']:.6f}",
            ])
    print(f"    → Report written: {report_path.relative_to(_ROOT)}")
    return aggregated


# ── Console summary ───────────────────────────────────────────────────────────

_KPI_TABLE: List[Tuple[str, str, str]] = [
    # (dict_key,                         display_label,                    target)
    ("recovery_rate",                    "Surplus Recovery Rate",           "≥ 80 %"),
    ("pickup_completion_rate",           "Pickup Completion Rate",          "≥ 85 %"),
    ("avg_matching_latency_s",           "Avg Matching Latency (s)",        "< 2 s"),
    ("charity_priority_rate",            "Charity Priority Rate (REQ-03)",  "≥ 90 %"),
    ("peripheral_match_rate",            "Peripheral Match Rate (REQ-11)",  "≥ 15 %"),
    ("engine_utilization",               "Matching Engine Utilization",     "—"),
    ("avg_queue_length",                 "Avg Queue Len (peak hours)",      "—"),
    ("max_queue_length",                 "Max Queue Len (peak hours)",      "—"),
    ("throughput_per_hour",              "Throughput (completions/h)",      "—"),
    ("avg_reassignment_chain",           "Avg Reassignment Chain",          "—"),
    ("co2_avoided_kg",                   "CO₂ Avoided (kg)",                "—"),
    ("kg_published",                     "Total kg Published",              "—"),
    ("kg_collected",                     "Total kg Collected",              "—"),
    ("n_surpluses",                      "Total Surpluses",                 "—"),
]

_PERCENT_KEYS = {
    "recovery_rate", "pickup_completion_rate",
    "charity_priority_rate", "peripheral_match_rate",
    "engine_utilization",
}


def _fmt(key: str, value: float, ci: float) -> str:
    if key in _PERCENT_KEYS:
        return f"{value * 100:.1f}% ±{ci * 100:.1f}%"
    if "latency" in key:
        return f"{value:.3f}s ±{ci:.3f}s"
    if "kg" in key or key in ("kg_published", "kg_collected"):
        return f"{value:.1f} ±{ci:.1f}"
    return f"{value:.3f} ±{ci:.3f}"


def print_summary(all_results: Dict[str, Dict[str, Dict[str, float]]]) -> None:
    scenario_ids = [s.id for s in ALL_SCENARIOS]
    headers = ["KPI", "Target"] + scenario_ids

    rows = []
    for key, label, target in _KPI_TABLE:
        row = [label, target]
        for sid in scenario_ids:
            res = all_results.get(sid, {}).get(key, {})
            row.append(_fmt(key, res.get("mean", 0.0), res.get("ci95", 0.0)))
        rows.append(row)

    print("\n" + "═" * 100)
    print("  FOOD WASTE REDUCTION PLATFORM — PROCESS-ORIENTED SIMULATION RESULTS")
    print("  Workshop 4  |  SimPy DES  |  Bogotá UD Engineering Faculty, 3 km radius")
    print("═" * 100)
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print("═" * 100)

    # Validation summary
    s01 = all_results.get("S01", {})
    checks = [
        ("Recovery rate ≥ 80%",     s01.get("recovery_rate",          {}).get("mean", 0) >= 0.80),
        ("Pickup success ≥ 85%",    s01.get("pickup_completion_rate", {}).get("mean", 0) >= 0.85),
        ("Avg latency < 2 s",       s01.get("avg_matching_latency_s", {}).get("mean", 0) < 2.0),
        ("Charity priority ≥ 90%",  s01.get("charity_priority_rate",  {}).get("mean", 0) >= 0.90),
        ("Peripheral rate ≥ 15%",   s01.get("peripheral_match_rate",  {}).get("mean", 0) >= 0.15),
    ]
    s03_users = (
        ALL_SCENARIOS[2].recipient_individual_range[0]
        + ALL_SCENARIOS[2].charity_count_range[0]
    )
    checks.append((f"S03 ≥200 users ({s03_users} min)", s03_users >= 200))

    print("\n  S01 BASELINE VALIDATION:")
    for label, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"    [{status}]  {label}")
    print()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    params = _load_shared_params()
    n_reps = int(params["statistics"]["n_replications"])

    print("=" * 60)
    print("  Food Waste Reduction Platform — Workshop 4 Simulation")
    print(f"  {n_reps} Monte Carlo replications per scenario")
    print("=" * 60)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    arrival_rates = _load_arrival_rates()

    t0 = time.time()
    all_results: Dict[str, Dict[str, Dict[str, float]]] = {}

    for scenario in ALL_SCENARIOS:
        all_results[scenario.id] = run_scenario(
            scenario, arrival_rates, params
        )

    elapsed = time.time() - t0
    print(f"\n  Total runtime: {elapsed:.1f} s")

    print_summary(all_results)


if __name__ == "__main__":
    main()
