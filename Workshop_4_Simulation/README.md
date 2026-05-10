# Workshop 4 – System Simulation and Validation
**Food Waste Reduction Platform**  
**Real-Time Surplus Redistribution Mobile Application**

## Overview
The Food Waste Reduction Platform is a geospatially constrained mobile application that connects local cafeterias and restaurants with students, community members, and verified charitable organizations for real-time surplus food redistribution within a strict 3 km radius of the Engineering Faculty at Universidad Distrital Francisco José de Caldas (Bogotá, Colombia).

This repository folder contains all artifacts for **Workshop 4**, focused on **computational simulation and validation** of the system architecture designed in Workshop 2 and enhanced in Workshop 3.

The simulations provide empirical evidence to validate design decisions, evaluate system performance under different scenarios, identify bottlenecks, and explore emergent behaviors and complexity patterns.

## Workshop Objectives
- Develop two complementary simulation models:
  - **Process-Oriented Simulation** (Discrete-Event Simulation with SimPy)
  - **Behavior-Oriented Simulation** (Agent-Based Modeling with Mesa)
- Validate the proposed architecture, matching algorithm, priority rules, and no-show mitigation strategies.
- Evaluate system performance through multiple scenarios (low, medium, and high adoption).
- Analyze emergent behaviors, sensitivity to key parameters, and design robustness.
- Generate quantitative metrics and visualizations to support academic deliverables (Paper, Technical Report, and Poster).

## Key Achievements (Workshop 4)
- Implementation of two complementary simulation paradigms
- Surplus recovery rate analysis under different adoption levels
- Evaluation of matching efficiency, no-show impact, and reallocation effectiveness
- Identification of system bottlenecks and optimization opportunities
- Quantitative validation of the 3 km radius constraint and priority system for charities
- Reproducible experimental framework with clear parameter configuration

## Relation with Previous Workshops
- **Workshop 1**: Systems boundaries, 17 design requirements, 10 critical risks, and baseline metrics.
- **Workshop 2**: Four-layer architecture, PostGIS geospatial matching, serialized priority algorithm, staggered notifications, and reliability scoring.
- **Workshop 3**: Robust engineering improvements (asynchronous messaging, service abstraction) and project management framework.

## Team
- **Luna Alejandra Sandoval Rodríguez** (20241020053) – Systems Analyst / Project Lead
- **Cristian Camilo Bonilla Lizarazo** (20241020015) – Systems Analyst / Simulation Developer
- **Nicolás Rodríguez Granados** (20241020037) – Systems Analyst / Backend Developer
- **Juan Sebastián Bravo Rojas** (20241020004) – Systems Analyst / Database Specialist

## Status
**In Progress** – Targeted delivery: **22 May 2026**

## Repository Structure
Workshop_4_Simulation/
├── src/                    # Source code of both simulations
│   ├── process_simulation.py
│   ├── behavior_simulation.py
│   └── matching_algorithm.py
├── data/                   # Input parameters and configurations
├── experiments/            # Scenario definitions and execution scripts
├── results/                # Output data, logs, and plots
│   └── plots/
├── notebooks/              # Exploratory notebooks (SimPy & Mesa)
├── docs/                   # Simulation Report and additional documentation
└── README.md


## Related Files
- ...


**Last updated:** May 5, 2026

**Academic Context:** Systems Analysis & Design Course – Universidad Distrital Francisco José de Caldas, Semester 2026-I
