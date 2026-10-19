import shutil
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db import connection


class BackupError(Exception):
    pass


def backup_dir() -> Path:
    path = Path(settings.BACKUP_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_backup() -> Path:
    """Dump the default database into BACKUP_DIR and return the file path."""
    db = settings.DATABASES["default"]
    engine = db["ENGINE"]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    if engine.endswith("sqlite3"):
        target = backup_dir() / f"backup-{stamp}.sqlite3"
        source = sqlite3.connect(str(db["NAME"]))
        try:
            dest = sqlite3.connect(str(target))
            try:
                source.backup(dest)
            finally:
                dest.close()
        finally:
            source.close()
        return target

    if "postgresql" in engine:
        if shutil.which("pg_dump") is None:
            raise BackupError("pg_dump is not installed on the server.")
        target = backup_dir() / f"backup-{stamp}.sql"
        params = connection.get_connection_params()
        cmd = ["pg_dump", "--no-owner", "--file", str(target)]
        env = None
        if params.get("host"):
            cmd += ["--host", str(params["host"])]
        if params.get("port"):
            cmd += ["--port", str(params["port"])]
        if params.get("user"):
            cmd += ["--username", str(params["user"])]
        if params.get("password"):
            env = {"PGPASSWORD": str(params["password"]), "PATH": "/usr/bin:/bin:/usr/local/bin"}
        cmd.append(str(params.get("dbname") or db["NAME"]))
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            target.unlink(missing_ok=True)
            raise BackupError(result.stderr.strip() or "pg_dump failed.")
        return target

    raise BackupError(f"Unsupported database engine: {engine}")


def celery_available() -> bool:
    """True when a Celery broker is configured in the env and reachable."""
    if not getattr(settings, "CELERY_CONFIGURED", False):
        return False
    try:
        from config.celery import app

        with app.connection_for_write() as conn:
            conn.ensure_connection(max_retries=1, timeout=2)
        return True
    except Exception:
        return False


def run_backup(*, force_sync: bool = False) -> dict:
    """Queue the backup on Celery when available, otherwise run it inline."""
    if not force_sync and celery_available():
        from .tasks import backup_database

        result = backup_database.delay()
        return {"mode": "celery", "task_id": result.id}
    return {"mode": "sync", "file": create_backup().name}
