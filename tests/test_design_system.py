"""Tests for Part 10: UI/UX & Design System.

Verifies:
- Color palette tokens: #2563EB, #1E3A8A, #FFFFFF, #F8FAFC, #E2E8F0, #0F172A, #64748B
- Absence of anti-patterns (no excessive gradients/animations)
- Core components: typography, buttons, inputs, selects, checks, tables, cards, alerts, navigation
- Responsive breakpoints and layout classes
- Keyboard accessibility focus-visible outlines
- Template rendering conformity across landing, dashboard, and invoice screens
- Documentation completeness in docs/DESIGN_SYSTEM.md
"""
import os
from pathlib import Path
import re
import pytest
from django.test import Client

from apps.accounts.models import User, Role
from apps.companies.models import Company
from apps.sales.models import Sale, Customer
from django.utils import timezone


@pytest.fixture
def auth_client(db):
    """Returns an authenticated test client with an active company."""
    role, _ = Role.objects.get_or_create(name="admin", defaults={"description": "Admin"})
    company = Company.objects.create(
        company_name="Design System Corp",
        company_phone="9800000000",
        vat_pan_number="123456789"
    )
    user = User.objects.create_user(
        email="designer@test.com",
        name="UI Designer",
        password="ValidPassword123!",
        role=role,
        active_company=company
    )
    client = Client()
    client.force_login(user)
    return client, user, company


class TestDesignTokensAndCSS:
    @pytest.fixture
    def css_text(self):
        root_dir = Path(__file__).resolve().parent.parent
        css_file = root_dir / "backend" / "django_app" / "static" / "css" / "main.css"
        assert os.path.exists(css_file), f"main.css not found at {css_file}"
        with open(css_file, "r", encoding="utf-8") as f:
            return f.read()

    def test_required_palette_present(self, css_text):
        """10.1 Required palette must be present in CSS variables."""
        palette = [
            ("#2563EB", "Primary Blue"),
            ("#1E3A8A", "Dark Blue"),
            ("#FFFFFF", "White"),
            ("#F8FAFC", "Background Slate-50"),
            ("#E2E8F0", "Border Slate-200"),
            ("#0F172A", "Text Slate-900"),
            ("#64748B", "Secondary Text Slate-500"),
        ]
        for hex_code, name in palette:
            assert hex_code.upper() in css_text.upper(), f"Missing required palette token {name} ({hex_code}) in main.css"

    def test_keyboard_accessibility_focus_visible(self, css_text):
        """Keyboard accessibility :focus-visible ring must be defined."""
        assert ":focus-visible" in css_text
        assert "outline" in css_text

    def test_button_component_variants(self, css_text):
        """10.3 Buttons: primary, secondary, danger, ghost, sm, lg."""
        required_classes = [".btn", ".btn-primary", ".btn-secondary", ".btn-danger", ".btn-ghost", ".btn-sm", ".btn-lg"]
        for cls in required_classes:
            assert cls in css_text, f"Missing button class {cls} in main.css"

    def test_form_component_controls_and_validation(self, css_text):
        """10.3 Form inputs, checkboxes, radios, validation states."""
        required_form_classes = [
            ".form-group",
            ".form-label",
            ".form-control",
            ".form-check",
            ".form-check-input",
            ".is-invalid",
            ".is-valid"
        ]
        for cls in required_form_classes:
            assert cls in css_text, f"Missing form class {cls} in main.css"

    def test_tables_and_empty_states(self, css_text):
        """10.3 Tables, headers, hover states, and empty states."""
        assert ".table-container" in css_text
        assert "thead" in css_text
        assert ".table-empty" in css_text
        assert ".empty-state" in css_text

    def test_cards_and_stat_grid(self, css_text):
        """10.3 Cards and compact stat grid metrics."""
        assert ".card" in css_text
        assert ".card-header" in css_text
        assert ".stat-grid" in css_text
        assert ".stat-card" in css_text
        assert ".stat-value" in css_text

    def test_alerts_semantic_variants(self, css_text):
        """10.3 Alerts: success, danger, warning, info."""
        required_alerts = [".alert", ".alert-success", ".alert-danger", ".alert-warning", ".alert-info"]
        for alert_cls in required_alerts:
            assert alert_cls in css_text, f"Missing alert class {alert_cls} in main.css"

    def test_responsive_breakpoints(self, css_text):
        """10.3 Responsive breakpoints for mobile, tablet, and desktop."""
        assert "@media (max-width: 1024px)" in css_text
        assert "@media (max-width: 640px)" in css_text


@pytest.mark.django_db
class TestTemplateRenderingAesthetics:
    def test_landing_page_clean_aesthetics(self):
        """Verify landing page renders clean HTML without excessive gradients."""
        client = Client()
        response = client.get("/")
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "main.css" in content
        assert "radial-gradient" not in content
        assert "BizFlow" in content
        assert "btn btn-primary" in content

    def test_dashboard_minimal_cards_and_navigation(self, auth_client):
        """Verify dashboard implements minimal cards, clean stats, and sidebar."""
        client, user, company = auth_client
        response = client.get("/dashboard/")
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "sidebar" in content
        assert "stat-card" in content
        assert "Acme Corp" not in content  # Uses Design System Corp
        assert "Design System Corp" in content

    def test_invoice_printable_layout(self, auth_client):
        """Verify sales invoice detail template includes print styles."""
        client, user, company = auth_client
        customer = Customer.objects.create(company=company, name="Test Buyer")
        sale = Sale.objects.create(company=company, customer=customer, invoice_number="INV-DESIGN-01", total=1500.00, sale_date=timezone.now())
        response = client.get(f"/sales/{sale.id}/")
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "@media print" in content
        assert "window.print()" in content
        assert "TAX INVOICE" in content


class TestDesignSystemDocumentation:
    def test_design_system_doc_exists_and_complete(self):
        """Verify docs/DESIGN_SYSTEM.md exists and covers all required sections."""
        root_dir = Path(__file__).resolve().parent.parent
        doc_path = root_dir / "docs" / "DESIGN_SYSTEM.md"
        assert os.path.exists(doc_path), f"Missing docs/DESIGN_SYSTEM.md at {doc_path}"
        with open(doc_path, "r", encoding="utf-8") as f:
            text = f.read()

        required_topics = [
            "#2563EB",
            "#1E3A8A",
            "#FFFFFF",
            "#F8FAFC",
            "#E2E8F0",
            "#0F172A",
            "#64748B",
            "Typography",
            "Spacing",
            "Buttons",
            "Form Controls",
            "Tables",
            "Cards",
            "Alerts",
            "Navigation",
            "Responsive Breakpoints",
            "UX Patterns",
        ]
        for topic in required_topics:
            assert topic in text, f"Missing topic '{topic}' in docs/DESIGN_SYSTEM.md"
