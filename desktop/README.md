# Desktop Client Architecture

> **Target Integration for BizFlow Desktop Clients**

```
                    ┌─────────────────────────┐
                    │      FastAPI REST       │
                    │       (/api/v1/)        │
                    └────────────┬────────────┘
                                 │ HTTPS / JWT
                    ┌────────────▼────────────┐
                    │   Desktop POS Client    │
                    │ (PySide6 / Tauri / Elec)│
                    └─────────────────────────┘
```

## Status
Future phase client architecture. Architecture and API contracts are established in FastAPI. The desktop binary client is not implemented during the core web migration stage.

## Supported Desktop Technologies
When implemented, desktop clients can be developed using any of the following options depending on deployment requirements:
1. **PySide6 / Qt**: High-performance native Python GUI with native thermal printer support, local SQLite offline caching, and direct serial/USB barcode scanner integrations.
2. **Tauri (Rust + Web Frontend)**: Ultra-lightweight memory footprint, fast launch times, and web UI reusability.
3. **Electron**: Cross-platform web wrapper using web POS UI components.

## Integration Contract
- **Authentication**: OAuth2 password bearer flow (`POST /api/v1/auth/login`) returning JWT access and refresh tokens.
- **Data Synchronization**: REST endpoints (`/api/v1/inventory/`, `/api/v1/sales/`, `/api/v1/customers/`).
- **Offline Resilience**: Cashier terminals can buffer invoices locally when network is unavailable and batch-sync via `/api/v1/sales/batch` upon reconnection.