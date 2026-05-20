import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from pathlib import Path

import yaml
import pandas as pd

from src.model.food_waste_model import FoodWasteModel
from src.metrics.metrics_collector import MetricsCollector

print("Script started")

# Loads a YAML scenario configuration file.
# Returns dict: Parsed configuration dictionary
def load_config(path):
    with open(path, "r", encoding="utf=8") as f:
        return yaml.safe_load(f)
    
# Ececutes a single simulation run with the given configuration and seed.
# Returns MetricsCollector: Collector with full tick and agent records for this run.
def run_single(config, seed):
    stochastic = config.get("stochastic", {})
    operational = config.get("operational", {})

    model = FoodWasteModel(
        n_donors=config["n_donors"],
        n_beneficiaries=config["n_beneficiaries"],
        n_charities=config["n_charities"],
        n_volunteers=config["n_volunteers"],
        no_show_min=stochastic.get("no_show_probability_min", 0.10),
        no_show_max=stochastic.get("no_show_probability_max", 0.25),
        surplus_kg_min=stochastic.get("surplus_kg_min", 5.0),
        surplus_kg_max=stochastic.get("surplus_kg_max", 15.0),
        max_concurrent_assignments=operational.get("max_concurrent_assignments", None),
        seed=seed,
    )

    collector = MetricsCollector(
        model=model,
        scenario_name=config["scenario_name"],
    )

    for _ in range(config["n_ticks"]):
        model.step()
        collector.record_tick()

    collector.record_agents()
    return collector

# Executes all rund for a scenario and saves results to CSV files
def run_scenario(config_path):
    config = load_config(config_path)
    scenario_name = config["scenario_name"]
    n_runs = config["n_runs"]
    n_ticks = config["n_ticks"]

    results_dir = Path("experiments/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    tick_dfs = []
    agent_dfs = []
    summaries = []

    print("=" * 60)
    print(f"Scenario     : {scenario_name}")
    print(f"Runs         : {n_runs}")
    print(f"Ticks/run    : {n_ticks}")
    print(f"Donors       : {config['n_donors']}")
    print(f"Beneficiaries: {config['n_beneficiaries']}")
    print(f"Charities    : {config['n_charities']}")
    print(f"Volunteers   : {config['n_volunteers']}")
    print("=" * 60)

    for run_idx in range(n_runs):
        seed = run_idx
        collector = run_single(config, seed=seed)

        summary = collector.get_summary()
        summaries.append(summary)
        tick_dfs.append(collector.to_dataframe())
        agent_dfs.append(collector.agents_to_dataframe())

        print(
            f"  Run {run_idx + 1:>2}/{n_runs} | "
            f"seed={seed:>2} | "
            f"recovery={summary['final_recovery_rate']:.2%} | "
            f"completion={summary['final_pickup_completion_rate']:.2%} | "
            f"charity_share={summary['charity_assignment_share']:.2%} | "
            f"no_show={summary['avg_no_show_rate']:.2%}"
        )

    all_ticks = pd.concat(tick_dfs, ignore_index=True)
    all_agents = pd.concat(agent_dfs, ignore_index=True)
    all_summaries = pd.DataFrame(summaries)

    ticks_path = results_dir / f"{scenario_name}_ticks.csv"
    agents_path = results_dir / f"{scenario_name}_agents.csv"
    summary_path = results_dir / f"{scenario_name}_summary.csv"

    all_ticks.to_csv(ticks_path, index=False)
    all_agents.to_csv(agents_path, index=False)
    all_summaries.to_csv(summary_path, index=False)

    print()
    print("=" * 60)
    print(f"Results saved to experiments/results/")
    print(f"  {scenario_name}_ticks.csv   : {all_ticks.shape}")
    print(f"  {scenario_name}_agents.csv  : {all_agents.shape}")
    print(f"  {scenario_name}_summary.csv : {all_summaries.shape}")
    print()
    print("Aggregate results across all runs:")
    print(f"  Recovery rate    : {all_summaries['final_recovery_rate'].mean():.2%} "
          f"(±{all_summaries['final_recovery_rate'].std():.2%})")
    print(f"  Completion rate  : {all_summaries['final_pickup_completion_rate'].mean():.2%} "
          f"(±{all_summaries['final_pickup_completion_rate'].std():.2%})")
    print(f"  Charity share    : {all_summaries['charity_assignment_share'].mean():.2%} "
          f"(±{all_summaries['charity_assignment_share'].std():.2%})")
    print(f"  Avg no-show rate : {all_summaries['avg_no_show_rate'].mean():.2%} "
          f"(±{all_summaries['avg_no_show_rate'].std():.2%})")
    print("=" * 60)

        
if __name__ == "__main__":
    print("Parsing args...")
    parser = argparse.ArgumentParser(
        description="Run a Food Waste ABM simulation scenario."
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to the YAML scenario configuration file.",
    )
    args = parser.parse_args()
    print(f"Config path: {args.config}")
    run_scenario(args.config)