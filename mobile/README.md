# Mobile Client Architecture

> **Target Integration for BizFlow Mobile Clients (Android & iOS)**

```
                    ┌─────────────────────────┐
                    │      FastAPI REST       │
                    │       (/api/v1/)        │
                    └────────────┬────────────┘
                                 │ HTTPS / JSON / JWT
                    ┌────────────▼────────────┐
                    │   Mobile Applications   │
                    └────────────┬────────────┘
                           ┌─────┴─────┐
                           │           │
                        Android       iOS
```

## Status
Future phase client architecture. The backend API is designed from day one to be 100% mobile-ready via FastAPI endpoints. Native client binaries are not implemented during this web migration stage.

## Supported Mobile Technologies
Mobile clients will connect to the same FastAPI backend using one of the following stacks:
1. **Flutter (Dart)**: Single codebase targeting both Android and iOS with native camera barcode scanning and Bluetooth receipt printing.
2. **React Native**: Cross-platform mobile development sharing TypeScript interfaces with web frontends.
3. **Native Android (Kotlin) / Native iOS (Swift)**: For hardware-optimized enterprise handheld terminals.

## Mobile Functional Scope
- Mobile inventory stock-taking and camera barcode lookups.
- Delivery driver invoice receipts and payment collections (QR code / cash).
- Owner dashboard metrics and push notifications for low stock alerts.