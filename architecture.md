# Архитектура проекта Volunteer Shifts PWA

## Обзор

Мульти-tenant система управления сменами волонтёров в больницах. Бэкенд на FastAPI + PostgreSQL, фронтенд на Next.js, инфраструктура в Docker Compose.

---

## Структура проекта

```
projectV/
├── docker-compose.yml        # Оркестрация 4 сервисов
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml         # Все зависимости + pytest конфиг
│   ├── alembic/               # Миграции (async)
│   ├── app/
│   │   ├── main.py            # Точка входа FastAPI, CORS, seed-данные
│   │   ├── core/              # Конфиг, БД, безопасность
│   │   ├── models/            # 9 ORM-моделей
│   │   ├── schemas/           # Pydantic v2 схемы валидации
│   │   ├── api/v1/            # 8 роутеров (REST)
│   │   └── services/          # Бизнес-логика (уведомления, аудит)
│   └── tests/                 # 54 теста, 7 файлов
└── frontend/
    ├── Dockerfile
    └── src/
        ├── lib/api.ts         # HTTP-клиент с JWT
        ├── components/        # Sidebar
        └── app/               # 8 страниц (App Router)
```

---

## Ключевые архитектурные решения

### 1. Мульти-тенантность через `tenant_id`

Все таблицы (кроме `tenants`) имеют столбец `tenant_id` с `ON DELETE CASCADE`. Изоляция данных обеспечивается на уровне запросов — каждый эндпоинт фильтрует по `current_user.tenant_id`.

**Почему так:** Проще всего для MVP. Нет шардирования, нет отдельных схем — один PostgreSQL, один ключ. Когда понадобится масштабирование, можно перейти на row-level security или отдельные схемы.

### 2. Ядро безопасности (`core/`)

| Модуль | Ответственность |
|---|---|
| `config.py` | Все настройки из ENV через `pydantic-settings`. Singleton через `@lru_cache` |
| `database.py` | Async SQLAlchemy engine (pool_size=20), сессия, `get_db` зависимость FastAPI |
| `security.py` | bcrypt (passlib), JWT (python-jose, HS256), `get_current_user` — декодирует Bearer-токен, находит пользователя |

**Почему async:** PostgreSQL через asyncpg + Redis — всё I/O-bound. Запросы к БД не блокируют event loop.

### 3. Модели (`models/`) — 9 таблиц

| Таблица | Зачем | Особенности |
|---|---|---|
| `tenants` | Корень мульти-тенантности | Slug уникален, настройки в JSONB |
| `users` | Пользователи 4 ролей | Составной индекс (tenant_id, role), settings в JSONB |
| `departments` | Подразделения больницы | Уникальное (tenant_id, name) |
| `shifts` | Смены | Жизненный цикл: draft → published → closed/cancelled. Partial index по опубликованным |
| `shift_registrations` | Записи на смены | 5 статусов, уникальное (shift_id, user_id), partial indexes для быстрых выборок |
| `dialogs` | Диалоги чата | `participant_ids` — `ARRAY(Integer)` в PostgreSQL |
| `chat_messages` | Сообщения | Индекс (dialog_id, created_at) для пагинации |
| `notifications` | Уведомления | 4 канала (email/push/inapp/sms), partial index по pending + scheduled_at |
| `audit_logs` | Аудит действий | JSONB `meta` для произвольных данных, индекс (tenant_id, user_id, created_at) |

### 4. Схемы (`schemas/`) — Pydantic v2

Каждый домен имеет свою схему: запрос (`*Create`, `*Update`) и ответ (`*Response` с `from_attributes=True`). Отделены от ORM — API принимает/возвращает JSON, модели работают с БД.

**Почему отдельно от моделей:** Чистая архитектура. Схема API не привязана к структуре БД. Можно менять таблицы без сломанных клиентов.

### 5. API (`api/v1/`) — 8 роутеров

| Роутер | Путь | Доступ |
|---|---|---|
| `auth.py` | `/api/v1/auth` | Все (регистрация, логин, refresh) |
| `shifts.py` | `/api/v1/shifts` | Координатор — CRUD; волонтёр — чтение |
| `registrations.py` | `/api/v1/registrations` | Волонтёр — запись/отмена; координатор — модерация |
| `departments.py` | `/api/v1/departments` | Координатор — CRUD; волонтёр — чтение |
| `notifications.py` | `/api/v1/notifications` | Координатор — broadcast; все — чтение |
| `notification_settings.py` | `/api/v1/notification-settings` | Все (свои настройки) |
| `chat.py` | `/api/v1/chat` | Участники диалога |
| `analytics.py` | `/api/v1/analytics` | Только координатор |

**Почему v1:** Версионирование API с первого дня. Когда понадобится v2 — не придётся ломать клиентов.

### 6. Сервисы (`services/`) — бизнес-логика вне роутеров

| Сервис | Что делает |
|---|---|
| `notifications.py` | Создание уведомлений, напоминания по сменам (2 дня / 15ч / 1.5ч), broadcast |
| `audit.py` | `log_action()` — запись действий координаторов в audit_logs |

**Почему отдельно от роутеров:** Переиспользование. Один и тот же `log_action()` вызывается из shifts, registrations и notifications.

### 7. Миграции (Alembic)

Две миграции в `alembic/versions/`:
- **001**: Все 9 таблиц, индексы, ограничения
- **002**: Добавление `settings` JSONB в users

`env.py` настроен на async-режим через `async_engine_from_config`.

### 8. Тесты

54 теста, 7 файлов, все через `pytest-asyncio` (auto mode).

**Ключевые решения в `conftest.py`:**
- Сессионный engine для тестов (создаётся один раз)
- `setup_database` — autouse, пересоздаёт схему `public` через raw SQL (не `drop_all` — он вызывает `asyncpg InterfaceError`)
- `client` и `db` используют один `test_session_factory` — иначе данные не видны между фикстурами
- `seed_tenant()` создаёт пользователя с реальными ID, тесты не хардкодят ID

**Почему не `Base.metadata.drop_all()`:** asyncpg не может выполнять reflection пока другой запрос в процессе. Raw SQL `DROP SCHEMA ... CASCADE` работает надёжно.

### 9. Фронтенд (Next.js 15)

| Решение | Причина |
|---|---|
| App Router (`app/`) | Современный Next.js, layouts, server components |
| `apiFetch()` в `lib/api.ts` | Единая точка для JWT. При 401 — очистка токена и редирект на `/` |
| Tailwind CSS | Быстрая верстка без CSS-in-JS overhead |
| Sidebar компонент | Общий для всех страниц, показывает навигацию по ролям |
| Нет WebSocket | Чат через polling. Для MVP достаточно, WebSocket добавится позже |
| `lang="ru"` | Русскоязычный интерфейс |

### 10. Docker Compose — 4 сервиса

| Сервис | Образ | Порт | Зачем |
|---|---|---|---|
| `db` | postgres:16-alpine | 5432 | Основная БД |
| `redis` | redis:7-alpine | 6379 | Настроен, но пока не используется (кэш, pub/sub, WebSocket потом) |
| `backend` | python:3.11-slim | 8000 | FastAPI + uvicorn |
| `frontend` | node:20-alpine | 3000 | Next.js dev server |

---

## Что ещё не реализовано (но архитектурно готово)

- **Email/Push/SMS доставка** — каналы определены в модели, но нет воркеров
- **Redis** — подключён, но не используется (кэширование, rate limiting, WebSocket pub/sub)
- **WebSocket чат** — фронтенд опрашивает, нужно перейти на реалтайм
- **Cron для напоминаний** — `trigger-reminders` эндпоинт есть, но нет планировщика
- **Frontend role guards** — роли проверяются на бэкенде, фронтенд пока не скрывает UI по ролям
- **Refresh token на фронтенде** — при 401 просто выкидывает из системы
