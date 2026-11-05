"""Seed demo invoices, payments and expenses so the statistics chart has data.

Usage: python manage.py seed_statistics [--clear] [--seed 1]
Seeded rows carry the tag "[seed-stats]" so --clear can remove them.
"""
from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.clients.models import Client
from apps.expenses.models import Expense, ExpenseCategory, ExpenseMainCategory
from apps.invoices.models import Invoice, Payment

TAG = "[seed-stats]"
NAMES = ["محمد السيد", "أحمد حسين", "علي منصور", "خالد سالم", "يوسف عثمان", "كريم زكي"]
METHODS = [Payment.Method.CASH, Payment.Method.INSTAPAY, Payment.Method.WALLET]


class Command(BaseCommand):
    help = "Create demo invoices/payments/expenses over the last 12 months."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true")
        parser.add_argument("--seed", type=int, default=1)

    @transaction.atomic
    def handle(self, *args, **opts):
        # Hard-delete previously seeded rows (children first: FKs are PROTECT).
        Payment.all_objects.filter(notes__startswith=TAG).delete()
        Expense.all_objects.filter(description__startswith=TAG).delete()
        Invoice.all_objects.filter(notes__startswith=TAG).delete()
        Client.all_objects.filter(note__startswith=TAG).delete()
        if opts["clear"]:
            self.stdout.write("Removed previously seeded statistics data.")
            return

        rng = random.Random(opts["seed"])
        today = timezone.localdate()

        clients = [
            Client.objects.create(name=n, phone=f"0109{i:07d}", note=TAG)
            for i, n in enumerate(NAMES, start=1)
        ]
        main, _ = ExpenseMainCategory.objects.get_or_create(name="مصروفات تشغيل")
        cats = [
            ExpenseCategory.objects.get_or_create(main_category=main, name=n)[0]
            for n in ("خامات", "مرتبات", "نقل")
        ]

        n_inv = n_pay = n_exp = 0
        for back in range(0, 365):
            day = today - timedelta(days=back)
            # busier recently so the current month looks alive
            chance = 0.7 if back < 31 else 0.18
            if rng.random() < chance:
                total = Decimal(rng.randrange(800, 9000, 50))
                n_inv += 1
                inv = Invoice.objects.create(
                    number=f"SEED-{day:%Y%m%d}-{n_inv}",
                    client=rng.choice(clients),
                    issue_date=day,
                    status=Invoice.Status.CONFIRMED,
                    subtotal=total,
                    total=total,
                    notes=TAG,
                )
                paid = (total * Decimal(rng.choice([0.3, 0.5, 1]))).quantize(Decimal("1"))
                Payment.objects.create(
                    client=inv.client, invoice=inv, amount=paid, paid_at=day,
                    method=rng.choice(METHODS), notes=TAG,
                )
                n_pay += 1
            if rng.random() < chance:
                Payment.objects.create(
                    client=rng.choice(clients),
                    amount=Decimal(rng.randrange(200, 3000, 50)),
                    paid_at=day, method=rng.choice(METHODS), notes=TAG,
                )
                n_pay += 1
            if rng.random() < chance:
                Expense.objects.create(
                    amount=Decimal(rng.randrange(100, 2500, 50)),
                    description=f"{TAG} مصروف",
                    expense_date=day,
                    category=rng.choice(cats),
                )
                n_exp += 1
        self.stdout.write(
            f"Seeded {n_inv} invoices, {n_pay} payments, {n_exp} expenses."
        )
