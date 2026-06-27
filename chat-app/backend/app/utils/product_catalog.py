import csv
from functools import lru_cache
from typing import Any

try:
    from ..scenario_config import SCENARIOS_DIR, current_scenario
except ImportError:
    from app.scenario_config import SCENARIOS_DIR, current_scenario


@lru_cache(maxsize=1)
def ecommerce_catalog_by_title() -> dict[str, dict[str, Any]]:
    if current_scenario() != "ecommerce":
        return {}

    path = SCENARIOS_DIR / "ecommerce" / "data" / "catalog.csv"
    if not path.is_file():
        return {}

    by_title: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            title = (row.get("title") or "").strip()
            if not title:
                continue
            key = title.lower()
            try:
                price = float(row.get("price") or 0)
            except (TypeError, ValueError):
                price = 0.0
            by_title[key] = {
                "id": (row.get("productId") or key).strip(),
                "title": title,
                "price": price,
                "image": (row.get("image") or "").strip(),
                "category": (row.get("category") or "Paint Shades").strip(),
                "description": (row.get("description") or "").strip(),
            }
    return by_title


def enrich_product(product: dict[str, Any]) -> dict[str, Any]:
    catalog = ecommerce_catalog_by_title()
    title = str(product.get("title") or "").strip()
    if not title:
        return product

    match = catalog.get(title.lower())
    if not match:
        return product

    enriched = dict(product)
    if not enriched.get("image"):
        enriched["image"] = match.get("image", "")
    if not enriched.get("description"):
        enriched["description"] = match.get("description", "")
    if not enriched.get("category"):
        enriched["category"] = match.get("category", "Paint Shades")
    if not enriched.get("id") or str(enriched["id"]).startswith("product-"):
        enriched["id"] = match.get("id") or enriched.get("id")
    try:
        price = float(enriched.get("price") or 0)
    except (TypeError, ValueError):
        price = 0.0
    if price <= 0 and match.get("price"):
        enriched["price"] = match["price"]
    return enriched
