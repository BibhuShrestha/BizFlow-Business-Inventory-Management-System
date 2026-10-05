# External Integrations Architecture

> **BizFlow Integration Pipelines**  
> *Specifications for Transactional Email, Google OAuth2, SMS Gateways, File Exports, and PDF Generation.*

---

## 1. Integration Matrix

```mermaid
graph LR
    BizFlow[BizFlow Core Engine] --> SMTP[Email Engine (SMTP / Core)]
    BizFlow --> OAuth[Google OAuth2 Flow]
    BizFlow --> SMS[SMS Gateway Service]
    BizFlow --> Exports[OpenPyXL / CSV Export Engine]
    BizFlow --> PDF[Thermal & A4 PDF Generator]

    SMTP --> MailLogs[apps.audit.models.EmailLog]
    SMS --> AuditLogs[apps.audit.models.AuditLog]
    Exports --> ExportLogs[apps.audit.models.ExportLog]
```

---

## 2. Transactional Email Pipeline (`backend/integrations/email.py`)
- **Protocol**: SMTP over TLS / SSL.
- **Failover / Logging**: All dispatched emails are mirrored in `apps.audit.models.EmailLog`.
- **Use Cases**: Account verification, password reset tokens, critical system error broadcasts.

---

## 3. Google OAuth2 Social Authentication (`backend/integrations/google_oauth.py`)
- **Flow**: Authorization Code Grant with PKCE.
- **State Validation**: CSRF state parameter stored in session to prevent login CSRF.
- **User Provisioning**: Auto-provisions or links existing `accounts.User` record matching verified email.

---

## 4. SMS Gateway Provider Integration (`backend/integrations/sms.py`)
- **Target**: Mobile carriers (Sparrow SMS, Aakash SMS, Twilio).
- **Design Pattern**: Adapter pattern allowing seamless gateway provider switching via settings.
- **Rate Limiting**: In-memory / cache throttle preventing duplicate debtor harassment ($1\text{ SMS / 24h}$).

---

## 5. File Export & Spreadsheet Engine (`backend/django_app/apps/core_app/exports.py`)
- **CSV**: Encoded with UTF-8 BOM (`\ufeff`) to ensure international UTF-8 character preservation in Microsoft Excel.
- **Excel (.xlsx)**: Built via `openpyxl` with Dark Slate header formatting, bold white fonts, and dynamic column auto-sizing.
- **Security**: 10MB file upload guard and filename sanitization via `os.path.basename`.
