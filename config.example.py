# ─────────────────────────────────────────────
# config.example.py  –  Home Depot Parser Configuration Template
#
# Copy this file to config.py and fill in your real values.
#   cp config.example.py config.py
# config.py is git-ignored and will never be committed.
# ─────────────────────────────────────────────

# ── SerpApi ──────────────────────────────────
SERPAPI_KEY = "your_serpapi_key_here"

# ── PostgreSQL ────────────────────────────────
DB_HOST     = "localhost"
DB_PORT     = 5432
DB_NAME     = "homedepot"
DB_USER     = "postgres"
DB_PASSWORD = "your_db_password_here"

# ── Crawl settings ────────────────────────────
MAX_PAGES = 2          # pages per query  (24 products / page)
REQUEST_DELAY = 1.5    # seconds between API calls

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
