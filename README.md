# Green-Vault  
Capstone II Project  

## Overview
Green-Vault is a full-stack system composed of three interconnected services:
- **UI (React + Vite)** → user interface for signup, login, and running analyses  
- **Analyzer (FastAPI, Python)** → performs trade analysis and returns metrics  
- **Internal API (Go + GORM)** → handles all authentication, http layer, and db layer
- **Postgres DB and Volume** → database storage and data retrieval

Each service runs in its own Docker container, communicating over HTTP inside the Docker network.  
All data is persisted in your local PostgreSQL database.

---

## Requirements
- Install **Docker**
- Install **Docker Compose plugin**

---

## Environment Files and Postgres Configuration

### Postgres DB (`/.env.db`)
Create this file:
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD={password}
POSTGRES_DB=greenvault
```
Setup any password. The postgres instance will automatically create you account with the provided user, password, and db name.

### Internal Service (`internal/.env.docker`)
Create this file:
```
DB_URL=postgres://username:password@db:5432/dbname?sslmode=disable

JWT_SECRET=change-me
```
* For local dev, create `internal/.env.local`:
```
# Connect from container to your host's Postgres
DB_URL=postgres://username:password@localhost:5432/dbname?sslmode=disable

JWT_SECRET=change-me
```

### Update `DB_URL` with valid auth
* Update ```username```, ```password```, and ```dbname``` to the credentials of the postgres container

### Update `JWT_SECRET` with a unique value
* Make sure you have ```openssl``` installed. Linux and Mac users already have it. Windows users can run ```openssl``` using ````wsl```
* Update ```change-me``` to an unique random generated hex value by running
```
openssl rand -hex 32
```
* NOTE: If you ever update ```JWT_SECRET``` again, the session for the previous created users will not be remembered.

### UI Service (`ui/.env`)
Create this file:
```
VITE_CALC_BASE_URL=http://localhost:8000
VITE_API_BASE_URL=http://localhost:8080
```

### Analyzer Service (`analyzer/.env`)
The analyzer makes external requests to Twelve Data. Set up your API key once and keep it out of source control.
#### Steps
1. Go to https://twelvedata.com/login and sign up / sign in.
2. Open **API keys** in your dashboard and click **Reveal** to copy your key.
3. In the project root, create a file named `.env` with:
```
TWELVE_DATA_API_KEY=your_secret_twelve_data_api_key
```

### Run Postgres DB Container
Run this to access postgres db (only after docker compose up):
```
docker exec -it postgres-db psql -U postgres -d greenvault
```
OR
```
psql -h localhost -p 5433 -U postgres -d greenvault
```

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
