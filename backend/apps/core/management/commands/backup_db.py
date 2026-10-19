from django.core.management.base import BaseCommand, CommandError

from apps.core.backup import BackupError, celery_available, run_backup


class Command(BaseCommand):
    help = "Back up the database. Uses Celery if configured and reachable, else runs inline."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sync", action="store_true", help="Skip Celery and run the backup now."
        )

    def handle(self, *args, **options):
        if options["sync"]:
            self.stdout.write("Running backup inline (--sync).")
        elif celery_available():
            self.stdout.write("Celery found: queueing backup task.")
        else:
            self.stdout.write("Celery not configured or unreachable: running inline.")
        try:
            result = run_backup(force_sync=options["sync"])
        except BackupError as exc:
            raise CommandError(str(exc))
        if result["mode"] == "celery":
            self.stdout.write(self.style.SUCCESS(f"Queued task {result['task_id']}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Backup created: {result['file']}"))
