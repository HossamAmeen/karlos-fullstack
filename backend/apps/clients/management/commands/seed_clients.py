"""Seed demo clients for local development.

Usage: python manage.py seed_clients [--count 500] [--clear]
Seeded clients carry the note "[seed]" so --clear can remove them.
"""
from __future__ import annotations

import random

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.clients.models import Client

SEED_TAG = "[seed]"
FIRST = ["محمد", "أحمد", "محمود", "علي", "حسام", "عماد", "خالد", "يوسف", "إبراهيم", "مصطفى",
         "عمرو", "طارق", "سعيد", "حسن", "كريم", "ياسر", "هاني", "وليد", "أسامة", "رضا"]
LAST = ["عبدالله", "السيد", "حسين", "إسماعيل", "فتحي", "الشريف", "منصور", "البلينا", "سالم",
        "الجمل", "عثمان", "موسى", "جابر", "نصر", "زكي", "رمضان", "شحاتة", "عوض", "غنيم", "درويش"]
TRADES = ["", "", "", " للزجاج", " للألومنيوم", " للمقاولات", " للديكور"]
STREETS = ["شارع النيل", "شارع الجمهورية", "شارع الهرم", "شارع البحر", "شارع المحطة", "شارع الجلاء"]
CITIES = ["القاهرة", "الجيزة", "الإسكندرية", "سوهاج", "أسيوط", "المنيا", "طنطا"]
PREFIXES = ["010", "011", "012", "015"]


class Command(BaseCommand):
    help = "Create demo clients (default 500) with unique phone numbers."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=500)
        parser.add_argument("--clear", action="store_true", help="Hard-delete previously seeded clients first")
        parser.add_argument("--seed", type=int, default=1)

    def handle(self, *args, **opts):
        rng = random.Random(opts["seed"])
        if opts["clear"]:
            qs = Client.all_objects.filter(note__startswith=SEED_TAG)
            n = qs.count()
            qs.delete()  # all_objects is a plain manager -> hard delete
            self.stdout.write(f"Removed {n} previously seeded clients.")

        used = set(Client.objects.values_list("phone", flat=True))
        rows: list[Client] = []
        while len(rows) < opts["count"]:
            phone = rng.choice(PREFIXES) + "".join(rng.choice("0123456789") for _ in range(8))
            if phone in used:
                continue
            used.add(phone)
            name = f"{rng.choice(FIRST)} {rng.choice(LAST)}{rng.choice(TRADES)}"
            rows.append(
                Client(
                    name=name,
                    phone=phone,
                    email=f"client{len(rows) + 1}@example.com" if rng.random() < 0.3 else "",
                    address=f"{rng.choice(STREETS)}، {rng.choice(CITIES)}" if rng.random() < 0.6 else "",
                    note=SEED_TAG,
                )
            )
        with transaction.atomic():
            Client.objects.bulk_create(rows, batch_size=200)
        self.stdout.write(self.style.SUCCESS(f"Created {len(rows)} seeded clients."))
