# Workshop 2 — Systems Design  
**Food Waste Reduction Platform**  
**Semester 2026-I** | Universidad Distrital Francisco José de Caldas  

**Team**  
- Luna Alejandra Sandoval Rodríguez (20241020053) — Systems Analyst / Project Lead  
- Cristian Camilo Bonilla Lizarazo (20241020015) — Systems Analyst / Frontend Developer  
- Nicolás Rodríguez Granados (2024102037) — Systems Analyst / Backend Developer  
- Juan Sebastián Bravo Rojas (20241020004) — Systems Analyst / Database Specialist  

---

## Workshop Objectives (aligned with course guidelines)
This workshop delivers the **complete technical design** of the mobile Food Waste Reduction Platform as a direct continuation of Workshop 1.  
Key deliverables:
- High-level architecture + component responsibilities  
- 17 traceable, measurable design requirements (REQ-01 to REQ-17)  
- Technology stack, data flows, interfaces, and external services  
- Three-phase implementation roadmap (6 weeks)  
- Risk/complexity mitigation table for the 10 critical sensitivities identified in Workshop 1  
- KPIs, monitoring strategy, and success criteria  
- Local deployment blueprint (Docker Compose)  

All design decisions ensure **≥80 % surplus recovery**, **matching < 2 s**, **pickup ≥85 %**, and strict enforcement of the 3 km radius + same-day freshness window.

---

## Diagrams:
- [High-level architecture](https://github.com/Cristian7B/SystemAnalysisCourse/tree/main/Workshop_2/diagrams/architecture-high-level.png)  
- [Detailed data flows](https://github.com/Cristian7B/SystemAnalysisCourse/tree/main/Workshop_2/diagrams/data-flows/)

---
## Git Workflow & Collaboration (TeamWork_CS best practices)

- **Branches**: `feature/matching-engine`, `feature/notifications`, `docs/requirements-update`, `phase/1-core-infra`
- **Commits**: Atómicos + descriptivos (ejemplo: `feat: implement serialized Bull queue for REQ-09`)
- **Pull Requests**: Revisión por pares obligatoria

---

**Last updated**: March 20, 2026  
**Status**: Design complete ✓ | Phase 1 development started  

**Questions?** Abre un issue o menciona @luna-sandoval en el repo.


