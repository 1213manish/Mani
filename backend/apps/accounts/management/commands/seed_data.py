"""
Seed data management command.

Creates realistic demo data:
- 4 users (Aisha, Rohan, Priya, Meera)
- 1 group (Goa Trip 2024)
- Memberships with timeline (Meera leaves March 31)
- 8 expenses with various split types
- 2 settlements
- 2 currencies (INR, USD)
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.currencies.models import Currency
from apps.groups.models import Group, GroupMembership
from apps.expenses.models import Expense, ExpenseSplit
from apps.settlements.models import Settlement

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with demo data"

    def handle(self, *args, **options):
        self.stdout.write("[*] Seeding database...")

        # 1. Create currencies
        inr, _ = Currency.objects.get_or_create(
            code="INR", defaults={"name": "Indian Rupee", "symbol": "₹"}
        )
        usd, _ = Currency.objects.get_or_create(
            code="USD", defaults={"name": "US Dollar", "symbol": "$"}
        )
        self.stdout.write("[ok] Currencies: INR, USD")

        # 2. Create users
        users_data = [
            {"email": "aisha@example.com", "username": "aisha", "first_name": "Aisha", "last_name": "Khan", "password": "demo1234!"},
            {"email": "rohan@example.com", "username": "rohan", "first_name": "Rohan", "last_name": "Sharma", "password": "demo1234!"},
            {"email": "priya@example.com", "username": "priya", "first_name": "Priya", "last_name": "Verma", "password": "demo1234!"},
            {"email": "meera@example.com", "username": "meera", "first_name": "Meera", "last_name": "Nair", "password": "demo1234!"},
        ]

        user_objs = {}
        for data in users_data:
            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "username": data["username"],
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "is_email_verified": True,
                },
            )
            if created:
                user.set_password(data["password"])
                user.save()
            user_objs[data["username"]] = user
        self.stdout.write("[ok] Users: Aisha, Rohan, Priya, Meera")

        aisha = user_objs["aisha"]
        rohan = user_objs["rohan"]
        priya = user_objs["priya"]
        meera = user_objs["meera"]

        # 3. Create group
        group, created = Group.objects.get_or_create(
            name="Goa Trip 2024",
            defaults={
                "description": "Our Goa trip in early 2024",
                "created_by": aisha,
                "default_currency": inr,
            },
        )

        # 4. Memberships with timeline
        # All join Jan 1, Meera leaves Mar 31
        GroupMembership.objects.get_or_create(
            group=group, user=aisha,
            defaults={"joined_at": date(2024, 1, 1), "role": GroupMembership.Role.ADMIN},
        )
        GroupMembership.objects.get_or_create(
            group=group, user=rohan,
            defaults={"joined_at": date(2024, 1, 1)},
        )
        GroupMembership.objects.get_or_create(
            group=group, user=priya,
            defaults={"joined_at": date(2024, 1, 1)},
        )
        # Meera: joined Jan 1, left Mar 31 — expenses after March 31 should NOT affect her
        GroupMembership.objects.get_or_create(
            group=group, user=meera,
            defaults={"joined_at": date(2024, 1, 1), "left_at": date(2024, 3, 31)},
        )
        self.stdout.write("[ok] Memberships: All joined Jan 1. Meera left Mar 31.")

        # 5. Expenses

        # Expense 1: Hotel (before Meera left) — EQUAL split among all 4
        hotel = Expense.objects.create(
            title="Hotel Stay",
            amount=Decimal("12000.00"),
            currency=inr,
            original_amount=Decimal("12000.00"),
            original_currency=inr,
            exchange_rate=Decimal("1.0"),
            converted_amount=Decimal("12000.00"),
            paid_by=aisha,
            expense_date=date(2024, 3, 15),
            group=group,
            split_type=Expense.SplitType.EQUAL,
            created_by=aisha,
        )
        per_person = Decimal("3000.0000")
        for user in [aisha, rohan, priya, meera]:
            ExpenseSplit.objects.create(
                expense=hotel, user=user,
                owed_amount=per_person, share_amount=per_person, share_percentage=Decimal("25"),
            )
        self.stdout.write("[ok] Expense 1: Hotel Rs12,000 (EQUAL, 4 members)")

        # Expense 2: Flight (PERCENTAGE split)
        flight = Expense.objects.create(
            title="Goa Flights",
            amount=Decimal("24000.00"),
            currency=inr,
            original_amount=Decimal("24000.00"),
            original_currency=inr,
            exchange_rate=Decimal("1.0"),
            converted_amount=Decimal("24000.00"),
            paid_by=rohan,
            expense_date=date(2024, 3, 10),
            group=group,
            split_type=Expense.SplitType.PERCENTAGE,
            created_by=rohan,
        )
        splits_pct = [(aisha, 30), (rohan, 30), (priya, 20), (meera, 20)]
        for user, pct in splits_pct:
            amt = Decimal("24000.00") * Decimal(str(pct)) / 100
            ExpenseSplit.objects.create(
                expense=flight, user=user,
                owed_amount=amt, share_amount=amt, share_percentage=Decimal(str(pct)),
            )
        self.stdout.write("[ok] Expense 2: Flights Rs24,000 (PERCENTAGE)")

        # Expense 3: After Meera left — only 3 members
        dinner = Expense.objects.create(
            title="Farewell Dinner",
            amount=Decimal("4500.00"),
            currency=inr,
            original_amount=Decimal("4500.00"),
            original_currency=inr,
            exchange_rate=Decimal("1.0"),
            converted_amount=Decimal("4500.00"),
            paid_by=priya,
            expense_date=date(2024, 4, 5),  # After Meera left
            group=group,
            split_type=Expense.SplitType.EQUAL,
            created_by=priya,
        )
        per_3 = Decimal("1500.0000")
        for user in [aisha, rohan, priya]:
            ExpenseSplit.objects.create(
                expense=dinner, user=user,
                owed_amount=per_3, share_amount=per_3,
            )
        self.stdout.write("[ok] Expense 3: Dinner Rs4,500 (EQUAL, 3 members - after Meera left)")

        # Expense 4: USD expense (multi-currency)
        amazon = Expense.objects.create(
            title="Amazon Supplies (USD)",
            amount=Decimal("7200.00"),  # INR
            currency=inr,
            original_amount=Decimal("86.00"),
            original_currency=usd,
            exchange_rate=Decimal("83.72093"),  # USD to INR
            converted_amount=Decimal("7200.00"),
            paid_by=aisha,
            expense_date=date(2024, 3, 20),
            group=group,
            split_type=Expense.SplitType.EQUAL,
            created_by=aisha,
        )
        per_person_usd = Decimal("1800.0000")
        for user in [aisha, rohan, priya, meera]:
            ExpenseSplit.objects.create(
                expense=amazon, user=user, owed_amount=per_person_usd, share_amount=per_person_usd
            )
        self.stdout.write("[ok] Expense 4: Amazon $86 USD (stored as Rs7,200)")

        # 6. Settlement
        Settlement.objects.create(
            group=group,
            payer=rohan,
            receiver=aisha,
            amount=Decimal("3000.00"),
            currency=inr,
            settlement_date=date(2024, 4, 10),
            notes="Rohan paid Aisha back for hotel",
            created_by=rohan,
        )
        Settlement.objects.create(
            group=group,
            payer=priya,
            receiver=rohan,
            amount=Decimal("4800.00"),
            currency=inr,
            settlement_date=date(2024, 4, 12),
            notes="Priya settled flight balance",
            created_by=priya,
        )
        self.stdout.write("[ok] Settlements: 2 recorded")

        self.stdout.write(self.style.SUCCESS(
            "\n[DONE] Demo data seeded!\n"
            "  Users: aisha@example.com, rohan@example.com, priya@example.com, meera@example.com\n"
            "  Password (all): demo1234!\n"
            "  Group: 'Goa Trip 2024'\n"
        ))
