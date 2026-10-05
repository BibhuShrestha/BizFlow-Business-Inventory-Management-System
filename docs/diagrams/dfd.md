# Visual Architecture: Data Flow Diagrams (DFD)

> **BizFlow Process Data Flows**  
> *Context Level 0 and Level 1 Functional Data Flow Diagrams rendered in Mermaid.*

---

## 1. Context Level 0 DFD

```mermaid
graph TD
    Cashier[Cashier / POS User] -->|1. Customer & Sale Line Items| BizFlow((BizFlow System))
    BizFlow -->|2. Printed Receipt & Stock Status| Cashier

    Manager[Store Manager] -->|3. Supplier Bills & Stock In| BizFlow
    BizFlow -->|4. Daybook, Ledgers & Stock Alerts| Manager

    Customer[Customer / Debtor] -->|5. Partial Payment Settlement| BizFlow
    BizFlow -->|6. SMS Payment Receipt & Due Reminders| Customer

    Admin[System Administrator] -->|7. Configuration, Auth & Companies| BizFlow
    BizFlow -->|8. Audit Logs & Financial Reports| Admin
```

---

## 2. Level 1 Process Breakdown DFD

```mermaid
graph TD
    subgraph Processes["Core Subsystems"]
        P1["1.0 POS & Sales Processing"]
        P2["2.0 Inventory & Stock Control"]
        P3["3.0 Receivables & Payables (Credit)"]
        P4["4.0 Payment Voucher Engine"]
        P5["5.0 Notification & Alert Dispatch"]
    end

    subgraph DataStores["Data Stores"]
        D1[("D1: Products & Stock Movements")]
        D2[("D2: Sales & Invoices")]
        D3[("D3: Payments & Cheques")]
        D4[("D4: Notifications & Audit Logs")]
    end

    Cashier[Cashier] -->|Create Sale| P1
    P1 -->|Query Price & Stock| D1
    P1 -->|Save Invoice| D2
    P1 -->|Trigger Stock Out| P2
    P2 -->|Decrement Stock & Log Movement| D1

    P1 -->|If Credit: Queue Receivable| P3
    P3 -->|Evaluate Dues & Overdue| D2

    Customer[Customer] -->|Submit Payment| P4
    P4 -->|Save Payment Voucher| D3
    P4 -->|Recalculate Status| P3

    P2 -->|If Stock <= Min: Trigger Alert| P5
    P3 -->|If Overdue: Trigger Alert| P5
    P5 -->|Save Alert & Dispatch SMS| D4
```
