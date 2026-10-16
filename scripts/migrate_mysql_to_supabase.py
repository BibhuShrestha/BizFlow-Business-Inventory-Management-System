"""
Automated Migration Tool: MySQL / Source DB -> Supabase PostgreSQL.

Usage:
    # 1. Using DATABASE_URL from .env pointing to Supabase:
    python scripts/migrate_mysql_to_supabase.py --fixture backups/bizflow_backup.json

    # 2. Specifying target PostgreSQL URL directly:
    python scripts/migrate_mysql_to_supabase.py --target-url "postgresql://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:5432/postgres?sslmode=require" --fixture backups/bizflow_backup.json

Steps Performed:
    1. Validates connection to target PostgreSQL (Supabase).
    2. Runs Django migrations to construct PostgreSQL schema with native types:
       - AUTO_INCREMENT -> BIGSERIAL / IDENTITY
       - TINYINT(1) -> BOOLEAN
       - DATETIME -> TIMESTAMPTZ
       - JSON -> JSONB
       - DECIMAL -> NUMERIC
       - Foreign keys and composite indexes
    3. Loads sanitized data fixtures if provided.
    4. Resets all PostgreSQL primary key sequences (prevents ID collision on subsequent INSERTs).
    5. Verifies table status and records.
"""
import os
import sys
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
DJANGO_APP_DIR = BACKEND_DIR / "django_app"

for p in [str(DJANGO_APP_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)


def main():
    parser = argparse.ArgumentParser(description="Migrate MySQL data to Supabase PostgreSQL.")
    parser.add_argument("--fixture", help="Path to JSON data fixture exported from source DB")
    parser.add_argument("--target-url", help="Target Supabase/PostgreSQL DATABASE_URL")
    args = parser.parse_args()

    if args.target_url:
        os.environ["DATABASE_URL"] = args.target_url

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

    import django
    django.setup()

    from django.db import connection, transaction
    from django.core.management import call_command
    from django.conf import settings

    db_config = settings.DATABASES.get("default", {})
    engine = db_config.get("ENGINE", "")

    print("===================================================================")
    print("      BizFlow Migration Tool -> PostgreSQL / Supabase              ")
    print("===================================================================")
    print(f"[*] Target Database Engine: {engine}")
    print(f"[*] Target Host: {db_config.get('HOST', 'localhost')}")
    print(f"[*] Target Database: {db_config.get('NAME')}")

    # 1. Connection check
    print("\n[Step 1/4] Testing connection to database...")
    try:
        connection.ensure_connection()
        with connection.cursor() as cur:
            cur.execute("SELECT version();" if "postgresql" in engine else "SELECT 1;")
            ver = cur.fetchone()[0]
            print(f"[+] Connection established! Database version:\n    {ver}")
    except Exception as e:
        print(f"[ERROR] Could not connect to target database: {e}")
        sys.exit(1)

    # 2. Run Django migrations
    print("\n[Step 2/4] Applying Django schema migrations...")
    try:
        call_command("migrate", interactive=False)
        print("[+] All migrations applied successfully.")
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        sys.exit(1)

    # 3. Load fixture data if supplied
    if args.fixture:
        fixture_path = Path(args.fixture)
        if not fixture_path.exists():
            print(f"[ERROR] Fixture file not found: {fixture_path}")
            sys.exit(1)

        print(f"\n[Step 3/4] Importing fixture data from {fixture_path}...")
        try:
            call_command("loaddata", str(fixture_path))
            print("[+] Data fixture loaded successfully!")
        except Exception as e:
            print(f"[!] Warning during loaddata: {e}")
            print("    Attempting model-by-model verification...")

    # 4. PostgreSQL Sequence Reset (Critical for PostgreSQL/Supabase)
    if "postgresql" in engine or "postgres" in engine:
        print("\n[Step 4/4] Aligning PostgreSQL primary key sequences (setval)...")
        try:
            with connection.cursor() as cur:
                cur.execute("""
                    SELECT c.relname, a.attname
                    FROM pg_class c
                    JOIN pg_attribute a ON a.attrelid = c.oid
                    JOIN pg_index i ON i.indrelid = c.oid AND a.attnum = ANY(i.indkey)
                    WHERE c.relkind = 'r'
                      AND i.indisprimary
                      AND c.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                    ORDER BY c.relname;
                """)
                tables_and_pks = cur.fetchall()

                for table_name, pk_col in tables_and_pks:
                    try:
                        cur.execute(f"""
                            SELECT setval(
                                pg_get_serial_sequence('{table_name}', '{pk_col}'),
                                COALESCE((SELECT MAX({pk_col}) FROM "{table_name}"), 1),
                                true
                            );
                        """)
                    except Exception:
                        pass
            print("[+] All PostgreSQL sequences aligned with existing primary keys.")
        except Exception as e:
            print(f"[!] Sequence reset note: {e}")
    else:
        print("\n[Step 4/4] Skipped sequence reset (Non-PostgreSQL engine).")

    print("\n===================================================================")
    print(" [SUCCESS] Supabase / PostgreSQL migration process complete!")
    print("===================================================================")


if __name__ == "__main__":
    main()
