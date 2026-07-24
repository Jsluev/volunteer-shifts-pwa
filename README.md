# Volunteer Shifts Management System

Multi-tenant PWA for managing volunteer shifts in hospitals.

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy (async), PostgreSQL
- **Frontend:** Next.js 15, React 19, Tailwind CSS
- **Infrastructure:** Docker, Redis

## Quick Start

```bash
docker-compose up -d
```

Then run migrations:

```bash
docker-compose exec backend alembic upgrade head
```

Access:
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

## Development

### Backend

```bash
cd backend
pip install -e .
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/shifts/` - List shifts
- `POST /api/v1/shifts/` - Create shift (coordinator)
- `POST /api/v1/registrations/` - Register for shift
- `PATCH /api/v1/registrations/{id}/moderate` - Approve/reject (coordinator)
- `GET /api/v1/notifications/` - List notifications
- `GET /api/v1/chat/dialogs` - List chat dialogs
- `GET /api/v1/analytics/fill-rate` - Fill rate analytics
