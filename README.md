# Volunteer Shifts Management System

Multi-tenant PWA for managing volunteer shifts in hospitals.

## Tech Stack

- **Backend:** Python 3.11, FastAPI, SQLAlchemy (async), PostgreSQL 16, Redis 7
- **Frontend:** Next.js 15, React 19, Tailwind CSS
- **Infrastructure:** Docker Compose
- **Chat:** WebSocket real-time messaging
- **Auth:** JWT access + refresh tokens with auto-renewal

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

## Features

- **Multi-tenancy** — data isolation via `tenant_id` on all tables
- **RBAC** — 4 roles: volunteer, coordinator, controller, admin
- **Shift management** — create, publish, cancel shifts with slot tracking
- **Registration workflow** — register, moderate (approve/reject), confirm attendance
- **Real-time chat** — WebSocket-based messaging between participants
- **Notifications** — in-app notifications with unread count badge
- **Analytics** — fill rate, volunteer stats, classification, audit log
- **Auto-reminders** — background task sends reminders 2 days, 15 hours, 1.5 hours before shift
- **Rate limiting** — Redis-based rate limiting on auth endpoints
- **Caching** — Redis caching for shift listings (60s TTL)
- **Refresh token** — automatic JWT renewal on frontend
- **Role guards** — admin pages protected by role check

## API Endpoints

- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login (returns access + refresh tokens)
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Current user profile
- `GET /api/v1/shifts/` - List shifts (cached)
- `POST /api/v1/shifts/` - Create shift (coordinator)
- `PATCH /api/v1/shifts/{id}/publish` - Publish shift
- `PATCH /api/v1/shifts/{id}/cancel` - Cancel shift
- `POST /api/v1/registrations/` - Register for shift
- `PATCH /api/v1/registrations/{id}/moderate` - Approve/reject (coordinator)
- `POST /api/v1/registrations/bulk-moderate` - Bulk moderate
- `GET /api/v1/notifications/` - List notifications
- `GET /api/v1/notifications/unread-count` - Unread count
- `POST /api/v1/notifications/broadcast` - Broadcast message (coordinator)
- `GET /api/v1/chat/dialogs` - List chat dialogs
- `POST /api/v1/chat/dialogs` - Create dialog
- `GET /api/v1/chat/dialogs/{id}/messages` - List messages
- `POST /api/v1/chat/messages` - Send message
- `WS /api/v1/chat/ws/{id}` - WebSocket for real-time chat
- `GET /api/v1/analytics/fill-rate` - Fill rate analytics
- `GET /api/v1/analytics/volunteer-stats/{id}` - Volunteer stats
- `GET /api/v1/analytics/volunteer-classification` - Classification tiers
- `GET /api/v1/analytics/unfilled-slots` - Unfilled slots
- `GET /api/v1/analytics/audit` - Audit log

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

### Tests

```bash
docker-compose exec backend python -m pytest tests/ -v
```

54 tests covering auth, shifts, registrations, departments, notifications, chat, and analytics.
