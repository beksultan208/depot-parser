# ─────────────────────────────────────────────
# db.py  –  PostgreSQL helpers
# ─────────────────────────────────────────────
import json
import logging

import psycopg2
from psycopg2.extras import Json

import config

logger = logging.getLogger(__name__)

# ── DDL ───────────────────────────────────────
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id           SERIAL PRIMARY KEY,
    product_id   VARCHAR(64)  UNIQUE NOT NULL,
    title        TEXT,
    price        NUMERIC(12, 2),
    description  TEXT,
    brand        VARCHAR(255),
    model_number VARCHAR(255),
    category     VARCHAR(255),
    raw_json     JSONB,
    created_at   TIMESTAMP DEFAULT NOW()
);
"""

UPSERT_SQL = """
INSERT INTO products
    (product_id, title, price, description, brand, model_number, category, raw_json)
VALUES
    (%(product_id)s, %(title)s, %(price)s, %(description)s,
     %(brand)s, %(model_number)s, %(category)s, %(raw_json)s)
ON CONFLICT (product_id) DO NOTHING
RETURNING id;
"""


def get_connection():
    """Open and return a psycopg2 connection using config settings."""
    return psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )


def init_db(conn):
    """Create the products table if it does not exist."""
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    logger.info("Database initialised (table ready).")


def save_product(conn, product: dict) -> bool:
    """
    Insert a product row.

    Returns True if a new row was inserted, False if it was a duplicate.
    """
    params = {
        "product_id":   product.get("product_id"),
        "title":        product.get("title"),
        "price":        product.get("price"),
        "description":  product.get("description"),
        "brand":        product.get("brand"),
        "model_number": product.get("model_number"),
        "category":     product.get("category"),
        "raw_json":     Json(product.get("raw_json", {})),
    }
    with conn.cursor() as cur:
        cur.execute(UPSERT_SQL, params)
        inserted = cur.rowcount > 0
    conn.commit()
    return inserted
