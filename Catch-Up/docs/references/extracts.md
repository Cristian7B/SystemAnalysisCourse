# Key Points Abstraction

**Food Waste Reduction Platform**  
**Author:** Nicolás Rodríguez  

---

## 1. Problem and Context

The project addresses the high level of food waste in Colombia, especially in urban environments where cafeterias and restaurants generate daily surpluses. The lack of coordination and the short shelf life of food make efficient redistribution difficult.

The proposed solution consists of a **digital platform** that connects suppliers (restaurants and cafeterias) with demand-side users (students, community members, and foundations), facilitating real-time redistribution.

---

## 2. System Definition

The system is a mobile application aimed at redistributing food surpluses under the following conditions:

* Geographic radius limited to 3 km  
* Real-time operation  
* Strict time windows (same day)  
* Digital coordination (no transportation or payments)  

---

## 3. Main Components

The system is structured into three key components:

* **Frontend:** Mobile application for user interaction  
* **Backend:** System logic and data management  
* **Matching Engine:** Assignment algorithm based on proximity, priority, and availability  

---

## 4. Functional Model (IPO)

### Inputs

* Surplus information (type, quantity, expiration)  
* Geolocation data  
* User profiles and preferences  

### Processes

* Surplus publishing  
* Automatic matching  
* Notification and acceptance  
* Tracking and confirmation  

### Outputs

* Effective food redistribution  
* Impact metrics (kg recovered, success rates)  

---

## 5. Stakeholders

* **Users:** students, community, foundations  
* **Suppliers:** restaurants and cafeterias  
* **Administrators:** system management and monitoring  
* **External actors:** institutions, authorities, technological infrastructure  

---

## 6. Key Findings (Workshop 1)

* High dependency on geolocation  
* Sensitivity to users who do not pick up (no-shows)  
* Concurrency issues during peak hours  
* Risk of inequity due to proximity  
* Emergent behaviors (external coordination)  

---

## 7. Design Requirements (Workshop 2)

* Matching in less than 2 seconds  
* Recovery ≥ 80% of surplus  
* Pickup rate ≥ 85%  
* Notifications in less than 5 seconds  
* Support for multiple concurrent users  

---

## 8. System Architecture

* **Frontend:** React Native  
* **Backend:** NestJS  
* **Database:** PostgreSQL + PostGIS  
* **Cache and concurrency:** Redis  

Modular architecture with separation of responsibilities and support for real-time processing.

---

## 9. Implementation Strategy

Development is divided into three phases:

1. Basic infrastructure  
2. Matching engine and coordination  
3. Analytics, monitoring, and validation  

---

## 10. Risk Management

### Critical sensitivities

* High simultaneous demand  
* Geolocation failures  

### Emergent behaviors

* External user networks  
* Supplier dropout  

### Chaotic dynamics

* Cascades due to no-shows  
* Notification saturation  

**Solutions:**

* Tiered notifications  
* Automatic reassignment  
* Reputation system  

---

## 11. Monitoring and KPIs

* Food recovery rate  
* System response time  
* Successful pickup rate  
* Concurrency capacity  

---

## 12. Conclusion

The platform integrates analysis and design to offer a viable technological solution to food waste. Through the use of geolocation, assignment algorithms, and real-time monitoring, it improves redistribution efficiency and generates positive social and environmental impact.

---
# Key Points Abstraction

**Food Waste Reduction Platform**

**Author:** Cristian Bonilla

## 13. Interesting Findings (Workshop 1 and 2)

* **Exclusion of transportation logistics:** It is essential to note that the system will NOT control or manage food transportation. Responsibility and pickup logistics fall entirely on the users.  
* **Critical operating window (8am - 5pm):** The platform will reach its peak operation between 8am and 5pm, a period of high concurrency where the system must ensure maximum availability, stability, and performance.  
* **Implementation of a Feedback Loop:** Workshop 1 highlights the need to design a continuous feedback mechanism to iterate and improve the system based on user experience. The question remains open on how to collect this feedback effectively without introducing friction, so it can be used for system design and improvement.  
* **Risk of bottlenecks due to concurrency:** There is concern about handling hundreds of simultaneous requests or "uploads" that could saturate the system and leave users without response. This requires clear mitigation strategies (e.g., message queues).  
* **BFF Architecture Proposal (Backend for Frontend):** The BFF is proposed as a highly interesting and suitable architectural solution to adapt, orchestrate, and efficiently optimize server responses to the specific needs of the mobile interface.  
* **100% local execution environment:** It was defined that the infrastructure will be "all local"; that is, the entire application, databases, and services will run strictly in local environments for testing. For now, there will be no deployment to production or the cloud.  

---

# Key Points Abstraction

**Food Waste Reduction Platform**  
**Author:** Luna Alejandra Sandoval Rodríguez  
**Date:** March 23, 2026  

## 14. Decomposition into 4 Subsystems (Workshop 1)
- User Interaction System (registration, mobile, notifications)  
- Surplus Management System (publishing, geolocation, DB)  
- Assignment and Coordination System (matching, assignment, tracking)  
- Monitoring and Analysis System (logs, dashboard, metrics)  

## 15. Table of 17 Exact Measurable Requirements (Workshop 2)
- **REQ-01:** 3 km radius with ±50 m accuracy (100% enforcement)  
- **REQ-03:** ≥90% of offers ≥10 kg go first to charities  
- **REQ-06:** 15 min timeout + automatic reassignment  
- **REQ-09:** ≥200 concurrent users without degradation  
- **REQ-11:** Peripheral users (2.5–3 km) receive ≥15% of matches  
- **REQ-13:** Matching decision <2 seconds (95%)  
- **REQ-17:** User with >3 no-shows in 7 days → 48 h restriction  

## 16. Specific Risk Mitigations (Workshop 2)
- Tiered notifications by distance (500 m → 1 km → 3 km)  
- User reliability score (100 initial points –20 per no-show)  
- Equity index on dashboard to detect geographic bias  
- Automatic alerts if unclaimed_rate >20% for 3 days  
- Maximum of 3 reassignments per surplus  

## 17. Defined Interfaces and Data Flows (Workshop 2)
- User Management API (HTTPS + JWT)  
- Surplus Registration → Geo Service → Matching Engine  
- Notification Service (Expo Push + FCM)  
- Closure & Verification (QR or photo)  
- WebSocket for real-time tracking  

## 18. 6-Week Implementation Phases (Workshop 2)
- **Phase 1 (weeks 1-2):** Auth + Surplus CRUD + Docker  
- **Phase 2 (weeks 3-4):** Serialized matching + tiered notifications + WebSocket  
- **Phase 3 (weeks 5-6):** Dashboard + KPIs + user reliability + local validation  

## 19. Feedback Loop and Continuous Improvement Metrics (Workshop 2)
- Weekly metric review by admin  
- Algorithm tuning based on fairness and equity index  
- User behavior analysis (repeated no-shows)  
- Optimization based on peak load patterns  
