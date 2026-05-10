# Workshop 3 – Robust System Design and Project Management

**Food Waste Reduction Platform**  
*Real-Time Surplus Redistribution Mobile Application*

## Overview

The **Food Waste Reduction Platform** is a geospatially constrained mobile application that connects local cafeterias and restaurants with students, community members, and verified charitable organizations for **real-time surplus food redistribution** within a strict **3 km radius** of the Engineering Faculty at Universidad Distrital Francisco José de Caldas (Bogotá, Colombia).

This repository contains all artifacts for **Workshop 3** (Implementation, Experimental Validation, Risk Management, Quality Assurance, and Project Management), building directly on:
- **Workshop 1**: Rigorous systems analysis, IPO model, 17 design requirements, and 10 critical risks.
- **Workshop 2**: Technical design (four-layer architecture, PostGIS matching algorithm, reliability scoring, staggered notifications).

**Key Achievements (Workshop 3)**:
- Surplus Recovery Rate **≥ 80%**
- Backend Matching Latency **< 2 seconds**
- Pickup Completion Rate **≥ 85%** under concurrent-user scenarios
- Enhanced architecture with asynchronous messaging (message broker) and service abstraction for external mapping providers
- Full traceability to all 17 requirements and mitigation of the 10 critical risks
- Comprehensive quality assurance (unit, integration, acceptance, and pilot testing strategy)

The platform promotes the **circular economy**, reduces food waste (Colombia generates ~9.7 million tons annually), and supports Bogotá’s “Yo Contribuyo, No Desperdicio” strategy.

## Workshop Objectives

- Implement a robust, scalable, and maintainable full-stack prototype using the Workshop 2 architecture.
- Validate the system through systematic testing and simulation (concurrent users, edge cases, sensitivity analysis).
- Demonstrate compliance with ISO/IEC 25010 (reliability, maintainability) and ISO 31000 (risk management).
- Produce reproducible artifacts following computer-science collaboration best practices.

## Team
- **Luna Alejandra Sandoval Rodríguez** (20241020053) – Systems Analyst / Project Lead  
- **Cristian Camilo Bonilla Lizarazo** (20241020015) – Systems Analyst / Frontend Developer  
- **Nicolás Rodríguez Granados** (20241020037) – Systems Analyst / Backend Developer  
- **Juan Sebastián Bravo Rojas** (20241020004) – Systems Analyst / Database Specialist 

## Status
✅ **Completed** – Delivered April 2026

## Diagrams & Artifacts
- Gantt Diagram
- Quality Process Flow
- Robust Architexture Diagram
- System Architecture Diagram (Update)

## Related Files
- [`Workshop_3.pdf`](./Workshop_3.pdf) – Full Robust Sistem and Project Management

**Last updated**: April 26, 2026  
**Academic Context**: Systems Analysis & Design Course – Universidad Distrital Francisco José de Caldas, 2026-I
