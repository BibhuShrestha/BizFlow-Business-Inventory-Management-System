"""
MySQL Database Backup Utility.

Usage:
    python scripts/backup_mysql.py [--output backups/mysql_backup.json]

Features:
    1. Reads database credentials from environment variables (.env).
    2. Performs a non-destructive database backup.
    3. Exports clean, database-agnostic JSON fixture format preserving:
       - Natural keys, foreign keys, relationships, model instances.
    4. If mysqldump CLI is available on the host, optionally generates raw SQL dump as well.
"""
import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
DJANGO_APP_DIR = BACKEND_DIR / "django_app"

for p in [str(DJANGO_APP_DIR), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django  # noqa: E402
django.setup()

from django.core.management import call_command  # noqa: E402
from django.conf import settings  # noqa: E402


def run_backup(output_file: str | None = None) -> Path:
    backup_dir = BASE_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not output_file:
        json_path = backup_dir / f"bizflow_backup_{timestamp}.json"
    else:
        json_path = Path(output_file)
        json_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[*] Starting BizFlow Database Backup [{timestamp}]...")
    db_config = settings.DATABASES.get("default", {})
    engine = db_config.get("ENGINE", "")
    print(f"[*] Source Database Engine: {engine}")

    # 1. Django Model-Agnostic JSON Dump (Compatible with PostgreSQL / Supabase)
    print(f"[*] Exporting data fixture to: {json_path}")
    with open(json_path, "w", encoding="utf-8") as f:
        call_command(
            "dumpdata",
            exclude=["contenttypes", "auth.permission"],
            natural_foreign=True,
            natural_primary=True,
            indent=2,
            stdout=f,
        )

    file_size_kb = json_path.stat().st_size / 1024
    print(f"[+] JSON Backup complete! File size: {file_size_kb:.2f} KB")

    # 2. If MySQL and mysqldump is available, also attempt raw SQL dump
    if "mysql" in engine and shutil.which("mysqldump"):
        sql_path = backup_dir / f"mysql_raw_dump_{timestamp}.sql"
        print(f"[*] Attempting mysqldump to: {sql_path}")
        user = db_config.get("USER", "")
        password = db_config.get("PASSWORD", "")
        host = db_config.get("HOST", "localhost")
        port = str(db_config.get("PORT", "3306"))
        db_name = db_config.get("NAME", "")

        cmd = [
            "mysqldump",
            f"--host={host}",
            f"--port={port}",
            f"--user={user}",
            f"--password={password}",
            "--single-transaction",
            "--quick",
            "--routines",
            "--triggers",
            db_name,
        ]
        try:
            with open(sql_path, "w", encoding="utf-8") as out:
                subprocess.run(cmd, stdout=out, check=True)
            print(f"[+] Raw MySQL dump created: {sql_path}")
        except Exception as e:
            print(f"[!] Note: mysqldump execution skipped or failed: {e}")

    print("\n[SUCCESS] Backup successfully preserved. Original database was untouched.")
    return json_path


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else None
    run_backup(out)
