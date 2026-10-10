"""
Seed initial system roles and an optional default admin user for development.
Run:
    py scripts/seed_roles.py
"""
import os
import sys
from pathlib import Path

# Setup paths
_ROOT = Path(__file__).resolve().parent.parent
_DJANGO_APP = _ROOT / "backend" / "django_app"
_BACKEND = _ROOT / "backend"

for p in [str(_DJANGO_APP), str(_BACKEND)]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
django.setup()

from apps.accounts.models import Role, User
from apps.companies.models import Company

def seed():
    roles_data = [
        {"name": Role.ROLE_ADMIN, "description": "System Administrator with full access"},
        {"name": Role.ROLE_MANAGER, "description": "Store Manager with management access"},
        {"name": Role.ROLE_STAFF, "description": "Staff Member with operations access"},
        {"name": "cashier", "description": "Cashier with POS checkout and counter sales access"},
        {"name": Role.ROLE_CUSTOMER, "description": "Customer with view-only catalog access"},
    ]

    for data in roles_data:
        role, created = Role.objects.get_or_create(name=data["name"], defaults={"description": data["description"]})
        status = "Created" if created else "Already exists"
        print(f"Role '{role.name}': {status}")

    # Create default demo company if none exists
    company, created = Company.objects.get_or_create(
        company_name="BizFlow Demo Corp",
        defaults={
            "company_phone": "9800000000",
            "vat_pan_number": "123456789",
            "address": "Kathmandu, Nepal",
        }
    )
    if created:
        print(f"Created default company: {company.company_name}")

    # Create default admin user if none exists
    admin_email = "admin@bizflow.com"
    admin_pass = "Admin@12345"
    admin_role = Role.objects.get(name=Role.ROLE_ADMIN)

    if not User.objects.filter(email=admin_email).exists():
        admin = User.objects.create_superuser(
            email=admin_email,
            name="BizFlow Admin",
            password=admin_pass,
            role=admin_role,
            active_company=company,
        )
        print(f"Created default superuser: {admin.email} (Password: {admin_pass})")
    else:
        print(f"Superuser '{admin_email}' already exists.")

if __name__ == "__main__":
    seed()
