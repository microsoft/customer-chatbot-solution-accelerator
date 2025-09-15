import pyodbc
from contextlib import contextmanager
from ..config import settings
from decimal import Decimal


@contextmanager
def get_conn():
    conn = pyodbc.connect(settings.sql_conn_str)
    try:
        yield conn
    finally:
        conn.close()

def _normalize(row: dict) -> dict:
    if "id" in row: row["id"] = int(row["id"])
    if "inventory" in row and row["inventory"] is not None:
        row["inventory"] = int(row["inventory"])
    if "price" in row and row["price"] is not None:
        # pyodbc returns Decimal for SQL DECIMAL/NUMERIC
        row["price"] = float(row["price"]) if isinstance(row["price"], Decimal) else row["price"]
    return row

def fetch_products(limit: int = 50):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT TOP (?) id, sku, name, description, price, image_url, inventory FROM dbo.products ORDER BY name", limit)
        cols = [c[0] for c in cur.description]
        return [_normalize(dict(zip(cols, row))) for row in cur.fetchall()]

def find_product_by_sku(sku: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, sku, name, description, price, image_url, inventory FROM dbo.products WHERE sku=?", sku)
        row = cur.fetchone()
        if not row:
            return None
        cols = [c[0] for c in cur.description]
        return _normalize(dict(zip(cols, row)))

def search_products(query: str, limit: int = 10):
    q = f"%{query}%"
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            '''
            SELECT TOP (?) id, sku, name, description, price, image_url, inventory
            FROM dbo.products
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY name
            ''',
            limit, q, q
        )
        cols = [c[0] for c in cur.description]
        return [_normalize(dict(zip(cols, row))) for row in cur.fetchall()]
