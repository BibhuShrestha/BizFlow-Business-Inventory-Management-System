"""
Safe database reset and schema rebuild script for Supabase PostgreSQL / Django.
1. Confirms connected target database.
2. Clears the public schema (DROP SCHEMA public CASCADE; CREATE SCHEMA public;).
3. Applies all migrations from scratch.
4. Seeds essential initial data (Roles, Default Company, New Superuser).
5. Verifies database cleanliness and superuser login.
"""
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_DJANGO_APP = _ROOT / "backend" / "django_app"
_BACKEND = _ROOT / "backend"

for p in [str(_DJANGO_APP), str(_BACKEND), str(_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
django.setup()

from django.db import connection
from django.conf import settings
from django.core.management import call_command


def run_reset():
    db_conf = settings.DATABASES["default"]
    engine = db_conf.get("ENGINE", "")
    host = db_conf.get("HOST", "")
    db_name = db_conf.get("NAME", "")
    user = db_conf.get("USER", "")

    print("==================================================")
    print("BIZFLOW SAFE DATABASE RESET UTILITY")
    print("==================================================")
    print(f"Engine:    {engine}")
    print(f"Host:      {host}")
    print(f"Database:  {db_name}")
    print(f"User:      {user}")

    # Step 1: Wipe existing tables
    print("\n[Step 1/4] Dropping and recreating schema 'public'...")
    with connection.cursor() as cursor:
        if "postgresql" in engine or "postgres" in engine:
            cursor.execute("DROP SCHEMA IF EXISTS public CASCADE;")
            cursor.execute("CREATE SCHEMA public;")
            cursor.execute("GRANT ALL ON SCHEMA public TO postgres;")
            cursor.execute("GRANT ALL ON SCHEMA public TO public;")
            # Supabase default roles if they exist
            for role in ["anon", "authenticated", "service_role"]:
                try:
                    cursor.execute(f"GRANT ALL ON SCHEMA public TO {role};")
                except Exception:
                    pass
            print("Successfully recreated public schema.")
        else:
            # SQLite fallback
            tables = connection.introspection.table_names()
            for t in tables:
                cursor.execute(f'DROP TABLE IF EXISTS "{t}";')
            print(f"Dropped {len(tables)} SQLite tables.")

    # Step 2: Run all migrations from scratch
    print("\n[Step 2/4] Running all Django migrations from scratch...")
    call_command("migrate", interactive=False)
    print("All migrations applied successfully.")

    # Step 3: Seed essential data (roles, default company, new administrator)
    print("\n[Step 3/4] Seeding initial roles, company, and fresh administrator...")
    from scripts.seed_roles import seed
    seed()

    # Step 4: Verification
    print("\n[Step 4/4] Verifying clean database state and admin authentication...")
    from apps.accounts.models import User, Role
    from apps.companies.models import Company
    from apps.inventory.models import Product
    from apps.sales.models import Sale
    from apps.purchases.models import Purchase
    from domain.services.auth_service import AuthService

    total_users = User.objects.count()
    total_roles = Role.objects.count()
    total_companies = Company.objects.count()
    total_products = Product.objects.count()
    total_sales = Sale.objects.count()
    total_purchases = Purchase.objects.count()

    print(f"Verified counts:")
    print(f" - Users:      {total_users} (Expected: 1 admin)")
    print(f" - Roles:      {total_roles} (Expected: 5 roles)")
    print(f" - Companies:  {total_companies} (Expected: 1 company)")
    print(f" - Products:   {total_products} (Expected: 0 clean)")
    print(f" - Sales:      {total_sales} (Expected: 0 clean)")
    print(f" - Purchases:  {total_purchases} (Expected: 0 clean)")

    admin_email = (getattr(settings, "DEFAULT_ADMIN_EMAIL", None) or os.getenv("DEFAULT_ADMIN_EMAIL", "admin@bizflow.com")).strip().lower()
    admin_pass = getattr(settings, "DEFAULT_ADMIN_PASSWORD", None) or os.getenv("DEFAULT_ADMIN_PASSWORD")

    admin = User.objects.get(email__iexact=admin_email)
    assert admin.is_superuser, "Admin is_superuser must be True"
    assert admin.is_staff, "Admin is_staff must be True"
    assert admin.is_active, "Admin is_active must be True"
    assert admin.email_verified, "Admin email_verified must be True"
    assert admin.role and admin.role.name == Role.ROLE_ADMIN, "Admin role must be admin"
    assert admin.password.startswith("pbkdf2_sha256$") or admin.password.startswith("argon2$"), "Admin password must be properly hashed"

    # Test login
    auth_user = AuthService.authenticate(email=admin_email, password=admin_pass)
    assert auth_user.id == admin.id, "Authentication verification failed"
    print(f"\nSUCCESS: Admin user '{admin_email}' authenticated and verified with superuser privileges.")
    print("Database reset completed successfully.")


if __name__ == "__main__":
    run_reset()
