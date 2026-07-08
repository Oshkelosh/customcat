"""CustomCat print-on-demand supplier integration."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field, SecretStr

from app.addons.suppliers.base import SupplierAddon
from app.addons.suppliers.customcat.catalog import normalize_customcat_catalog_products
from app.addons.suppliers.customcat.client import CustomCatAPIError, CustomCatClient
from schemas.supplier import SupplierCatalogProduct
from app.addons.log import info, warning
from app.addons.config_serialization import dump_addon_config


class CustomCatConfig(BaseModel):
    api_key: SecretStr = Field(default=..., description="CustomCat API key")
    is_active: bool = Field(default=False)
    sandbox: bool = Field(default=False, description="Submit sandbox test orders")

    @classmethod
    def config_model(cls):
        return cls


def _map_shipping(address: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "first_name": address.get("first_name", ""),
        "last_name": address.get("last_name", ""),
        "address1": address.get("line1", ""),
        "address2": address.get("line2", ""),
        "city": address.get("city", ""),
        "state": address.get("state", ""),
        "zip": address.get("zip", ""),
        "country": address.get("country", ""),
        "email": address.get("email", ""),
        "phone": address.get("phone", ""),
    }


class CustomCatAddon(SupplierAddon):
    addon_id: str = "customcat"
    addon_name: str = "CustomCat"
    addon_description: str = "US print-on-demand via CustomCat API."
    addon_category: str = "supplier"
    version: str = "1.0.0"

    _config: Dict[str, Any] | None = None
    _client: CustomCatClient | None = None

    @classmethod
    def config_schema(cls):
        return CustomCatConfig

    async def initialize(self, config: dict) -> None:
        validated = CustomCatConfig(**config)
        self._config = dump_addon_config(validated)
        self._client = CustomCatClient(
            validated.api_key.get_secret_value(),
            sandbox=validated.sandbox,
        )
        self.is_enabled = validated.is_active
        info("CustomCat", "Initialized sandbox={}", validated.sandbox)

    async def validate_config(self, config: dict) -> None:
        from app.core.exceptions import ValidationError

        validated = CustomCatConfig(**config)
        api_key = validated.api_key.get_secret_value()
        if not api_key:
            return
        client = CustomCatClient(api_key, sandbox=validated.sandbox)
        try:
            await client.get_catalog()
        except CustomCatAPIError as exc:
            if exc.status_code == 401:
                raise ValidationError(message="Invalid API key — check your credentials") from exc
            if exc.status_code == 403:
                raise ValidationError(
                    message="API key is valid but missing required permissions: catalog:read"
                ) from exc
            raise ValidationError(message=f"CustomCat API error: {exc}") from exc

    async def shutdown(self) -> None:
        self._client = None
        self._config = None
        self.is_enabled = False

    def _require_client(self) -> CustomCatClient:
        if self._client is None:
            raise CustomCatAPIError("CustomCat addon is not initialized")
        return self._client

    async def list_products(self, **kwargs: Any) -> List[Dict[str, Any]]:
        catalog = await self._require_client().get_catalog()
        if isinstance(catalog, list):
            return [r for r in catalog if isinstance(r, dict)]
        if isinstance(catalog, dict):
            for key in ("catalog", "products", "data"):
                val = catalog.get(key)
                if isinstance(val, list):
                    return [r for r in val if isinstance(r, dict)]
        return []

    async def fetch_catalog_for_import(self, **kwargs: Any) -> List[SupplierCatalogProduct]:
        catalog = await self._require_client().get_catalog()
        return normalize_customcat_catalog_products(catalog)

    async def get_product(self, product_id: str) -> Dict[str, Any]:
        for row in await self.list_products():
            sku = str(row.get("catalog_sku") or row.get("sku") or row.get("id") or "")
            if sku == product_id:
                return row
        return {"error": f"CustomCat SKU '{product_id}' not found"}

    async def create_order(
        self,
        items: List[Dict[str, Any]],
        shipping_address: Dict[str, Any],
        *,
        external_id: str | None = None,
        supplier_ref: str | None = None,
    ) -> Dict[str, Any]:
        del supplier_ref
        client = self._require_client()
        try:
            line_items = []
            for item in items:
                sku = str(item.get("supplier_product_id") or "").strip()
                if not sku:
                    continue
                line_items.append(
                    {
                        "catalog_sku": sku,
                        "quantity": int(item.get("quantity") or 1),
                    }
                )
            if not line_items:
                return {"success": False, "error": "No valid CustomCat line items"}

            payload: Dict[str, Any] = {
                "items": line_items,
                "shipping": _map_shipping(shipping_address),
            }
            if external_id:
                payload["order_id"] = external_id

            data = await client.create_order(payload)
            order_id = str(data.get("order_id") or data.get("id") or "")
            return {
                "success": True,
                "order_id": order_id,
                "status": data.get("status", "submitted"),
                "customcat_order_id": order_id,
            }
        except CustomCatAPIError as exc:
            warning("CustomCat", "create_order error: {}", exc)
            return {"success": False, "error": str(exc)}

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        try:
            data = await self._require_client().get_order(order_id)
            return {"order_id": order_id, "status": data.get("status", "unknown")}
        except CustomCatAPIError as exc:
            return {"order_id": order_id, "status": "error", "detail": str(exc)}

    async def sync_inventory(self) -> None:
        products = await self.list_products()
        info("CustomCat", "Catalog has {} SKUs", len(products))

    def get_routers(self) -> List[APIRouter]:
        from app.addons.suppliers.customcat.routes import api_router

        return [api_router]

    def get_admin_routes(self) -> List[APIRouter]:
        from app.addons.suppliers.customcat.routes import admin_router

        return [admin_router]

    def get_admin_templates(self) -> str:
        from pathlib import Path

        return str(Path(__file__).resolve().parent / "templates")

    def get_admin_static(self) -> str:
        from pathlib import Path

        return str(Path(__file__).resolve().parent / "static")
