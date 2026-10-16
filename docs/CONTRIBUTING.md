# Contributing to BizFlow

> **Developer Guidelines and Coding Standards for BizFlow (Django SSR + FastAPI).**

---

## 1. Architectural Principles

1. **Lightweight & Framework-Free Frontend**:
   - The frontend is built strictly with **Django Templates**, **Vanilla CSS** (`main.css`), and **Vanilla JavaScript**.
   - Do NOT introduce React, Vue, Angular, Bootstrap, Tailwind, or SPA frameworks.
2. **Unified Data Layer via Django ORM**:
   - Both Django views and FastAPI routes must use Django ORM models.
   - Do NOT introduce a second ORM (such as SQLAlchemy or Tortoise).
3. **Domain Service Encapsulation**:
   - All complex business calculations (stock movements, invoicing, credit balances, ledger records) must reside in `backend/domain/services/`.
   - Never place business logic directly in views or route handlers.

---

## 2. Development Setup

1. **Prerequisites**: Python 3.12+ (or 3.13), Git.
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment Setup**:
   - Copy `.env.example` to `.env`.
   - Default configuration uses local SQLite (`inventory.db`) with zero external dependencies.
4. **Run Migrations**:
   ```bash
   python backend/django_app/manage.py migrate
   ```
5. **Start Dev Server**:
   ```bash
   python scripts/run_dev.py
   ```

---

## 3. Testing Requirements

- Before committing, ensure the entire test suite passes:
  ```bash
  python -m pytest
  ```
- All new features must include corresponding unit and integration tests under `tests/`.
- Ensure `python backend/django_app/manage.py check` passes with 0 issues.

---

## 4. Coding & Git Standards

- Follow **PEP 8** style guidelines.
- Use explicit type annotations.
- Keep commits atomic and prefixed (e.g. `feat:`, `fix:`, `docs:`, `test:`).
- Keep `CHANGELOG.md` updated adhering to Keep a Changelog.
