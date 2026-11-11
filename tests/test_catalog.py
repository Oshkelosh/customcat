"""Unit tests for CustomCat catalog normalization."""

from app.addons.suppliers.customcat.catalog import (
    normalize_customcat_catalog,
    normalize_customcat_catalog_products,
)


def test_customcat_skips_out_of_stock():
    items = normalize_customcat_catalog([{"catalog_sku": "CC-1", "name": "Hat", "in_stock": False}])
    assert items[0].skip_reason is not None


def test_customcat_products_fill_image_alts():
    products = normalize_customcat_catalog_products(
        [{"catalog_sku": "CC-2", "name": "Hat", "price": "8.00", "image": "https://cdn.example/hat.jpg"}]
    )
    assert products[0].image_urls == []
    assert products[0].variants[0].image_alt_texts == ["Hat"]
