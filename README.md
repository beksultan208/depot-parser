# Home Depot Product Parser

Scrapes construction and building materials from homedepot.com via [SerpApi](https://serpapi.com) and saves them to a local PostgreSQL database or JSON file.

## How It Works

Two-step pipeline per product:

1. **Search** — `engine: home_depot` queries (e.g. "lumber", "drywall") return paginated product ID lists
2. **Detail** — `engine: home_depot_product` fetches full data for each ID: title, price, description, brand, model number, specifications

## Project Structure

```
homedepot_parser/
├── config.example.py   # Config template — copy to config.py and fill in values
├── parser.py           # Entry point + pipeline logic
├── db.py               # PostgreSQL helpers (DDL, upsert)
├── requirements.txt
├── output/             # test_results.json written here (test mode)
└── logs/               # parser.log written here
```

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Configure**
```bash
cp config.example.py config.py
```
Edit `config.py` and set:
- `SERPAPI_KEY` — get one at [serpapi.com](https://serpapi.com)
- `DB_*` — your PostgreSQL credentials (only needed for `--mode db`)

**3. Create the database** *(only for DB mode)*
```sql
CREATE DATABASE homedepot;
```
The `products` table is created automatically on first run.

## Usage

```bash
# Test mode — no database required, saves to output/test_results.json
python parser.py --mode test

# Production mode — saves to PostgreSQL
python parser.py --mode db

# Parse a single category
python parser.py --mode db --query "lumber"
```

## Database Schema

```sql
CREATE TABLE products (
    id           SERIAL PRIMARY KEY,
    product_id   VARCHAR(64) UNIQUE NOT NULL,
    title        TEXT,
    price        NUMERIC(12, 2),
    description  TEXT,
    brand        VARCHAR(255),
    model_number VARCHAR(255),
    category     VARCHAR(255),
    raw_json     JSONB,
    created_at   TIMESTAMP DEFAULT NOW()
);
```

## Configuration Options

| Setting | Default | Description |
|---|---|---|
| `SERPAPI_KEY` | — | Your SerpApi API key |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_NAME` | `homedepot` | Database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | — | Database password |
| `MAX_PAGES` | `2` | Pages per query (24 products/page) |
| `REQUEST_DELAY` | `1.5` | Seconds between API calls |
| `SEARCH_QUERIES` | 7 categories | List of search terms to parse |

Default search queries: `lumber`, `power tools`, `concrete`, `drywall`, `insulation`, `plumbing`, `roofing`

## Output

**Test mode** — `output/test_results.json`:
```json
[
  {
    "product_id": "123456",
    "title": "2 in. x 4 in. x 8 ft. Lumber",
    "price": 5.48,
    "description": "...",
    "brand": "...",
    "model_number": "...",
    "category": "lumber"
  }
]
```

**Logs** — `logs/parser.log` (also printed to console):
```
2026-04-16 10:00:00  INFO     Home Depot Parser  |  mode=test  |  queries=['lumber']
2026-04-16 10:00:01  INFO     Found 24 product IDs on page 1.
...
2026-04-16 10:01:20  INFO     SUMMARY  total_found=48   saved=47   skipped=1
```

## Requirements

- Python 3.10+
- SerpApi account with `home_depot` engine access
- PostgreSQL (only for `--mode db`)
