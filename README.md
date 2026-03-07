# 🍎 Food Waste Redistribution Platform

A full-stack platform connecting food donors, charities, trusted collectors, and general recipients to reduce food waste.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite, React-Leaflet, Recharts, PWA |
| Backend | Node.js 20 + Express 4 |
| Database | PostgreSQL 15 + PostGIS 3.3 |
| Auth | JWT (access + refresh tokens) + bcrypt |
| Real-time | Socket.IO |
| Notifications | Nodemailer (email) + web-push (PWA) |
| File upload | Multer |

## Quick Start

### Prerequisites
- Node.js 20+
- Docker Desktop (for PostgreSQL + PostGIS)

### 1. Start the database
```bash
docker-compose up -d
```

### 2. Backend
```bash
cd backend
cp .env.example .env
# Edit .env with your secrets
npm install
npm run dev
# → http://localhost:4000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## User Roles

| Role | Description |
|---|---|
| `donor` | Posts surplus food items |
| `charity` | Verified organization with priority claim window (first 2h) |
| `trusted_collector` | Upgraded general users, second-priority window |
| `general_recipient` | Open access after priority windows expire |
| `admin` | Full moderation + verification capabilities |

## API Endpoints

See `backend/src/routes/` for full documentation. Key prefixes:
- `POST /api/auth/register` — Register
- `POST /api/auth/login` — Login
- `GET/POST /api/surplus` — List/create surplus items
- `POST /api/claims/:surplusId` — Claim an item
- `GET /api/metrics` — Impact dashboard data
- `GET /api/admin/*` — Admin moderation endpoints

## Environment Variables

See `backend/.env.example` for all required variables.


# Food Waste Reduction Platform

## Overview

The **Food Waste Reduction Platform** is a geolocation-centered web application designed to reduce food waste in Bogotá, Colombia. The platform connects food donors such as university cafeterias and restaurants with recipients, prioritizing verified charitable organizations before allowing access to general users.

The system focuses on improving food redistribution efficiency through geographic visualization and a priority-based access system.

Users interact with an interactive map where food donations appear as location pins. Recipients can discover, filter, and claim available food near them.

---

# System Purpose

The main purpose of the platform is to **reduce food waste while increasing social impact** by prioritizing food redistribution to verified charities before opening access to general users.

The system also allows tracking impact metrics such as:

- kilograms of food redistributed
- percentage of food delivered to charities
- number of active users and donations

---

# Objectives

## General Objective

Develop a geolocation-based web platform that facilitates the redistribution of surplus food while prioritizing charitable organizations.

## Specific Objectives

- Implement a backend capable of handling donation registration and priority logic.
- Develop a REST API to connect frontend and backend services.
- Create an interactive map interface to display nearby food donations.
- Implement geospatial queries for efficient location-based discovery.
- Track and measure the social impact of redistributed food.
- Deploy the system using cloud services.

---

# Stakeholders

The system involves several stakeholders:

### Donors
- University cafeterias
- Restaurants
- Food service staff

### Priority Recipients
- Verified charitable organizations
- Community kitchens
- Student organizations

### General Recipients
- University students
- Local community members

### Trusted Collectors
Users who frequently collect donations responsibly and receive trust badges.

### Platform Administrators
Project developers and university partners responsible for maintaining the system.

### External Stakeholders
- Universities
- Local authorities
- Social organizations interested in food redistribution.

---

# Functional Requirements

The system must:

1. Allow donors to create food donation posts.
2. Allow donors to include information such as:
   - food type
   - quantity
   - expiration time
   - location
   - photos.
3. Display donations on an interactive map using geolocation.
4. Allow recipients to search for nearby donations.
5. Implement a **priority access system** where charities have early access.
6. Allow users to claim available food donations.
7. Generate pickup confirmations (for example QR codes).
8. Send notifications when food becomes available.
9. Allow administrators to verify charity organizations.
10. Provide an impact dashboard showing redistributed food statistics.

---

# Non-Functional Requirements

The system should:

- Be accessible through modern web browsers.
- Support responsive design for desktop and mobile devices.
- Ensure reasonable performance for geolocation queries.
- Maintain user privacy and secure authentication.
- Allow scalability for future system expansion.
- Provide reliable storage for images and user data.

---

# System Architecture

The platform follows a **client–server architecture**.

### UI Layer
- Interactive map interface
- Donation posting dashboard
- Claiming system

### Backend Layer
- REST API
- Priority logic implementation
- User authentication
- Geospatial query processing

### Database Layer
- Storage of donation data
- User profiles
- geolocation coordinates

### Supporting Services

- Photo storage
- QR code generation
- Impact analytics dashboard

---

# Technologies Used

## Frontend
- React
- Vite
- HTML
- CSS
- JavaScript
- Leaflet or Google Maps API
- Bootstrap

## Backend
- Node.js / Express or FastAPI
- REST API

## Database
- PostgreSQL
- PostGIS (geospatial queries)

## Authentication
- Firebase Auth or JWT

## Deployment
- Vercel
- Render

---

# Operating Environment

### Geographic Context
The system is designed to operate primarily in **Bogotá**, focusing on university areas and nearby restaurants.

### Connectivity
The platform requires internet connectivity but may use **PWA caching** to improve user experience during intermittent connections.

### Regulatory Context
The system must respect Colombian data protection laws, including **Law 1581 of 2012**, especially regarding user geolocation data.

### Risks

- GPS accuracy issues
- Low user adoption
- API usage limits
- Privacy concerns

---

# Project Structure
project/
│
├── frontend/
│
├── backend/
│
├── database/
│
├── docs/
│
└── README.md

---

# Team Roles

**Luna**  
Project Lead / Backend Developer / Systems Analyst  
Responsible for leading the project, backend development, API implementation, priority logic, geospatial queries, and contributing to system diagrams and academic reports.

**Bravo**  
Database Specialist / Backend Support / Systems Analyst  
Responsible for database design and management, supporting API development, and contributing to system diagrams and project documentation.

**Cristian**  
Frontend Developer / UI-UX Designer  
Responsible for designing and implementing the user interface, developing the interactive map, creating Figma mockups, and ensuring responsive design and usability.

**Nicolás**  
Backend Developer / DevOps / Quality Assurance  
Responsible for backend development support, API testing, system validation, scenario simulation, and deployment using platforms such as Vercel or Render.

---

# Installation

Clone the repository
git clone https://github.com/Cristian7B/SystemAnalysisCourse.git
Enter the project folder
cd food-waste-platform
Install dependencies
npm install
Run the development server
npm run dev

---

# Deployment

The application will be deployed using cloud services such as:

- Vercel
- Render

---

# Academic Context

This project is developed as part of the **Systems Analysis course** at **Universidad Distrital Francisco José de Caldas**, Bogotá, Colombia.

The project focuses on applying concepts of:

- system analysis
- software architecture
- web development
- geospatial systems
- project collaboration
