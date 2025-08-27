# Thin, backward-compatible entrypoint for uvicorn:
#   uvicorn app.main:app --reload --port 8000
from .api.server import app