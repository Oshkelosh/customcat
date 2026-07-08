# CustomCat (`customcat`)

US print-on-demand via CustomCat API.

## Overview

| | |
|---|---|
| Addon ID | `customcat` |
| Category | supplier |
| Version | 1.0.0 |
| Category guide | [../README.md](../README.md) |
| Fulfillment key | `customcat` |

Multiple suppliers can be enabled at the same time. Fulfillment runs when an order becomes **paid**.

## Enable and configure

1. Install this package under `app/addons/suppliers/customcat/`
2. Open **Admin → Suppliers → CustomCat** at `/admin/suppliers/customcat`
3. Enter API credentials and enable the addon

## Configuration schema

| Field | Type | Description |
|-------|------|-------------|
| `api_key` | secret | CustomCat API key |
| `is_active` | bool | Whether the addon is active |
| `sandbox` | bool | Submit sandbox test orders |

## Routes

### Public API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/suppliers/customcat/products` | List catalog products |

### Admin

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/suppliers/customcat` | Config form |
| POST | `/admin/suppliers/customcat/save` | Save config |
| POST | `/admin/suppliers/customcat/sync` | Trigger catalog sync |

## Core integration

- **Variant supplier fields:** paid-order fulfillment reads CustomCat SKUs from each **ProductVariant** row
- **Fulfillment:** creates CustomCat order; respects sandbox toggle
- **Grouping:** line items grouped by fulfillment key `customcat`

## Variant supplier fields

| Field | Description |
|-------|-------------|
| `supplier_addon_id` | `customcat` |
| `supplier_product_id` | CustomCat catalog SKU |

## Catalog sync

Supported. Admin sync at `/admin/suppliers/customcat` or `POST /api/v1/admin/suppliers/customcat/sync`.

**Import model:** grouped products; one variant per catalog SKU.

| Key | Format |
|-----|--------|
| Variant dedup key | `customcat:{sku}` |

**Prerequisites:**

- Out-of-stock SKUs are skipped during import.

## Provider setup

- Obtain API key from CustomCat.

## Package layout

```
customcat/
├── README.md
├── addon.py
├── catalog.py
├── client.py
├── routes.py
└── templates/
```

## See also

- [Supplier addon development](../README.md)
- [Oshkelosh addon guide](../../README.md)
