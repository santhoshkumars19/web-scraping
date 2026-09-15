# LeadScout Backend

Backend API for the **LeadScout Web Scraping & Lead Discovery Platform**.

Built with **Python 3.12+ (Python 3.14 verified)**, **FastAPI**, **SQLAlchemy 2.x (async)**, **Alembic**, and **PostgreSQL**.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Web Framework | FastAPI 0.115+ |
| ASGI Server | Uvicorn |
| Real-time & WebSockets | FastAPI WebSockets + Redis Pub/Sub |
| Background Workers & Broker | Celery 5.4+ & Redis 7+ |
| ORM | SQLAlchemy 2.x (async) |
| DB Driver | asyncpg |
| Migrations | Alembic |
| Database | PostgreSQL 16+ |
| Validation | Pydantic v2 |
| Testing | pytest + pytest-asyncio + aiosqlite + httpx |

---

## Folder Structure

```
backend/
├── app/
│   ├── main.py               # FastAPI application factory + lifespan
│   ├── core/
│   │   ├── config.py         # Pydantic Settings — reads from .env (DB, Redis, Celery, WS)
│   │   ├── logging.py        # Logging configuration (never logs secrets)
│   │   └── exceptions.py     # Custom AppException hierarchy
│   ├── api/
│   │   └── routes/
│   │       ├── __init__.py   # Central API router
│   │       ├── health.py     # GET /api/health
│   │       ├── tasks.py      # POST /api/scrape, GET /api/tasks, GET /api/tasks/{task_id}
│   │       ├── leads.py      # GET /api/leads, GET /api/leads/{lead_id}, GET /api/tasks/{task_id}/leads
│   │       └── websocket.py  # WS /api/ws/tasks/{task_id} real-time updates
│   ├── realtime/             # Real-time WebSocket connection manager & Redis Pub/Sub
│   │   ├── __init__.py       # Package exports (ConnectionManager, RedisPubSub, etc.)
│   │   ├── events.py         # Real-time event models, types, and builder helpers
│   │   ├── connection_manager.py # ConnectionManager tracking WebSockets per task
│   │   ├── redis_pubsub.py   # Async & sync Redis Pub/Sub client
│   │   ├── publisher.py      # TaskEventPublisher (Redis + Mock for test mode)
│   │   └── subscriber.py     # TaskSubscriberManager managing Redis listener tasks
│   ├── schemas/
│   │   ├── base.py           # Pydantic base model + response envelopes
│   │   ├── task.py           # Task create, response, list, detail schemas (queued, celery_task_id)
│   │   ├── lead.py           # Lead list item, detail, verification, and pagination schemas
│   │   ├── verification.py   # Lead verification scoring & audit schemas
│   │   └── finalization.py   # Finalization summary schemas
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── __init__.py       # Re-exports all models for Alembic discovery
│   │   ├── user.py           # User model
│   │   ├── scraping_task.py  # ScrapingTask model (with celery_task_id)
│   │   ├── organization.py   # Organization model & task_organizations M2M
│   │   ├── lead.py           # Lead (task-to-org link) model
│   │   ├── lead_verification.py # LeadVerification quality score model
│   │   ├── website.py        # Website model
│   │   ├── contact.py        # Contact model
│   │   ├── phone_number.py   # PhoneNumber model
│   │   ├── email_address.py  # EmailAddress model
│   │   ├── source_page.py    # SourcePage provenance model
│   │   ├── social_link.py    # SocialLink profile model
│   │   ├── extracted_field.py# ExtractedField audit model
│   │   ├── organization_merge_event.py # Merge provenance audit model
│   │   └── scraping_log.py   # ScrapingLog event model
│   ├── services/
│   │   ├── task_service.py   # Task business logic & workflow orchestration
│   │   ├── lead_service.py   # Lead business logic, query filtering, and DTO mappings
│   │   ├── task_progress_service.py # Centralized progress, monotonicity, DB commit & events
│   │   ├── discovery_service.py # Organization discovery service
│   │   ├── crawler_service.py   # Resilient website crawler service
│   │   ├── extraction_service.py# Structured data extraction service
│   │   ├── cleaning/         # Cleaning & deduplication pipeline
│   │   ├── verification/     # 3-pillar confidence scoring & quality assessment
│   │   └── finalization_service.py # Pipeline reconciliation & task completion
│   ├── workers/              # Celery background workers & pipeline orchestration
│   │   ├── __init__.py       # Re-exports celery_app, pipeline, stage tasks
│   │   ├── celery_app.py     # Celery app instance, queues, serializers, settings
│   │   ├── task_context.py   # Sync/async worker execution bridge & DB session manager
│   │   ├── tasks.py          # Celery stage tasks with transient retry handling
│   │   └── pipeline.py       # Sequential pipeline chain composer
│   ├── repositories/
│   │   ├── task_repository.py# Data access layer for ScrapingTask
│   │   └── lead_repository.py# Data access layer for Lead entities with selectinload and pagination
│   ├── db/
│   │   ├── base.py           # UUIDMixin, TimestampMixin, Declarative Base
│   │   └── database.py       # Async engine, session factory, get_db()
│   └── utils/
│       └── task_id.py        # Concurrency-safe human-readable Task ID generator
├── alembic/
│   ├── env.py                # Async-compatible migration environment
│   ├── script.py.mako        # Migration file template
│   └── versions/             # Migrations (001_initial_schema, 002_merge, 003_scoring, 004_celery)
├── scripts/
│   └── seed_dev.py           # Fictional development database seeder
├── tests/
│   ├── conftest.py           # Pytest fixtures (async client, static db_session, celery eager)
│   ├── test_health.py        # Health endpoint tests
│   ├── test_config.py        # Configuration tests
│   ├── test_models.py        # Database models & relationships tests
│   ├── test_tasks_api.py     # Scraping Task API & creation workflow tests
│   ├── test_discovery.py     # Discovery Engine tests
│   ├── test_crawler.py       # Website Crawler tests
│   ├── test_extraction.py    # Data Extraction Engine tests
│   ├── test_cleaning.py      # Cleaning & Deduplication tests
│   ├── test_verification.py  # Verification & Scoring tests
│   ├── test_workers.py       # Celery workers, routing, and pipeline orchestration tests
│   └── test_websocket.py     # Real-time WebSocket connection & event tests
├── .env.example              # Environment variable template
├── .env                      # Local dev values (git-ignored)
├── requirements.txt          # Python dependencies
├── alembic.ini               # Alembic configuration
├── pytest.ini                # Pytest configuration
├── Dockerfile                # Multi-stage Docker image
└── docker-compose.yml        # Dev: backend + postgres + redis + worker
```

---

## Scraping Task API (Step 3)

> [!NOTE]
> At this stage, `POST /api/scrape` validates the request, normalizes inputs, generates a unique human-readable Task ID (`TASK-XXXXXX`), and records the task in the database with status `PENDING` and `0%` progress. The actual asynchronous scraping discovery engine and workers will be integrated in subsequent steps.

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/scrape` | Submit and initialize a new scraping task (returns HTTP 201). |
| `GET` | `/api/tasks` | Get paginated task history with filtering and sorting. |
| `GET` | `/api/tasks/{task_id}` | Get full task details, execution status, and metrics. |
| `GET` | `/api/health` | Service liveness probe. |
| `GET` | `/docs` | Interactive Swagger UI API documentation. |

---

### cURL Examples

#### 1. Create a Scraping Task
```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Puducherry",
    "keyword": "CBSE Schools",
    "search_radius": 25,
    "max_results": 100,
    "max_pages_per_site": 20,
    "selected_fields": [
      "name",
      "phone",
      "email",
      "website",
      "address",
      "whatsapp",
      "social_links"
    ],
    "crawl_depth": 3,
    "follow_internal_links": true,
    "prioritize_contact": true,
    "prioritize_about": true,
    "prioritize_admissions": true,
    "prioritize_staff_management": true
  }'
```

**Response (HTTP 201 Created):**
```json
{
  "success": true,
  "data": {
    "task_id": "TASK-000001",
    "status": "PENDING",
    "location": "Puducherry",
    "keyword": "CBSE Schools",
    "max_results": 100,
    "max_pages_per_site": 20,
    "progress": 0,
    "created_at": "2026-09-12T11:20:00Z"
  }
}
```

#### 2. List Tasks (with Pagination, Filtering & Sorting)
```bash
# Basic list
curl http://localhost:8000/api/tasks

# Filter by location and status with pagination
curl "http://localhost:8000/api/tasks?location=Puducherry&status=PENDING&page=1&limit=10"

# Sort by keyword ascending
curl "http://localhost:8000/api/tasks?sort_by=keyword&sort_order=asc"
```

**Response (HTTP 200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "task_id": "TASK-000001",
      "keyword": "CBSE Schools",
      "location": "Puducherry",
      "status": "PENDING",
      "progress": 0,
      "results_count": 0,
      "verified_count": 0,
      "created_at": "2026-09-12T11:20:00Z",
      "started_at": null,
      "completed_at": null,
      "duration": null
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "total_pages": 1
  }
}
```

#### 3. Get Task Details
```bash
curl http://localhost:8000/api/tasks/TASK-000001
```

**Response (HTTP 200 OK):**
```json
{
  "success": true,
  "data": {
    "task_id": "TASK-000001",
    "status": "PENDING",
    "current_stage": "CREATING_TASK",
    "progress": 0,
    "location": "Puducherry",
    "keyword": "CBSE Schools",
    "search_radius": 25,
    "max_results": 100,
    "max_pages_per_site": 20,
    "crawl_depth": 3,
    "selected_fields": ["name", "phone", "email", "website", "address", "whatsapp", "social_links"],
    "follow_internal_links": true,
    "prioritize_contact": true,
    "prioritize_about": true,
    "prioritize_admissions": true,
    "prioritize_staff_management": true,
    "results_discovered": 0,
    "websites_found": 0,
    "websites_crawled": 0,
    "phones_found": 0,
    "emails_found": 0,
    "addresses_found": 0,
    "duplicates_removed": 0,
    "failed_websites": 0,
    "started_at": null,
    "completed_at": null,
    "created_at": "2026-09-12T11:20:00Z",
    "updated_at": "2026-09-12T11:20:00Z",
    "failure_reason": null
  }
}
```

---

### Leads REST API Endpoints (Step 11)

#### 1. Query Leads Globally
```bash
curl "http://localhost:8000/api/leads?page=1&limit=20&search=school&verification=HIGH"
```

**Query Parameters:**
- `page`: Page number (default: 1, `ge=1`)
- `limit`: Items per page (default: 20, 1–100)
- `task_id`: Scoped to a specific task ID
- `search`: Multi-field case-insensitive search across organization name, category, location, phone, email, website, contact person
- `category`: Filter by category substring
- `location`: Filter by city, state, or address
- `verification`: Filter by tier (`HIGH`, `MEDIUM`, `LOW`, `PENDING`)
- `has_phone`, `has_email`, `has_website`, `has_whatsapp`, `has_contact`, `has_social`: Boolean availability facets
- `scraped_from`, `scraped_to`: Date range ISO timestamps
- `sort_by`: `"organization"`, `"category"`, `"location"`, `"verification"`, `"scraped_date"` (default: `"scraped_date"`)
- `sort_order`: `"asc"`, `"desc"` (default: `"desc"`)

**Response (HTTP 200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "e7c653f8-80e9-4e78-b118-2e0085a6b0c1",
      "task_id": "TASK-20260312-000001",
      "organization": {
        "id": "7b09b531-15b9-4a37-b4d6-3e0e7a2b0051",
        "name": "St. Patrick Matriculation Higher Secondary School",
        "category": "Matriculation School",
        "website": "https://stpatricks.edu",
        "address": "100 Saram Road",
        "city": "Puducherry",
        "state": "Puducherry",
        "pincode": "605001"
      },
      "phone": "+91 413 2244668",
      "alternate_phone": "+91 98765 43210",
      "whatsapp": "+91 98765 43210",
      "email": "office@stpatricks.edu",
      "website": "https://stpatricks.edu",
      "location": "Puducherry, Puducherry",
      "contact_person": "Fr. John Britto",
      "designation": "Principal",
      "verification": {
        "status": "HIGH",
        "score": 88,
        "fields_found": 7,
        "total_fields": 8
      },
      "scraped_date": "2026-03-12T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

#### 2. Get Leads For a Specific Task
```bash
curl "http://localhost:8000/api/tasks/TASK-20260312-000001/leads?page=1&limit=20"
```
*Returns HTTP 404 (`TASK_NOT_FOUND`) if the task does not exist, or HTTP 200 with `data: []` and `total: 0` if the task exists but has no discovered leads.*

#### 3. Get Full Lead Profile & Provenance Audit
```bash
curl "http://localhost:8000/api/leads/e7c653f8-80e9-4e78-b118-2e0085a6b0c1"
```

**Response (HTTP 200 OK):**
```json
{
  "success": true,
  "data": {
    "id": "e7c653f8-80e9-4e78-b118-2e0085a6b0c1",
    "task_id": "TASK-20260312-000001",
    "task": {
      "task_id": "TASK-20260312-000001",
      "keyword": "CBSE Schools",
      "location": "Puducherry",
      "status": "COMPLETED",
      "created_at": "2026-03-12T10:00:00Z",
      "completed_at": "2026-03-12T10:05:00Z"
    },
    "organization": {
      "id": "7b09b531-15b9-4a37-b4d6-3e0e7a2b0051",
      "name": "St. Patrick Matriculation Higher Secondary School",
      "category": "Matriculation School",
      "website": "https://stpatricks.edu",
      "address": "100 Saram Road",
      "city": "Puducherry",
      "state": "Puducherry",
      "pincode": "605001"
    },
    "websites": [
      {
        "id": "2a1e3b5c-80e9-4e78-b118-2e0085a6b0c1",
        "url": "https://stpatricks.edu",
        "domain": "stpatricks.edu",
        "is_official": true
      }
    ],
    "phones": [
      {
        "id": "3b2c1a4d-80e9-4e78-b118-2e0085a6b0c1",
        "number": "+91 413 2244668",
        "normalized_number": "+914132244668",
        "type": "MAIN",
        "is_primary": true,
        "is_whatsapp": false
      },
      {
        "id": "4c3b2a1e-80e9-4e78-b118-2e0085a6b0c1",
        "number": "+91 98765 43210",
        "normalized_number": "+919876543210",
        "type": "WHATSAPP",
        "is_primary": false,
        "is_whatsapp": true
      }
    ],
    "emails": [
      {
        "id": "5d4c3b2a-80e9-4e78-b118-2e0085a6b0c1",
        "email": "office@stpatricks.edu",
        "normalized_email": "office@stpatricks.edu",
        "type": "GENERAL",
        "is_primary": true
      }
    ],
    "contacts": [
      {
        "id": "6e5d4c3b-80e9-4e78-b118-2e0085a6b0c1",
        "name": "Fr. John Britto",
        "designation": "Principal"
      }
    ],
    "social_links": [
      {
        "platform": "FACEBOOK",
        "url": "https://facebook.com/stpatricks",
        "is_official": true
      }
    ],
    "sources": [
      {
        "field": "phone",
        "value": "+91 413 2244668",
        "source_url": "https://stpatricks.edu/contact",
        "page_type": "CONTACT",
        "page_title": "Contact St. Patrick School"
      }
    ],
    "verification": {
      "status": "HIGH",
      "score": 88,
      "fields_found": 7,
      "total_fields": 8,
      "completeness_percentage": 87.5,
      "source_quality_score": 90.0,
      "consistency_score": 95.0,
      "reasons": { "phone": "Valid format" },
      "source_quality_details": { "domain": "official" },
      "verified_at": "2026-03-12T10:05:00Z"
    },
    "scraped_date": "2026-03-12T10:00:00Z"
  }
}
```
*Returns HTTP 404 (`LEAD_NOT_FOUND`) if the lead is not found.*

---

### Export APIs (CSV & Excel) (Step 12)

FastAPI endpoints to export processed lead data into **CSV** (with UTF-8 BOM `\ufeff` for full Excel/Windows compatibility) and **Excel (.xlsx)** (via `openpyxl` with styled headers, text-formatted phone numbers, freeze panes, and auto-filters).

#### 1. Export Task Leads
```bash
# Export all leads belonging to a specific task as CSV
curl "http://localhost:8000/api/tasks/TASK-000001/export/csv" -o task_leads.csv

# Export task leads as Excel with custom selected fields
curl "http://localhost:8000/api/tasks/TASK-000001/export/excel?fields=name,phone,email,city,website" -o task_leads.xlsx
```

#### 2. Export Global / Filtered Leads
```bash
# Export all leads globally as CSV
curl "http://localhost:8000/api/leads/export/csv" -o all_leads.csv

# Export filtered leads (by search, verification status, location) as Excel
curl "http://localhost:8000/api/leads/export/excel?location=Puducherry&verification=HIGH&search=School" -o filtered_leads.xlsx

# Export specific selected lead IDs
curl "http://localhost:8000/api/leads/export/csv?ids=uuid-1,uuid-2" -o selected_leads.csv
```

#### 3. Export Single Lead Profile
```bash
# Export single lead profile as CSV
curl "http://localhost:8000/api/leads/{lead_id}/export/csv" -o single_lead.csv

# Export single lead profile as Excel
curl "http://localhost:8000/api/leads/{lead_id}/export/excel" -o single_lead.xlsx
```

**Guardrails & Error Codes:**
- `404 NO_LEADS_TO_EXPORT`: When a task or filter query produces zero exportable leads.
- `404 TASK_NOT_FOUND`: When the specified `task_id` does not exist.
- `404 LEAD_NOT_FOUND`: When the specified `lead_id` does not exist.
- `413 EXPORT_TOO_LARGE`: When the matching dataset exceeds `MAX_EXPORT_ROWS` (default: 10,000).
- `422 INVALID_EXPORT_FIELD`: When an unrecognized field name is requested in `fields=`.
- `422 INVALID_LEAD_ID`: When an invalid UUID string is passed in `ids=`.

---

## Database Architecture & Core Entities

---

## Discovery Engine (Step 4)

The Discovery Engine accepts a scraping task (`location` + `keyword`) and discovers relevant organizations and candidate public website URLs without crawling them or extracting contact info.

### Provider Architecture
Discovery uses a pluggable multi-provider architecture managed by `DiscoveryManager`:
- **`FixtureDiscoveryProvider`**: Deterministic development provider using reserved `.example` domains.
- **`PublicSearchProvider`**: External public search engine integration (with rate limits, timeouts, and graceful offline fallback).
- **`UserURLProvider`**: High-confidence seed URLs directly provided by users.

### Execution Flow
```
ScrapingTask (Location + Keyword)
      ↓
Query Generation (build_discovery_queries)
      ↓
DiscoveryManager (Queries registered providers)
      ↓
Normalization & Deduplication (normalize_url, extract_domain, normalize_organization_name)
      ↓
Relevance Scoring & Ranking (score_candidate 0–100, is_candidate_official_website)
      ↓
Database Persistence (Organization, Website with PENDING status, task_organizations)
      ↓
Task Metrics & Logs (results_discovered, websites_found, duplicates_removed, FINDING_WEBSITES stage)
```

### Running Discovery Manually (Development CLI)

In development, trigger discovery for an existing task:

```bash
python -m app.jobs.run_discovery TASK-000001
```

**Example Output:**
```
Task: TASK-000001
Location: Puducherry
Keyword: CBSE Schools
Candidates: 6
Accepted: 5
Duplicates: 1
Websites: 5
Status: Discovery completed
```

---

## Website Crawler (Backend Step 5)

The **Website Crawler** receives organizations and candidate websites from Step 4 (Discovery Engine) and crawls publicly accessible web pages to build a provenance-tracked repository of `SourcePage` records in PostgreSQL.

### Architecture & Components

- **Two-Level Fetching Architecture**:
  - **Level 1 (`HttpCrawler`)**: High-performance HTTPX client with streaming guards, content-type verification (`text/html`), response size limits (`MAX_RESPONSE_SIZE_MB`), redirect limits, and connection retries.
  - **Level 2 (`PlaywrightCrawler`)**: Automated headless Chromium fallback triggered strictly when client-side JavaScript SPA shells or minimal unhydrated DOMs are detected (`is_js_shell`). Gracefully degrades to Level 1 if browser binaries are not installed.
- **`RobotsChecker`**: In-memory cached robots parser (`urllib.robotparser.RobotFileParser`) with timeouts and permissive fallbacks.
- **`PageClassifier`**: Rule-based heuristic classifier identifying `HOME`, `CONTACT`, `ABOUT`, `ADMISSIONS`, `MANAGEMENT`, `PRINCIPAL`, `FACULTY`, `STAFF`, `BRANCH`, `LOCATION`, `INFRASTRUCTURE`, and `OTHER`.
- **`UrlFrontier`**: Priority queue ordering crawl targets based on task preferences (`prioritize_contact`, `prioritize_about`, `prioritize_admissions`, `prioritize_staff_management`), while enforcing `crawl_depth` and `max_pages_per_site`.
- **`LinkExtractor`**: BeautifulSoup-based parser resolving relative URLs, stripping fragments, excluding assets/social platforms, and locking crawler execution within target domain boundaries.
- **`CrawlerService`**: Orchestrator executing task-wide crawling with **strict per-website failure isolation** (one failing site does not fail peers or abort the task), upserting `SourcePage` records, and advancing task stage to `EXTRACTING`.

### Running the Crawler Manually (Development CLI)

Trigger website crawling for an existing task:

```bash
python -m app.jobs.run_crawl TASK-000001
```

**Example Output:**
```
Task: TASK-000001
Websites: 2
Crawled: 2
Failed: 0
Blocked: 0
Pages: 12
Playwright: 0
Status: Crawling completed
Next Stage: EXTRACTING
```

---

## Data Extraction Engine (Backend Step 6)

The **Data Extraction Engine** processes crawled `SourcePage` records, parses HTML into a reusable DOM representation (`ParsedPage`), extracts structured business entities (phones, emails, addresses, contacts, social links, organization metadata), creates strict provenance audit trails (`ExtractedField`), persists records in PostgreSQL, and advances the task stage to `CLEANING`.

### Architecture & Modular Extractors

- **`ParsedPage`**: Caches precomputed visible text, stripped strings, and tag collections using BeautifulSoup (`lxml` / `html.parser`) to eliminate redundant parsing.
- **`PhoneExtractor`**: Extracts phones from `tel:` links, WhatsApp URLs (`wa.me`, `api.whatsapp.com`), and visible text; normalizes via `phonenumbers` to E.164; classifies types (`MAIN`, `OFFICE`, `ADMISSIONS`, `LANDLINE`, `WHATSAPP`, `ALTERNATE`).
- **`EmailExtractor`**: Extracts from `mailto:` links, visible text, and de-obfuscated forms (`info [at] school [dot] com`); filters out asset extensions (`.png`, `.css`, `.js`) and placeholder domains; categorizes into `GENERAL`, `CONTACT`, `ADMISSIONS`, `MANAGEMENT`.
- **`AddressExtractor`**: Parses `<address>` tags, contact block sections, and JSON-LD `PostalAddress` into full address, city, state, and 6-digit Indian pincodes.
- **`ContactExtractor`**: Extracts leadership and contact persons (Principals, Directors, Heads, Admissions Coordinators) paired with designations from staff cards, schema.org data, and heading patterns.
- **`SocialExtractor`**: Identifies official social profiles on Facebook, Instagram, LinkedIn, YouTube, Twitter/X; strips share buttons; normalizes URLs with `is_official=True`.
- **`OrganizationExtractor` & `WebsiteExtractor`**: Extracts canonical signals from JSON-LD Schema.org types (`EducationalOrganization`, `School`, `LocalBusiness`), OpenGraph tags, and canonical tags without overwriting strong discovery records.
- **`ExtractionService`**: Task-level orchestrator storing `PhoneNumber`, `EmailAddress`, `Contact`, `SocialLink`, `ExtractedField` provenance rows, updating task counters (`phones_found`, `emails_found`, `addresses_found`), and advancing task stage to `CLEANING`.

### Running Data Extraction Manually (Development CLI)

Trigger data extraction for an existing task:

```bash
python -m app.jobs.run_extraction TASK-000001
```

**Example Output:**
```
Task: TASK-000001
Pages Processed: 12
Phones Extracted: 6
Emails Extracted: 4
Addresses Extracted: 2
Contacts Extracted: 3
Social Links Extracted: 4
Status: Extraction completed
Next Stage: CLEANING
```

---

## Data Cleaning & Deduplication Pipeline (Step 7)

The Cleaning & Deduplication Engine sanitizes extracted data, eliminates garbage placeholders, resolves child duplicates, and detects & safely merges duplicate organizations while guaranteeing branch safety and zero provenance loss.

### Pipeline Architecture

```
Raw Extracted Data
       ↓
Field Cleaning & Validation (text, E.164 phone, email syntax, URL tracking, pincode)
       ↓
Exact Child Duplicate Removal (phones, emails, websites, social links, source pages)
       ↓
Organization Duplicate Matching (weighted scoring: domain 50, phone 25, name 20, address 15, email 15, city 5)
       ↓
Branch Safety Verification (different confirmed cities/locations without common domain/phone NEVER merge)
       ↓
Safe Canonical Merging (child entity re-parenting, provenance retention, OrganizationMergeEvent audit)
       ↓
Lead Deduplication & Task Metric Update
       ↓
Next Stage: VERIFYING (progress 85%, status RUNNING)
```

### Running the Cleaning CLI
```bash
python -m app.jobs.run_cleaning TASK-000001
```

**Example Output:**
```
Task: TASK-000001
Organizations Processed: 15
Organizations Merged: 3
Exact Duplicates Removed: 8
Phones Cleaned: 18
Emails Cleaned: 12
Addresses Cleaned: 14
Invalid Phones Removed: 2
Invalid Emails Removed: 1
Potential Duplicates Flagged: 1
Total Duplicates Removed: 14
Status: Cleaning completed
Next Stage: VERIFYING
```

---

## Lead Data-Quality Verification & Confidence Scoring Engine (Step 8)

The Verification Engine assesses the data quality, completeness, provenance, and consistency of discovered leads without relying on intrusive or legally risky external identity checks.

### Three-Pillar Deterministic Confidence Scoring (0–100)

$$\text{Confidence Score} = (\text{Completeness} \times 50\%) + (\text{Source Quality} \times 30\%) + (\text{Consistency} \times 20\%)$$

1. **Field Completeness (50%)**:
   - Evaluated strictly against the user's `task.selected_fields`.
   - Unrequested fields are never penalized (e.g. if the user only requests Phone and Email, 100% is achievable with those two fields).
   - Weights normalized dynamically across requested fields.
   - Ignores placeholder values (`N/A`, `null`, `dummy`, `undefined`).

2. **Source Quality & Provenance (30%)**:
   - Scores data provenance using `ExtractedField` and `SourcePage` records:
     - Official Website Contact / About / Staff pages: `95–100`
     - Official Website Home page: `80`
     - Public Business Directories (e.g. JustDial, YellowPages): `60`
     - Inferred / Fallback with limited metadata: `45–75`

3. **Cross-Field Consistency (20%)**:
   - Cross-checks website domains against email address domains (`EMAIL_DOMAIN_MATCH`: 100).
   - Validates generic email providers (`@gmail.com`, `@yahoo.com`) as `WEAK_CONSISTENCY_SIGNAL` (75) rather than hard failures.
   - Validates E.164 phone formats (`+91...`).
   - Detects and flags `POSSIBLE_CONFLICT` for conflicting phone numbers without deleting data.

### Confidence Tiers

| Tier | Score Range | Description |
|---|---|---|
| `HIGH` | 80 – 100 | Strong completeness, sourced from official high-value pages, verified domain consistency. |
| `MEDIUM` | 60 – 79 | Moderate completeness or sourced from public business directories with valid syntax. |
| `LOW` | 0 – 59 | Minimal field presence, unverified sources, or multiple unresolved data conflicts. |

### Development CLI Runner

```bash
# Run verification on a task
python -m app.jobs.run_verification TASK-000001
```

Sample CLI output:
```
Task: TASK-000001
Leads Processed: 12
High Confidence Leads: 8
Medium Confidence Leads: 3
Low Confidence Leads: 1
Pending Leads: 0
Average Completeness: 87.5%
Average Source Quality: 84.2
Average Consistency: 91.0
Duration: 0.45s
Status: Verification completed
Next Stage: SAVING
```

---

## Redis, Celery & Background Pipeline Orchestration (Backend Step 9)

Converts the scraping pipeline from manual sequential execution into a resilient, decoupled background worker system orchestrated via **Celery** with **Redis** as the message broker and result backend.

### Architecture & Queue Routing

The pipeline decouples synchronous client requests (`POST /api/scrape`) from heavy multi-stage scraping:
1. `POST /api/scrape` persists the task with status `PENDING`, progress `0%`, and enqueues the Celery pipeline chain.
2. The endpoint immediately responds with **HTTP 201 Created** containing `queued: true` and `task_id`.
3. Celery workers execute the pipeline sequentially across dedicated logical queues:

```
POST /api/scrape
       │
       ▼
   PostgreSQL (status: PENDING, progress: 0)
       │
       ▼
   Redis Queue (celery_app)
       │
       ▼
Celery Worker Chain (immutable signatures: .si(task_id)):
 1. run_discovery_task    (queue: discovery)    ──> FINDING_WEBSITES (10%)
 2. run_crawl_task        (queue: crawl)        ──> CRAWLING (35%)
 3. run_extraction_task   (queue: extraction)   ──> EXTRACTING (65%)
 4. run_cleaning_task     (queue: cleaning)     ──> CLEANING (80%)
 5. run_verification_task (queue: verification) ──> VERIFYING (90%)
 6. run_finalize_task     (queue: pipeline)     ──> COMPLETED (100%)
```

### Key Technical Capabilities

- **Dedicated Logical Queues**: Tasks route to specific queues (`discovery`, `crawl`, `extraction`, `cleaning`, `verification`, `pipeline`) allowing fine-grained worker scaling.
- **Sync/Async Execution Bridge (`task_context.py`)**: Celery workers run synchronously while domain services use async SQLAlchemy (`AsyncSession`). The worker context executes coroutines safely with event loop isolation and manages independent DB sessions per task execution without leaks.
- **Transient Retry Handling**: Automatic retries with exponential backoff on transient network/database errors (`OperationalError`, `ConnectionError`, `RedisError`) up to `CELERY_MAX_RETRIES`.
- **Stage-Level Failure Isolation**: Permanent stage errors mark the task `FAILED`, populate `failure_reason`, record a `PIPELINE_STAGE_FAILED` event in `scraping_logs`, and immediately halt downstream stages in the Celery chain.
- **Cancellation Safety**: Tasks marked `CANCELLED` are detected prior to stage execution, halting further pipeline work gracefully without database corruption.
- **Finalization Stage (`FinalizationService`)**: Reconciles discovered metrics across entities, sets `status="COMPLETED"`, `current_stage="COMPLETED"`, `progress=100`, and records `completed_at`.

### Running Workers & Pipelines in Development

```bash
# 1. Start Redis
docker compose up redis -d

# 2. Start Celery Worker (listens on all queues)
celery -A app.workers.celery_app worker --loglevel=INFO --concurrency=4

# 3. Trigger full pipeline via CLI runner
python -m app.jobs.run_pipeline TASK-000001

# Run eagerly in-process (synchronous test mode without Celery worker)
python -m app.jobs.run_pipeline TASK-000001 --eager
```

---

## Real-Time Task Progress & WebSocket Updates (Backend Step 10)

Provides live progress streaming, stage change events, activity milestones, and failure/completion notifications via **FastAPI WebSockets** and **Redis Pub/Sub**, eliminating frontend polling.

### Architecture

```
Frontend (Next.js / Client)
       ↕  WS /api/ws/tasks/{task_id}
FastAPI (ConnectionManager + TaskSubscriber)
       ▲
       │  Redis Pub/Sub (channel: leadscout:task:{task_id})
       │
Celery Worker (TaskProgressService / Stage Tasks)
       │
       ▼  (Commit first, then publish)
PostgreSQL (Authoritative State)
```

### Endpoints

| Protocol | Endpoint | Description |
|---|---|---|
| `WS` | `/api/ws/tasks/{task_id}` | Task-specific real-time progress WebSocket. |
| `WS` | `/ws/tasks/{task_id}` | Direct path alias for frontend convenience. |

### Event Protocol (JSON)

Every event is serialized as JSON matching the standard envelope:
```json
{
  "type": "<event_type>",
  "task_id": "TASK-000124",
  "timestamp": "2026-09-12T15:30:00Z",
  "data": { ... }
}
```

#### Supported Event Types

| Event Type | Description | Sample Data Payload |
|---|---|---|
| `task.snapshot` | Immediate state snapshot on connect or reconnect (sourced from PostgreSQL). | `{"status": "RUNNING", "current_stage": "CRAWLING", "progress": 42, "websites_crawled": 31, ...}` |
| `task.queued` | Emitted when task is accepted and recorded in PENDING state. | `{"status": "PENDING", "current_stage": "CREATING_TASK", "progress": 0}` |
| `task.started` | Emitted when a background worker begins executing the first pipeline stage. | `{"status": "RUNNING", "current_stage": "DISCOVERING", "progress": 10}` |
| `task.progress` | Monotonic progress and metric updates. | `{"status": "RUNNING", "current_stage": "CRAWLING", "progress": 45, "websites_crawled": 12, ...}` |
| `task.stage_changed` | Emitted when transitioning between pipeline stages. | `{"status": "RUNNING", "current_stage": "EXTRACTING", "progress": 50}` |
| `task.activity` | Concise milestone messages or non-fatal crawl alerts. | `{"message": "Website xyz.com failed: HTTP 403", "stage": "CRAWLING"}` |
| `task.completed` | Emitted upon pipeline completion with 100% progress and reconciled metrics. | `{"status": "COMPLETED", "current_stage": "COMPLETED", "progress": 100, "verified_count": 8}` |
| `task.failed` | Emitted when a fatal error halts the pipeline (sanitized, no stack traces). | `{"status": "FAILED", "stage": "EXTRACTING", "reason": "Data extraction failed: ..."}` |
| `task.cancelled` | Emitted when a task is cancelled, preserving last valid progress. | `{"status": "CANCELLED", "current_stage": "CRAWLING", "progress": 67}` |
| `task.error` | Error or rate limit rejection during connection handshake. | `{"code": "TASK_NOT_FOUND", "message": "Scraping task '...' not found."}` |
| `ping` / `pong` | Server-initiated heartbeat ping every 30s (`{"type": "ping"}`) and client `{"type": "pong"}`. | `{}` |

### Key Resilience Guarantees

1. **PostgreSQL Authoritative State**: WebSocket messages are real-time notifications. Initial snapshots and reconnects query PostgreSQL directly.
2. **Monotonic Progress Guarantee**: Normal pipeline updates enforce $0 \le \text{progress} \le 100$ and reject regressive updates.
3. **Failure Isolation**: Redis Pub/Sub outages or client disconnects NEVER fail or abort scraping tasks.
4. **Per-Task Channel Isolation**: Connections are isolated per `task_id`; clients on Task A never receive events for Task B.
5. **Rate Limiting**: Configured with `MAX_WS_CONNECTIONS_PER_TASK=5` to prevent connection exhaustion.

---

## Database Architecture & Core Entities

```
User
  ↓ (1:N)
ScrapingTask (with celery_task_id)
  ├── ScrapingLog (1:N)
  └── Lead (1:N) ──→ Organization (M:N via task_organizations)
                        ├── Website (1:N)
                        │     └── SourcePage (1:N)
                        │           └── ExtractedField (1:N)
                        ├── Contact (1:N)
                        │     ├── PhoneNumber (1:N)
                        │     └── EmailAddress (1:N)
                        ├── SocialLink (1:N)
                        ├── OrganizationMergeEvent (1:N)
                        └── LeadVerification (1:N per task/org)
```

---

## Running Tests

```bash
pytest
```

The test suite runs with **187 automated tests (100% pass rate)**:
- 3 Configuration and environment tests (`tests/test_config.py`)
- 4 Health endpoint and envelope tests (`tests/test_health.py`)
- 10 Database model, constraint, and relationship tests (`tests/test_models.py`)
- 18 Scraping Task API integration, validation, pagination, filtering, sorting, concurrency, and lifecycle tests (`tests/test_tasks_api.py`)
- 20 Leads REST API, filtering, case-insensitive search, data availability facets, sorting, provenance, and N+1 prevention tests (`tests/test_leads_api.py`)
- 22 Export APIs tests covering CSV UTF-8 BOM, Excel openpyxl formatting, phone text formatting, freeze panes, field selection, aliases, 404/413/422 guardrails, and filename sanitization (`tests/test_export.py`)
- 10 Discovery Engine query, normalization, fixture, provider resilience, ranking, persistence, idempotency, and status tests (`tests/test_discovery.py`)
- 16 Website Crawler link extraction, domain boundary, page classification, frontier priority, robots.txt, HTTP guards, Playwright fallback, failure isolation, DB persistence, idempotency, and CLI runner tests (`tests/test_crawler.py`)
- 11 Data Extraction Engine phone validation, WhatsApp detection, email de-obfuscation, address/pincode, contact leadership, social links, JSON-LD, provenance tracking, DB persistence, idempotency, and CLI runner tests (`tests/test_extraction.py`)
- 22 Data Cleaning & Deduplication tests covering text cleaners, E.164 phone normalization, email de-obfuscation and filtering, URL & social tracking parameter removal, 6-digit pincode validation, organization legal suffix normalization, exact child deduplication, multi-signal weighted duplicate matching, branch safety protection, safe canonical merging with child re-parenting, full task workflow, idempotency, cross-task organization preservation, and CLI runner execution (`tests/test_cleaning.py`)
- 18 Lead Data-Quality Verification & Confidence Scoring tests covering field completeness against selected fields, placeholder filtering, source quality assessment, directory scoring, domain consistency checking, generic email detection, conflict flagging without data loss, deterministic 0–100 scoring, tier boundary mapping (HIGH/MEDIUM/LOW), end-to-end task workflow, multi-task score isolation, idempotency, individual lead failure isolation, and CLI runner execution (`tests/test_verification.py`)
- 12 Celery Background Workers, Queues & Pipeline Orchestration tests covering configuration settings, queue routing rules, registered task discovery, sync/async session bridge, full eager chain execution, stage failure halting, transient retries, cancellation safety, FastAPI queue integration, Redis 503 error handling, and CLI runner execution (`tests/test_workers.py`)
- 21 Real-Time WebSocket & Progress tests covering connection lifecycle, initial PostgreSQL snapshot, invalid task rejection, per-task connection limits, progress/stage/activity/completion/failure/cancellation events, disconnect safety, multi-client broadcast, multi-task channel isolation, reconnect snapshot recovery, monotonic progress validation, terminal state protection, Redis publish failure isolation, DB failure rollback safety, heartbeat ping/pong, dead socket pruning, and subscriber lifecycle (`tests/test_websocket.py`)

---

## Local Development (FastAPI + Celery)

```bash
# 1. Start the API server
uvicorn app.main:app --reload

# 2. Start Celery worker in a separate terminal
celery -A app.workers.celery_app worker --loglevel=INFO --concurrency=4

# Endpoints:
#   http://localhost:8000/api/health
#   http://localhost:8000/docs
#   ws://localhost:8000/api/ws/tasks/{task_id}
```

---

## Docker Setup

```bash
# From the backend/ directory:
docker compose up --build

# Services:
#   FastAPI API:  http://localhost:8000
#   PostgreSQL:   localhost:5432
#   Redis:        localhost:6379
#   Celery:       Background worker consuming pipeline queues
```
