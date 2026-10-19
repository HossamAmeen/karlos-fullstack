from celery import shared_task

from .backup import create_backup


@shared_task(ignore_result=False)
def backup_database() -> str:
    return str(create_backup())
