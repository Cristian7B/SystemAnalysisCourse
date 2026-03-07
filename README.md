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
