"""CustomCat catalog normalization."""

from __future__ import annotations

from typing import Any

from app.addons.suppliers.catalog_utils import decimal_price_to_cents, flat_catalog_item_to_product
from schemas.supplier import POD_INVENTORY_PLACEHOLDER, SupplierCatalogItem, SupplierCatalogProduct


def normalize_customcat_catalog(raw: Any) -> list[SupplierCatalogItem]:
    items: list[SupplierCatalogItem] = []
    rows: list[dict[str, Any]] = []
    if isinstance(raw, list):
        rows = [r for r in raw if isinstance(r, dict)]
    elif isinstance(raw, dict):
        for key in ("catalog", "products", "data", "items"):
            val = raw.get(key)
            if isinstance(val, list):
                rows = [r for r in val if isinstance(r, dict)]
                break

    for row in rows:
        sku = str(row.get("catalog_sku") or row.get("sku") or row.get("id") or "").strip()
        if not sku:
            continue
        if row.get("in_stock") is False or row.get("available") is False:
            items.append(
                SupplierCatalogItem(
                    external_key=f"customcat:{sku}",
                    name=str(row.get("name") or sku),
                    description=None,
                    price_cents=0,
                    sku=None,
                    image_url=None,
                    supplier_value="customcat",
                    supplier_product_id=sku,
                    supplier_variant_id="",
                    inventory_quantity=0,
                    skip_reason="CustomCat SKU is out of stock",
                )
            )
            continue
        name = str(row.get("name") or row.get("product_name") or sku)
        price = row.get("price") or row.get("retail_price") or row.get("cost")
        items.append(
            SupplierCatalogItem(
                external_key=f"customcat:{sku}",
                name=name,
                description=row.get("description"),
                price_cents=decimal_price_to_cents(price),
                sku=sku,
                image_url=row.get("image") or row.get("image_url"),
                supplier_value="customcat",
                supplier_product_id=sku,
                supplier_variant_id="",
                inventory_quantity=POD_INVENTORY_PLACEHOLDER,
            )
        )
    return items


def normalize_customcat_catalog_products(raw: Any) -> list[SupplierCatalogProduct]:
    """Map CustomCat catalog rows to single-variant catalog products."""
    return [flat_catalog_item_to_product(item) for item in normalize_customcat_catalog(raw)]
