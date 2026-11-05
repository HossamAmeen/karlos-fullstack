from decimal import Decimal

from django.contrib.auth.models import AbstractBaseUser

from apps.clients.models import Client


def _normalize_optional(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


# A deposit settles the last invoice if it exceeds the remaining by less than this.
AUTO_SETTLE_LIMIT = Decimal("50")


class ClientService:
    @staticmethod
    def create(
        *,
        name: str,
        phone: str,
        email: str | None = None,
        address: str | None = None,
        note: str | None = None,
        created_by: AbstractBaseUser | None = None,
        updated_by: AbstractBaseUser | None = None,
    ) -> Client:
        return Client.objects.create(
            name=name.strip(),
            phone=phone.strip(),
            email=_normalize_optional(email),
            address=_normalize_optional(address),
            note=_normalize_optional(note),
            created_by=created_by,
            updated_by=updated_by if updated_by is not None else created_by,
        )

    @staticmethod
    def update(
        *,
        client: Client,
        name: str,
        phone: str,
        email: str | None = None,
        address: str | None = None,
        note: str | None = None,
        updated_by: AbstractBaseUser | None = None,
    ) -> Client:
        client.name = name.strip()
        client.phone = phone.strip()
        client.email = _normalize_optional(email)
        client.address = _normalize_optional(address)
        client.note = _normalize_optional(note)
        if updated_by is not None:
            client.updated_by = updated_by  # type: ignore[assignment]
        client.save(
            update_fields=[
                "name",
                "phone",
                "email",
                "address",
                "note",
                "updated_by",
                "updated_at",
            ]
        )
        return client

    @staticmethod
    def delete(*, client: Client) -> None:
        client.delete()

    @staticmethod
    def record_deposit(
        *,
        client: Client,
        amount,
        paid_at=None,
        notes: str = "",
        method: str = "cash",
        invoice=None,
        created_by: AbstractBaseUser | None = None,
        updated_by: AbstractBaseUser | None = None,
    ):
        from apps.invoices.models import Invoice
        from apps.invoices.services import PaymentService
        from apps.services.pricing import quantize_money

        if invoice is None:
            # A standalone deposit settles the client's latest confirmed invoice
            # when it covers the remaining amount by less than AUTO_SETTLE_LIMIT.
            last = (
                Invoice.objects.filter(
                    client=client, status=Invoice.Status.CONFIRMED
                )
                .order_by("-issue_date", "-id")
                .first()
            )
            amt = quantize_money(Decimal(str(amount)))
            if last is not None and last.amount_remaining > 0:
                remaining = last.amount_remaining
                surplus = amt - remaining
                if 0 <= surplus < AUTO_SETTLE_LIMIT:
                    payment = PaymentService.record(
                        client=client,
                        amount=remaining,
                        invoice=last,
                        paid_at=paid_at,
                        notes=notes,
                        method=method,
                        created_by=created_by,
                        updated_by=updated_by,
                    )
                    if surplus > 0:  # keep the small excess as client credit
                        PaymentService.record(
                            client=client,
                            amount=surplus,
                            paid_at=paid_at,
                            notes=notes,
                            method=method,
                            created_by=created_by,
                            updated_by=updated_by,
                        )
                    return payment

        return PaymentService.record(
            client=client,
            amount=amount,
            invoice=invoice,
            paid_at=paid_at,
            notes=notes,
            method=method,
            created_by=created_by,
            updated_by=updated_by,
        )
