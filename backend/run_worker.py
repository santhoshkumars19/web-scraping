"""
backend/run_worker.py

Celery worker startup runner with explicit queue registration.
Subscribes to all 6 LeadScout pipeline queues.
"""

import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.workers.celery_app import celery_app

if __name__ == "__main__":
    queues = "pipeline,discovery,crawl,extraction,cleaning,verification"
    argv = [
        "worker",
        f"-Q={queues}",
        "--loglevel=INFO",
        "--pool=solo",
    ]
    celery_app.worker_main(argv)
