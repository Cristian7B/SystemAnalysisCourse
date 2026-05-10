# System Analysis
This repository contains all the projects from the systems analysis and design course in Universidad Distrital Francisco José de Caldas in the 2026-1 semester.

## 📁 Main Folders

- [Workshop 1 - Systems Analysis](./Workshop_1)  
  Comprehensive analysis of the Food Waste Redistribution Platform through primary data collection and systematic investigation. Includes system identification, element analysis, relationship mapping, sensitivity analysis, and complexity theory aspects.

- [Workshop 2 - Systems Design](./Workshop_2)  
  Detailed system architecture for the Food Waste Redistribution Platform, addressing challenges and opportunities identified in Workshop 1. Covers component design, priority-based access logic, and geospatial query specifications.

- [Workshop 3 - Robust Design & Project Management](./Workshop_3)  
  Enhancement of the system design through robust engineering principles and comprehensive project management planning. Includes risk mitigation, quality assurance strategies, and iterative development planning.

- [Workshop 4 - Simulation, Validation & Implementation](./Workshop_4)  
  Computational simulation, stakeholder validation, and functional prototype of the Food Waste Redistribution Platform. Integrates insights from all previous workshops into a cohesive, working solution with real-world testing and measurable improvements.

## 🧑‍💻 Members

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