"""
app/api/routes/__init__.py

Centralised API router.

All feature routers are registered here and then included in main.py.
Prefix and tags are attached at registration time so individual router
files remain free of path hard-coding.
"""

from fastapi import APIRouter

from app.api.routes import auth, dashboard, exports, health, leads, tasks, users

# ── Root API router ─────────────────────────────────────────────────────────
# All routes registered here will be mounted under settings.API_PREFIX ("/api")
# by main.py.

api_router = APIRouter()

# ── Authentication & User routes ─────────────────────────────────────────────
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(users.router, tags=["Users"])

# ── System / infra routes ────────────────────────────────────────────────────
api_router.include_router(health.router, tags=["Health"])

# ── Dashboard routes ─────────────────────────────────────────────────────────
api_router.include_router(dashboard.router, tags=["Dashboard"])

# ── Task & Scraping routes ───────────────────────────────────────────────────
api_router.include_router(tasks.router, tags=["Tasks"])

# ── Export routes (must be mounted before leads to avoid {lead_id} conflicts) ─
api_router.include_router(exports.router, tags=["Exports"])

# ── Leads routes ─────────────────────────────────────────────────────────────
api_router.include_router(leads.router, tags=["Leads"])
