# Database Relationships & Foreign Keys

> **BizFlow Referential Integrity Guide**  
> *Cardinality, Foreign Key cascade rules, and entity connections.*

---

## 1. Cardinality Overview

```text
Company (1) ───────────< (N) User
Company (1) ───────────< (N) Product
Company (1) ───────────< (N) Customer
Company (1) ───────────< (N) Supplier
Company (1) ───────────< (N) Sale
Company (1) ───────────< (N) Purchase

Category (1) ──────────< (N) Product
Product (1) ───────────< (N) StockMovement
Product (1) ───────────< (N) SaleItem
Product (1) ───────────< (N) PurchaseItem

Customer (1) ──────────< (N) Sale
Sale (1) ──────────────< (N) SaleItem
Sale (1) ──────────────< (N) Payment

Supplier (1) ──────────< (N) Purchase
Purchase (1) ──────────< (N) PurchaseItem
Purchase (1) ──────────< (N) Payment

User (1) ──────────────< (N) Payment (created_by)
User (1) ──────────────< (N) Notification
User (1) ──────────────< (N) AuditLog
```

---

## 2. Referential Deletion Policies (`on_delete`)

| Foreign Key | Parent Entity | Child Entity | Deletion Rule | Rationale |
|---|---|---|---|---|
| `Product.category` | `Category` | `Product` | `RESTRICT` | Prevents deleting a category while products still reference it. |
| `SaleItem.product` | `Product` | `SaleItem` | `RESTRICT` | Preserves past historical invoices; products with sales cannot be hard deleted. |
| `PurchaseItem.product`| `Product` | `PurchaseItem` | `RESTRICT` | Preserves purchase history and cost audit trails. |
| `SaleItem.sale` | `Sale` | `SaleItem` | `CASCADE` | Deleting/voiding an invoice header removes its line items. |
| `PurchaseItem.purchase`| `Purchase` | `PurchaseItem`| `CASCADE` | Deleting/voiding a purchase removes its line items. |
| `Sale.customer` | `Customer` | `Sale` | `SET_NULL` | If a customer is deleted, sales invoices retain anonymous history. |
| `Purchase.supplier` | `Supplier` | `Purchase` | `SET_NULL` | If a vendor is removed, purchase bills retain anonymous history. |
| `Payment.sale` | `Sale` | `Payment` | `SET_NULL` | Preserves payment voucher audit if an invoice is voided. |
| `Notification.user` | `User` | `Notification` | `CASCADE` | Removing a user account cascades to their notification queue. |
