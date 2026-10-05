# Visual Architecture: Sequence Diagrams

> **BizFlow Transaction Sequence**  
> *Udhaar Credit Sale, Partial Settlement, and Central Business Notification Lifecycle rendered in Mermaid.*

---

## 1. Credit Sale and Partial Settlement Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Cashier as Cashier / POS User
    actor Customer as Debtor Customer
    participant Web as Django Web UI / POS
    participant Svc as CreditService
    participant Stock as StockService
    participant DB as Relational Database
    participant SMS as SMSService

    Note over Cashier, DB: Phase 1: Issuing Credit Sale (Udhaar)
    Customer->>Cashier: Requests goods on credit (Due in 15 days)
    Cashier->>Web: Submits Sale Form (Customer, Items, Method='Credit', Due Date)
    Web->>Svc: create_credit_given(sale_data, items, user)
    Svc->>Stock: validate_stock(items)
    Stock-->>Svc: Stock Available (OK)
    critical Atomic Database Transaction
        Svc->>DB: INSERT into sales (total=10,000, due_date='2026-10-18', status='Due')
        Svc->>DB: INSERT into sale_items
        Svc->>Stock: deduct(product_id, qty)
        Stock->>DB: UPDATE products SET current_stock = current_stock - qty
        Stock->>DB: INSERT into stock_movements (type='OUT', ref='SALE')
    end
    DB-->>Svc: Sale created (ID: 101)
    Svc-->>Web: Success response
    Web-->>Cashier: Displays Invoice & updates Customer Ledger

    Note over Cashier, SMS: Phase 2: Partial Settlement Voucher (Day 10)
    Customer->>Cashier: Pays Rs. 6,000 cash towards Sale #101
    Cashier->>Web: Open /credit/payments/add/ (Select Sale #101, Amount=6000)
    Web->>Svc: add_payment(sale_id=101, amount=6000, method='Cash', user)
    Svc->>DB: Query Sale #101 (Total=10,000, Paid=0, Remaining=10,000)
    Note over Svc: Overpayment Check (6000 <= 10000 -> Valid)
    critical Atomic Payment Transaction
        Svc->>DB: INSERT into payments (amount=6000, sale_id=101, status='Completed')
        Svc->>DB: UPDATE sales SET payment_status = 'Partial'
        Svc->>DB: INSERT into audit_logs (action='Payment Added')
    end
    Svc->>SMS: send_alert_sms(customer_phone, paid=6000, remaining=4000)
    SMS-->>Customer: SMS delivered: "Received Rs. 6,000 for Sale #101. Remaining: Rs. 4,000."
    Svc-->>Web: Voucher Confirmed (Remaining Rs. 4,000)
    Web-->>Cashier: Print Payment Receipt Voucher
```

---

## 2. Central Business Notification & SMS Alert Dispatch Sequence

```mermaid
sequenceDiagram
    autonumber
    actor System as Scheduled Monitor / Stock Event
    participant NotifSvc as NotificationService
    participant Pref as NotificationPreference
    participant DB as Relational Database
    participant SMS as SMSService
    participant Gateway as SMSGateway
    actor Manager as Store Manager / User

    System->>NotifSvc: check_stock_alerts() / check_cheque_reminders()
    NotifSvc->>DB: Query Products (current_stock <= minimum_stock)
    DB-->>NotifSvc: Product "Rice 25kg" (Stock=0 -> Out of Stock)
    
    NotifSvc->>DB: Deduplication Check (dedup_key="stock_out:12:2026-10-03")
    alt Notification Already Created Today
        DB-->>NotifSvc: Exists (Skip duplicate)
    else State Transition / New Day
        NotifSvc->>Pref: Check User Preference (notify_out_of_stock)
        Pref-->>NotifSvc: Enabled (OK)
        critical Save In-App Notification
            NotifSvc->>DB: INSERT INTO notifications (priority='critical', is_popup=true)
        end
        opt SMS Enabled by User
            NotifSvc->>SMS: send_alert_sms(user, "out_of_stock", message, dedup_key)
            SMS->>DB: Check SMSLog (Duplicate phone & key check)
            SMS->>Gateway: send_sms(phone, "ALERT: Rice is out of stock.")
            Gateway-->>SMS: Status: Delivered
            SMS->>DB: INSERT INTO sms_logs (status='Sent', dedup_key=...)
        end
        NotifSvc-->>Manager: In-App Popup + Bell Counter Badge + SMS Alert
    end
```
