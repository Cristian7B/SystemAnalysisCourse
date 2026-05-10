# System Analysis

This repository contains all the projects from the systems analysis and design course in Universidad Distrital Francisco José de Caldas in the 2026-1 semester.

## Food Waste Reduction Platform  
**Real-Time Surplus Food Redistribution Mobile Application**

## 📋 Project Overview
This repository contains the complete development of the **Food Waste Reduction Platform**, a geospatially constrained mobile application that connects cafeterias and restaurants with students, volunteers, and verified charities within a strict 3 km radius around the Faculty of Engineering at **Universidad Distrital Francisco José de Caldas**, Bogotá, Colombia.

The platform enables real-time surplus food redistribution with mandatory same-day operation (publication 2–4 h before closing, pickup 1–3 h), priority for verified organizations, and proximity-based matching using PostGIS.

**Course**: Systems Analysis & Design – Semester 2026-I  
**Professor**: Eng. Carlos Andrés Sierra, M.Sc.

## 📁 Main Folders

### Workshop 1 – Systems Analysis (Completed)
**Folder**: [`./Workshop_1`](./Workshop_1_Analysis)
  Comprehensive analysis of the Food Waste Redistribution Platform through primary data collection and systematic investigation. Includes system identification, element analysis, relationship mapping, sensitivity analysis, and complexity theory aspects.
  **Key deliverables**: System overview, spatial/temporal boundaries, component table, and full risk identification.

### Workshop 2 – Systems Design (Completed)
**Folder**: [`./Workshop_2`](./Workshop_2_Design) 
  Detailed system architecture for the Food Waste Redistribution Platform, addressing challenges and opportunities identified in Workshop 1. Covers component design, priority-based access logic, and geospatial query specifications.
  **Key deliverables**: System architecture diagram, algorithm description, interface definitions, and traceability matrix to Workshop 1 requirements.

### Workshop 3 – Robust System Design and Project Management (**In Progress**)
**Folder**: [`./Workshop_3`](./Workshop_3_Management)
  Enhancement of the system design through robust engineering principles and comprehensive project management planning. Includes risk mitigation, quality assurance strategies, and iterative development planning.
  **Current status**: In development – Delivery: **25 April 2026**  
  **Key deliverables in progress**: Risk matrix, quality metrics, Gantt chart, enhanced architecture diagrams, and complete Project Management Plan.

### Workshop 4 – System Simulation and Validation (Upcoming)
**Folder**: [`./Workshop_4`](./Workshop_4)
  Computational simulation, stakeholder validation, and functional prototype of the Food Waste Redistribution Platform. Integrates insights from all previous workshops into a cohesive, working solution with real-world testing and measurable improvements.
  **Key deliverables**: Simulation code, experimental results, statistical validation, and updated academic deliverables (Paper, Poster, Report).

## 🧑‍💻 Team Members

| Name                            | ID         | Email                          | Role                          |
|---------------------------------|------------|--------------------------------|-------------------------------|
| Luna Alejandra Sandoval Rodriguez | 20241020053 | luasandovalr@udistrital.edu.co | Systems Analyst / Project Lead / Backend Developer |
| Cristian Camilo Bonilla Lizarazo  | 20241020015| ccbonillal@udistrital.edu.co   | Systems Analyst  / Frontend Developer / UI-UX Designer |
| Nicolas Rodriguez Granados  | 20241020037| nicorodriguezg@udistrital.edu.co | Systems Analyst / Backend Developer / QA |
| Juan Sebastian Bravo Rojas  | 20241020004| jsbravor@udistrital.edu.co | Systems Analyst / Database Specialist / Backend Support |
## 🚀 FoodBridge — MVP Setup

Mobile platform for real-time food surplus redistribution within a 3 km radius of Universidad Distrital Francisco José de Caldas.

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React Native + Expo |
| Backend | NestJS (Node.js) |
| Database | PostgreSQL + PostGIS |
| Cache / Queue | Redis + Bull |
| Notifications | Firebase Cloud Messaging (FCM) |
| Containerization | Docker Compose |

### Project Structure
├── backend/        # NestJS API
├── frontend/       # React Native + Expo app
├── docs/           # Architecture diagrams, API docs
├── scripts/        # DB seeds, migration scripts
├── docker-compose.yml
├── .env.example
└── README.md
### Installation

**Prerequisites:** Node.js >= 18, Docker Desktop, Expo CLI (`npm install -g expo-cli`)

1. Switch to develop branch: `git checkout develop`
2. Copy env file: `cp .env.example .env`
3. Start database: `docker compose up -d`
4. Run backend: `cd backend && npm install && npm run start:dev`
5. Run frontend: `cd frontend && npm install && npx expo start`

### Code Conventions

- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`)
- **Branches:** `feature/`, `fix/`, `docs/` prefixes
- **Linting:** ESLint + Prettier enforced via Husky pre-commit hook
- **PRs:** All PRs target `develop`, reviewed by at least one teammate
