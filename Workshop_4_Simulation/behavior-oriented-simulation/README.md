# Food Waste Reduction Platform — Behavior-Oriented Simulation

Agent-Based Model (ABM) simulating food surplus redistribution dynamics among cafeterias, beneficiaries, charities, and volunteers within a 3 km radius of Universidad Distrital Francisco José de Caldas, Bogotá.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Mesa](https://img.shields.io/badge/Mesa-2.3.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-In%20Development-orange)

## Overview

This simulation is part of **Workshop 4 – System Simulation** of the Food Waste Reduction Platform project, developed at Universidad Distrital Francisco José de Caldas (Bogotá, Colombia).

The model implements an Agent-Based Modeling (ABM) approach using Python Mesa to analyze the dynamic interactions and emergent behaviors of five actor types within a food surplus redistribution system. Unlike the complementary Process-Oriented Simulation (which evaluates macro-level flow metrics), this model focuses on *why* and *how* individual and collective behaviors evolve over time.

### Key phenomena modeled

- No-show cascading effects and their propagation across reassignment chains.
- Impact of staged radius notifications (500 m → 1 km → 3 km) on fairness and demand saturation.
- Temporal evolution of reliability scoring and its influence on future assignment probability.
- User adoption and disengagement dynamics across adoption scenarios.

### Success criteria linked to this simulation

| Metric | Target |
|---|---|
| Surplus recovery rate | ≥ 80% |
| Pickup completion rate | ≥ 85% |
| Fairness coefficient (Gini-based) | ≥ 0.75 |
| Assignments within 3 km radius | ≥ 99% |
| No-show rate reduction (vs. baseline) | ≥ 50% |

## Project Structure

```text
food-waste-abm/
├── src/
│   ├── agents/           # One file per agent type
│   │   ├── donor_agent.py
│   │   ├── beneficiary_agent.py
│   │   ├── charity_agent.py
│   │   ├── volunteer_agent.py
│   │   └── surplus_agent.py
│   ├── model/            # Main Mesa model and matching engine
│   │   ├── food_waste_model.py
│   │   └── matching_engine.py
│   ├── notifications/    # Staged radius notification system
│   │   └── notification_system.py
│   └── metrics/          # Metrics collectors and CO₂ calculator
│       └── metrics_collector.py
├── experiments/
│   ├── scenarios/        # YAML configuration files per scenario
│   │   ├── scenario_low_adoption.yaml
│   │   ├── scenario_medium_adoption.yaml
│   │   ├── scenario_high_adoption.yaml
│   │   ├── scenario_no_mitigations.yaml
│   │   └── scenario_sensitivity.yaml
│   └── results/          # CSV outputs (git-ignored)
├── notebooks/            # Statistical analysis and visualizations
├── tests/                # Unit tests per agent and mechanism
├── docs/                 # Technical documentation and traceability matrix
├── requirements.txt
└── README.md
```

## Setup

### Prerequisites

- Python 3.9 or higher
- Git

### Installation

1. Clone the repository:

```bash
git clone <your-repo-url>
cd food-waste-abm
```

2. Create and activate a virtual environment:

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Verify the installation:

```bash
python -c "import mesa; print('Mesa version:', mesa.__version__)"
```

## Running Experiments

Each scenario is defined as a YAML configuration file under `experiments/scenarios/`. To run a single scenario:

```bash
python -m experiments.run_scenario --config experiments/scenarios/scenario_medium_adoption.yaml
```

To run all scenarios with 30 repetitions each:

```bash
python -m experiments.run_all
```

Results are saved as CSV files under `experiments/results/` and can be analyzed using the notebooks in `notebooks/`.

## Authors

| Name | Role | Institution |
|---|---|---|
| Luna Alejandra Sandoval Rodríguez | Project Lead | Universidad Distrital Francisco José de Caldas |

**Course:** Ingeniería de Sistemas — Simulación de Sistemas  
**Delivery:** Workshop 4 – System Simulation  
**Date:** May 2026