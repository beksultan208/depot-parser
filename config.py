# ─────────────────────────────────────────────
# config.py  –  Home Depot Parser Configuration
# All secrets are read from environment variables.
# For local development copy config.example.py to
# config.py and set the values there instead.
# ─────────────────────────────────────────────
import os

# ── SerpApi ──────────────────────────────────
SERPAPI_KEY = os.environ["SERPAPI_KEY"]

# ── PostgreSQL ────────────────────────────────
# Railway injects DATABASE_URL automatically when a Postgres plugin is attached.
# Format: postgresql://user:password@host:port/dbname
DATABASE_URL = os.environ["DATABASE_URL"]

# ── Crawl settings ────────────────────────────
MAX_PAGES = int(os.environ.get("MAX_PAGES", 2))
REQUEST_DELAY = float(os.environ.get("REQUEST_DELAY", 1.5))

# ── Search queries ────────────────────────────
SEARCH_QUERIES = [
    "lumber",
    "power tools",
    "concrete",
    "drywall",
    "insulation",
    "plumbing",
    "roofing",
]
