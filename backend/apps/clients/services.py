from django.contrib.auth.models import AbstractBaseUser

from apps.clients.models import Client


def _normalize_optional(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


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
        created_by: AbstractBaseUser | None = None,
        updated_by: AbstractBaseUser | None = None,
    ):
        from apps.invoices.services import PaymentService

        return PaymentService.record(
            client=client,
            amount=amount,
            invoice=None,
            paid_at=paid_at,
            notes=notes,
            created_by=created_by,
            updated_by=updated_by,
        )
