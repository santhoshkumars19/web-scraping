import os
import sys

# Ensure backend root is in sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if os.path.isdir(backend_dir):
    sys.path.insert(0, backend_dir)

import uvicorn

if __name__ == "__main__":
    raw_port = os.getenv("PORT", "8000")
    port = int(raw_port) if raw_port.isdigit() else 8000
    print(f"Starting LeadScout API on 0.0.0.0:{port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
