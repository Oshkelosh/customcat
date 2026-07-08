"""Unit tests for CustomCat catalog normalization."""

from app.addons.suppliers.customcat.catalog import normalize_customcat_catalog


def test_customcat_skips_out_of_stock():
    items = normalize_customcat_catalog([{"catalog_sku": "CC-1", "name": "Hat", "in_stock": False}])
    assert items[0].skip_reason is not None
