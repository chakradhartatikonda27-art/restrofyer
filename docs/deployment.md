# Deployment & Infrastructure Guide

## 1. Local Development Setup

### Prerequisites
- Python 3.11+ / 3.14
- Node.js 18+ (Node 24 tested)
- PostgreSQL 15+ (or SQLite for local sandboxed development)

### Backend Startup
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python seed_data.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be accessible at: `http://localhost:8000/api/v1/docs`

### Frontend Startup
```bash
cd frontend
npm install
npm run dev
```
Web application will be accessible at: `http://localhost:3000`

---

## 2. Docker & Containerized Deployment

A production-ready `Dockerfile` and `docker-compose.yml` are provided in the repository root.

```bash
docker-compose up --build -d
```

### Services
1. `db`: PostgreSQL 16 Alpine with initialized RLS extensions and persistent volume.
2. `backend`: FastAPI Uvicorn ASGI server with Gunicorn workers.
3. `frontend`: Next.js production standalone server with static asset caching.
