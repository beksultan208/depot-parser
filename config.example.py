# ─────────────────────────────────────────────
# config.example.py  –  Home Depot Parser Configuration Template
#
# For LOCAL development:
#   cp config.example.py config.py
#   then fill in your real values below.
#   config.py is git-ignored and will never be committed.
#
# For RAILWAY (production):
#   Do NOT use this file. Set environment variables in the
#   Railway dashboard instead (see README for the full list).
# ─────────────────────────────────────────────
import os

# ── SerpApi ──────────────────────────────────
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "your_serpapi_key_here")

# ── PostgreSQL ────────────────────────────────
# Use a full connection string:
#   postgresql://user:password@host:port/dbname
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:your_password@localhost:5432/homedepot",
)

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
