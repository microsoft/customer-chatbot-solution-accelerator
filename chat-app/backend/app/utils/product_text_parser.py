import re
from typing import Any

try:
    from .product_catalog import enrich_product
    from ..scenario_config import current_scenario
except ImportError:
    from app.utils.product_catalog import enrich_product
    from app.scenario_config import current_scenario


def detect_content_type(text: str) -> str:
    if not text:
        return "text"

    has_order_number = "**Order Number:**" in text or "Order Number:" in text
    has_order_keywords = any(
        phrase in text for phrase in ("recent orders", "past orders", "your orders")
    )
    has_order_structure = any(
        marker in text for marker in ("**Status:**", "**Items:**", "**Subtotal:**")
    )
    if has_order_number or (has_order_keywords and has_order_structure):
        return "orders"

    if re.search(r"\d+\.\s*\*\*[^*]+\*\*.*!\[", text, re.DOTALL):
        return "products"
    if "**Price:**" in text and re.search(r"!\[[^\]]+\]\([^)]+\)", text):
        return "products"
    if re.search(r"\d+\.\s*\*\*[^*]+\*\*[\s\S]*?\*\*Price:\*\*", text):
        return "products"
    if "**Price:**" in text and "**Rating:**" in text:
        return "products"
    if re.search(r"!\[[^\]]+\]\([^)]+\)", text) and re.search(
        r"\w+\s+is\s+(?:described\s+as|a\s+)", text, re.IGNORECASE
    ):
        return "products"

    return "text"


def _slug_id(title: str) -> str:
    return f"product-{title.lower().replace(' ', '-')}"


def _parse_price(value: str | None) -> float:
    if not value:
        return 0.0
    match = re.search(r"\$?([0-9,]+\.?\d*)", value)
    if not match:
        return 0.0
    return float(match.group(1).replace(",", ""))


def _parse_product_section(section: str) -> dict[str, Any] | None:
    name_match = re.search(r"\d+\.\s*\*\*([^*]+)\*\*", section)
    title = ""
    if name_match:
        title = name_match.group(1).strip().rstrip(":")
    else:
        image_alt = re.search(r"!\[([^\]]+)\]\([^)]+\)", section)
        if image_alt:
            title = image_alt.group(1).strip()
        else:
            quoted = re.search(r'^"([^"]+)"|^\*\*([^*]+)\*\*', section.strip())
            if quoted:
                title = (quoted.group(1) or quoted.group(2) or "").strip()

    if not title:
        described = re.search(
            r'^"?([^"\n]+)"?\s+is\s+(?:described\s+as|a\s+)', section, re.IGNORECASE
        )
        if described:
            title = described.group(1).strip()

    if not title:
        return None

    price_match = re.search(r"\*\*Price:\*\*\s*\$([0-9,]+\.?\d*)", section)
    price = _parse_price(price_match.group(1) if price_match else None) or 59.5

    description = ""
    desc_match = re.search(r"\*\*Description:\*\*\s*([^\n]+)", section)
    if desc_match:
        description = desc_match.group(1).strip()
    if not description:
        escaped = re.escape(title)
        is_a = re.search(
            rf'{escaped}\s+is\s+(?:described\s+as\s+|a\s+)(.+?)(?=If\s+you\'re|!\[|\[[^\]]+\]\(|$)',
            section,
            re.IGNORECASE | re.DOTALL,
        )
        if is_a:
            description = is_a.group(1).strip()

    image = ""
    image_match = re.search(r"!\[.*?\]\(([^)]+)\)", section)
    if image_match:
        image = image_match.group(1).strip()
    else:
        link_match = re.search(r"\[[^\]]+\]\(([^)]+)\)", section)
        if link_match and re.search(r"\.(jpg|jpeg|png|gif|webp|svg)(\?|$)", link_match.group(1), re.I):
            image = link_match.group(1).strip()

    rating_match = re.search(r"\*\*Rating:\*\*\s*([0-9.]+)", section)
    rating = float(rating_match.group(1)) if rating_match else 4.5

    review_match = re.search(r"\((\d+)\s+Reviews\)", section)
    review_count = int(review_match.group(1)) if review_match else 0

    stock_match = re.search(r"\*\*In Stock:\*\*\s*(Yes|No)", section, re.I)
    in_stock = stock_match.group(1).lower() == "yes" if stock_match else True

    return {
        "id": _slug_id(title),
        "title": title,
        "price": price,
        "rating": rating,
        "reviewCount": review_count,
        "image": image,
        "category": "Paint Shades",
        "inStock": in_stock,
        "description": description,
    }


def parse_products_from_text(text: str) -> tuple[list[dict[str, Any]], str, str]:
    if not text:
        return [], "", ""

    parts = re.split(r"(?=\d+\.\s*\*\*[^*]+\*\*)", text)
    intro = parts[0].strip() if parts else text.strip()
    intro = re.sub(r"^###\s*[^\n]*\n?", "", intro, flags=re.MULTILINE).strip()

    outro = ""
    last_image = text.rfind("![")
    if last_image != -1:
        tail = text[last_image:]
        after_match = re.search(r"!\[[^\]]*\]\([^)]*\)\.?\s*([\s\S]*?)$", tail)
        if after_match and after_match.group(1).strip():
            candidate = after_match.group(1).strip()
            if not re.match(r"^\d+\.\s*\*\*", candidate):
                outro = candidate

    products: list[dict[str, Any]] = []
    for part in parts[1:]:
        parsed = _parse_product_section(part)
        if parsed:
            products.append(parsed)

    if not products and (
        "![" in text or re.search(r"\[[^\]]+\]\([^)]+\.(jpg|jpeg|png|gif|webp|svg)", text, re.I)
    ):
        parsed = _parse_product_section(text)
        if parsed:
            products.append(parsed)

    return products, intro, outro


def extract_recommended_products(text: str) -> list[dict[str, Any]]:
    if current_scenario() != "ecommerce" or not text:
        return []

    if detect_content_type(text) != "products":
        return []

    products, _, _ = parse_products_from_text(text)
    return [enrich_product(product) for product in products if product.get("title")]
