"""
run_worker.py

Root Celery worker startup runner for Railway / container deployments.
"""

import os
import sys

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if os.path.isdir(backend_dir) and backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.workers.celery_app import celery_app

if __name__ == "__main__":
    queues = "pipeline,discovery,crawl,extraction,cleaning,verification"
    argv = [
        "worker",
        "-Q",
        queues,
        "--loglevel=INFO",
        "--pool=solo",
    ]
    celery_app.worker_main(argv)
