import pyodbc
from contextlib import contextmanager
from ..config import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

@contextmanager
def get_conn():
    """Get SQL database connection"""
    if not settings.sql_conn_str:
        logger.warning("SQL connection string not configured")
        yield None
        return
    
    conn = pyodbc.connect(settings.sql_conn_str)
    try:
        yield conn
    finally:
        conn.close()

def _normalize(row: dict) -> dict:
    """Normalize database row data"""
    if "id" in row: 
        row["id"] = int(row["id"])
    if "inventory" in row and row["inventory"] is not None:
        row["inventory"] = int(row["inventory"])
    if "price" in row and row["price"] is not None:
        # pyodbc returns Decimal for SQL DECIMAL/NUMERIC
        row["price"] = float(row["price"]) if isinstance(row["price"], Decimal) else row["price"]
    return row

def fetch_products(limit: int = 50):
    """Fetch products from SQL database"""
    if not settings.sql_conn_str:
        logger.warning("SQL not configured, returning empty list")
        return []
    
    with get_conn() as conn:
        if not conn:
            return []
        cur = conn.cursor()
        cur.execute("SELECT TOP (?) id, sku, name, description, price, image_url, inventory FROM dbo.products ORDER BY name", limit)
        cols = [c[0] for c in cur.description]
        return [_normalize(dict(zip(cols, row))) for row in cur.fetchall()]

def find_product_by_sku(sku: str):
    """Find product by SKU"""
    if not settings.sql_conn_str:
        logger.warning("SQL not configured, returning None")
        return None
    
    with get_conn() as conn:
        if not conn:
            return None
        cur = conn.cursor()
        cur.execute("SELECT id, sku, name, description, price, image_url, inventory FROM dbo.products WHERE sku=?", sku)
        row = cur.fetchone()
        if not row:
            return None
        cols = [c[0] for c in cur.description]
        return _normalize(dict(zip(cols, row)))

def search_products(query: str, limit: int = 10):
    """Search products by query"""
    if not settings.sql_conn_str:
        logger.warning("SQL not configured, returning empty list")
        return []
    
    words = [w.strip() for w in query.split() if w.strip()]
    if not words:
        return []
    
    like_clauses = []
    params = [limit]
    for w in words:
        like_clauses.append("name LIKE ?")
        like_clauses.append("description LIKE ?")
        params.append(f"%{w}%")
        params.append(f"%{w}%")
    
    where_sql = " OR ".join(like_clauses)
    sql = f'''
        SELECT TOP (?) id, sku, name, description, price, image_url, inventory
        FROM dbo.products
        WHERE {where_sql}
        ORDER BY name
    '''
    
    with get_conn() as conn:
        if not conn:
            return []
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description]
        return [_normalize(dict(zip(cols, row))) for row in cur.fetchall()]









