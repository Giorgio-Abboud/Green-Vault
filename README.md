# Green-Vault  
Capstone II Project  

## Overview
Green-Vault is a full-stack system composed of three interconnected services:
- **UI (React + Vite)** → user interface for signup, login, and running analyses  
- **Analyzer (FastAPI, Python)** → performs trade analysis and returns metrics  
- **Internal API (Go + GORM + Postgres)** → handles authentication, database storage, and data retrieval  

Each service runs in its own Docker container, communicating over HTTP inside the Docker network.  
All data is persisted in your local PostgreSQL database.

---

## Requirements
- Install **Docker**
- Install **Docker Compose plugin**
- Have **PostgreSQL** installed and running locally

---

## Environment Files and Postgres Configuration

### 1️⃣ Internal Service (`internal/.env.docker`)
Create this file:
```
# Connect from container to your host's Postgres
DB_URL=postgres://username:password@host.docker.internal:5432/dbname?sslmode=disable

JWT_SECRET=change-me
```
* For local dev, create `internal/.env.local`:
```
# Connect from container to your host's Postgres
DB_URL=postgres://username:password@localhost:5432/dbname?sslmode=disable

JWT_SECRET=change-me
```

### 2️⃣ Postgres Setup
You must have:
* A Postgres user and database created manually:
```
CREATE USER your_user WITH PASSWORD 'your_password';
CREATE DATABASE dbname OWNER your_user;
```
* Allow Docker containers to connect:
- In ```postgresql.conf```:
```
listen_addresses = '*'
```
- In ```pg_hba.conf```:
```
host all all {subnet_docker_network} md5
```
- Restart PostgreSQL

## Architecture Summary

### Backend (Go API)
* Located in internal/cmd/api/main.go
* Uses GORM for ORM and automatic migrations
* Defines REST endpoints in /v1:
  * POST /v1/users → Signup
  * POST /v1/login → Login
  * POST /v1/fills → Save trade fills + metrics
  * GET /v1/me → (future) Get current user info
To add more routes:
1. Create a new handler in internal/package/handlers/.
2. Register it in main.go under r.Route("/v1", func(rt chi.Router) { ... }).
Example:
```
rt.Get("/transactions", handlers.ListTransactions(app))
```

### Analyzer (FastAPI)
* Located in analyzer/cmd/main.py
* Computes trade metrics and returns structured JSON:
```
{
  "ok": true,
  "request_id": "uuid",
  "fills": {...},
  "metrics": {...}
}
```
* No database access; purely computational.
To add more endpoints, edit ```cmd/main.py``` and add another ```@app.post()``` or ```@app.get()```.

### Frontend (React + Vite)
* Located in ui/src/
* Uses React Router for navigation between pages:
  * ```/signup``` → Create new user
  * ```/login``` → Log in
  * ```/calculate``` → Run analysis (calls Analyzer + Go API)

To add new pages:
Create a component in ```ui/src/pages/``` (e.g. ```Profile.jsx```)
Add a ```<Route>``` entry in ```ui/src/main.jsx```:
```
<Route path="/profile" element={<Profile />} />
```

## Service Connections
| Service | Port | Role | Connects To |
| :--- | :---: | ---: | ---: |
| UI | 5173 | Frontend (React) | Analyzer (8000) + Go API (8080) |
| Analyzer | 8000 | Python FastAPI | Receives requests from UI |
| Internal API | 8080 | Go (auth + DB) | Receives data from UI, connects to Postgres |

All services are orchestrated by Docker Compose, sharing an internal network automatically.

## Run

### Build images
```
docker compose build ui analyzer internal
```

### Run all services
```
docker compose up
```
Access the app at:
http://localhost:5173
