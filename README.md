# 🛰️ LeadScout — Autonomous Lead Discovery & Intelligence Platform

> **Production-Grade Enterprise Lead Generation System**
>
> High-performance Next.js frontend integrated with an async FastAPI backend, distributed Celery workers, Redis pub/sub streaming, and PostgreSQL database.

---

## 📋 Table of Contents
1. [System Architecture](#-system-architecture)
2. [End-to-End Pipeline Workflow](#-end-to-end-pipeline-workflow)
3. [Technology Stack](#-technology-stack)
4. [Key Features & Capabilities](#-key-features--capabilities)
5. [Project Structure](#-project-structure)
6. [Quick Start & Setup](#-quick-start--setup)
7. [API & WebSocket Reference](#-api--websocket-reference)
8. [Testing & Verification](#-testing--verification)
9. [Production Runbook](#-production-runbook)

---

## 🏛️ System Architecture

```
                                  ┌────────────────────────┐
                                  │   Next.js 16 Client    │
                                  │   (React 19, Tailwind) │
                                  └───────────┬────────────┘
                                              │
                         HTTP REST (Bearer)   │   WebSocket (/api/ws/tasks/{id})
                                              │
                                  ┌───────────▼────────────┐
                                  │   FastAPI Gateway      │
                                  │   (Uvicorn, Pydantic)  │
                                  └─────┬──────────────┬───┘
                                        │              │
                   PostgreSQL / asyncpg │              │ Redis Pub/Sub
                                        │              │
                  ┌─────────────────────▼─┐          ┌─▼──────────────────────┐
                  │ PostgreSQL Database   │          │ Redis (Broker & PubSub)│
                  │ (SQLAlchemy 2.x ORM)  │          └─┬──────────────────────┘
                  └───────────────────────┘            │
                                                       │ Celery Distributed
                                                       │ Task Queue
                                             ┌─────────▼──────────────┐
                                             │ Celery Worker Pool     │
                                             │ ┌────────────────────┐ │
                                             │ │  Discovery Engine  │ │
                                             │ ├────────────────────┤ │
                                             │ │  Resilient Crawler │ │
                                             │ ├────────────────────┤ │
                                             │ │  Extraction Engine │ │
                                             │ ├────────────────────┤ │
                                             │ │  Cleaning & Dedup  │ │
                                             │ ├────────────────────┤ │
                                             │ │  Verification      │ │
                                             │ └────────────────────┘ │
                                             └────────────────────────┘
```

---

## 🔄 End-to-End Pipeline Workflow

1. **Task Submission (`POST /api/scrape`)**:
   - Client submits keyword, location, radius, and targeted fields.
   - Guarded by double-click idempotency keys and rate limiting (10 tasks/hour/user).
   - Task record initialized in PostgreSQL; Celery task dispatched.
2. **Discovery (`run_discovery_stage`)**:
   - Searches and enumerates candidate business entities and their official domains.
3. **Crawl (`run_crawler_stage`)**:
   - Crawls target domains safely under strict SSRF rules, `robots.txt` compliance, domain rate limiting, and access detection (CAPTCHA/paywall avoidance).
4. **Extraction (`run_extraction_stage`)**:
   - Parses normalized phone numbers, emails, addresses, social profiles, and executive contacts.
5. **Cleaning & Deduplication (`run_cleaning_stage`)**:
   - Resolves duplicate organizations, canonicalizes phone numbers and emails, and reconciles domain merges.
6. **Verification & Audit (`run_verification_stage`)**:
   - Computes weighted 3-pillar confidence scores (Completeness, Source Quality, Consistency) and assigns confidence tiers (`HIGH`, `MEDIUM`, `LOW`).
7. **Real-time Streaming (`WebSocket /api/ws/tasks/{taskId}`)**:
   - Monotonic progress percentages, stage changes, and activity logs published via Redis Pub/Sub directly to the client UI.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 16.3.4 (App Router), React 19, TypeScript 5, Tailwind CSS v4, Radix UI, Lucide Icons, Recharts, Sonner |
| **Backend API** | FastAPI 0.115+, Uvicorn, Pydantic v2, Python 3.12+ / 3.14 |
| **Database & ORM** | PostgreSQL 16+, SQLAlchemy 2.x (async), asyncpg, Alembic migrations |
| **Task Queue & Cache** | Celery 5.4+, Redis 7+ (Broker, Result Backend, Pub/Sub, Sliding Rate Limiter) |
| **Crawling & Safety** | HTTPX, BeautifulSoup4, SSRF Validator, `robots.txt` TTL Cache, Circuit Breaker |
| **Testing** | pytest, pytest-asyncio, aiosqlite, unittest |

---

## 🚀 Key Features & Capabilities

- **Zero Mock Data in Production Flows**: Dashboard, task history, live progress, leads directory, lead detail profiles, and exports all run against live backend endpoints with real SQL aggregations.
- **Real-Time Progress & Resilient Reconnection**: WebSockets deliver real-time progress snapshots and streaming activity logs with bounded exponential reconnects (max 5 attempts) and fallback REST polling.
- **Multi-Tenant User Isolation**: Strict user-ownership filters ensure each authenticated user only accesses their own tasks, leads, and exports.
- **Double-Click & Idempotency Protection**: `Idempotency-Key` headers on task creation protect against duplicate jobs from network retries or multiple clicks.
- **Responsible Crawling & SSRF Protection**: Full defense-in-depth preventing access to private subnets, cloud metadata services, and disallowing bypass of robots.txt.
- **Enterprise Verification Engine**: Multi-metric lead validation showing completeness percentage, source quality score, consistency score, and audit reasons.
- **Multi-Format Streaming Export**: Export task results or user leads directly into CSV and Excel (`.xlsx`) with custom field selection.

---

## 📁 Project Structure

```
web/leadscout/
├── app/                        # Next.js App Router (Pages & Layouts)
│   ├── (auth)/                 # Login, Signup, Forgot/Reset Password
│   ├── dashboard/              # Live KPI metrics, charts, recent tasks
│   ├── tasks/                  # Task history, task creation, live progress
│   ├── leads/                  # Filterable, paginated lead directory & detail view
│   ├── exports/                # Export management and download triggers
│   └── settings/               # Profile, security, and preferences
├── components/                 # Shared UI components (Modals, Badges, Tables, Nav)
├── features/                   # Feature-specific modules (Dashboard, Tasks, Leads, Export)
├── lib/                        # API client, WebSocket builder, export utilities
├── backend/                    # FastAPI & Celery Backend
│   ├── app/
│   │   ├── api/routes/         # REST API routes (auth, tasks, leads, dashboard, export, ws)
│   │   ├── core/               # Configuration, security middleware, rate limiters
│   │   ├── db/                 # Database engine & async session factories
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── repositories/       # Data access layer
│   │   ├── services/           # Business logic & pipeline engines
│   │   └── workers/            # Celery pipeline tasks & orchestrator
│   └── tests/                  # 260 unit, integration, security, and e2e tests
```

---

## ⚡ Quick Start & Setup

### Prerequisites
- Python 3.12+ (or 3.14)
- Node.js 20+ & npm
- PostgreSQL 16+
- Redis 7+

### 1. Backend Setup
```bash
cd leadscout/backend

# Create virtual environment and activate
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start FastAPI API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Celery Worker Setup
```bash
cd leadscout/backend
.venv\Scripts\activate

# Start Celery worker
celery -A app.workers.celery_app worker --loglevel=info -P solo
```

### 3. Frontend Setup
```bash
cd leadscout

# Install frontend dependencies
npm install

# Start Next.js development server
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to access the application.

---

## 📡 API & WebSocket Reference

### Core REST Endpoints
- `POST /api/auth/signup` & `POST /api/auth/login` — Authentication & JWT tokens.
- `GET /api/dashboard/summary` — Aggregated counts, recent tasks, category breakdown.
- `POST /api/scrape` — Submit a scraping discovery task (`Idempotency-Key` supported).
- `GET /api/tasks` — List tasks with server-side pagination, search, status filters, and sorting.
- `GET /api/tasks/{taskId}` — Detailed task execution status and collected metrics.
- `POST /api/tasks/{taskId}/cancel` — Gracefully stop a running task.
- `GET /api/leads` — Filter and paginate leads by category, verification tier, and presence of phone/email/website.
- `GET /api/leads/{leadId}` — Full lead entity details, verification breakdown, and source pages.
- `GET /api/tasks/{taskId}/export/csv` & `GET /api/tasks/{taskId}/export/excel` — Download task lead records.

### WebSocket Protocol (`/api/ws/tasks/{taskId}`)
Connect via `ws://localhost:8000/api/ws/tasks/{taskId}?token=<JWT>`:
- `task.snapshot`: Immediate state payload on connection.
- `task.progress`: Monotonic progress percentage updates.
- `task.stage_changed`: Pipeline stage transitions.
- `task.activity`: Activity event log entries with timestamps.
- `task.completed` / `task.failed` / `task.cancelled`: Final lifecycle state notifications.

---

## 🧪 Testing & Verification

### Run Full Backend Test Suite
```bash
cd leadscout/backend
.venv\Scripts\pytest.exe -q --tb=short
# Result: 260 / 260 passed (100% pass rate)
```

### Run End-to-End Journey Suite
```bash
cd leadscout/backend
.venv\Scripts\pytest.exe tests/test_e2e_journey.py -v
# Result: 4 / 4 passed (Auth, Isolation, Pipeline & Dashboard, SSRF Defense)
```

### Run Frontend Type Check & Build
```bash
cd leadscout
npx tsc --noEmit
npm run build
# Result: 14 / 14 routes compiled with zero TypeScript or packaging errors
```

---

## 🛡️ Production Runbook

1. **Environment Variables**: Verify `.env` on backend and `.env.local` on frontend contain appropriate `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, and `NEXT_PUBLIC_API_URL`.
2. **Health Checks**:
   - Liveness probe: `GET /api/live` (HTTP 200).
   - Readiness probe: `GET /api/ready` (Verifies PostgreSQL connection, returns HTTP 200 or 503).
3. **Stale Task Daemon**: Ensure the background periodic job runs to transition tasks stalled for >60 minutes to `FAILED`.
4. **Rate Limits**: Configurable via `SCRAPE_TASK_RATE_LIMIT` (default 10/hour) and `API_RATE_LIMIT` (default 100/min).
