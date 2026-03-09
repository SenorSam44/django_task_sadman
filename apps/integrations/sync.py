from typing import Dict, Any
from django.db import transaction, IntegrityError
from django.utils import timezone
import logging

from apps.bookings.models import BookingSystem, Provider, Customer, Appointment, Service
from .client import BookingSystemClient

logger = logging.getLogger(__name__)


class DataSyncHandler:
    def __init__(self, booking_system: BookingSystem):
        self.booking_system = booking_system
        self.client = BookingSystemClient(
            booking_system.base_url,
            booking_system.credentials.get("username", ""),
            booking_system.credentials.get("password", ""),
        )

    def _coerce_null(self, value: Any, default: Any = "") -> Any:
        return value if value is not None else default

    def sync_all(self) -> dict:
        summary = {}

        summary["providers"] = self.sync_providers()
        summary["customers"] = self.sync_customers()
        summary["services"] = self.sync_services()
        summary["appointments"] = self.sync_appointments()

        return summary

    @transaction.atomic
    def sync_providers(self) -> int:
        data = self.client.get_providers()
        count = 0
        for item in data:
            try:
                Provider.objects.update_or_create(
                    booking_system=self.booking_system,
                    external_id=item["id"],
                    defaults={
                        "first_name": self._coerce_null(item.get("firstName")),
                        "last_name": self._coerce_null(item.get("lastName")),
                        "email": self._coerce_null(item.get("email")),
                        "phone": self._coerce_null(item.get("phone")),
                        "extra_data": {
                            k: v
                            for k, v in item.items()
                            if k
                            not in ["id", "firstName", "lastName", "email", "phone"]
                        },
                    },
                )
                count += 1
            except IntegrityError as e:
                logger.warning(f"Failed to sync provider {item['id']}: {e}")
        return count

    @transaction.atomic
    def sync_customers(self) -> int:
        customers = self.client.get_customers()
        count = 0

        for c in customers:
            try:
                Customer.objects.update_or_create(
                    booking_system=self.booking_system,
                    external_id=str(c["id"]),
                    defaults={
                        "first_name": c.get("firstName") or "",
                        "last_name": c.get("lastName") or "",
                        "email": c.get("email") or "",
                        "phone": c.get("phone") or "",
                    },
                )
                count += 1
            except Exception:
                logger.exception("Failed syncing customer %s", c.get("id"))

        return count

    @transaction.atomic
    def sync_services(self) -> int:
        services = self.client.get_services()
        count = 0

        for s in services:
            try:
                Service.objects.update_or_create(
                    booking_system=self.booking_system,
                    external_id=str(s["id"]),
                    defaults={
                        "name": s.get("name") or "",
                        "duration": s.get("duration") or 0,
                        "price": s.get("price") or 0,
                    },
                )
                count += 1
            except Exception:
                logger.exception("Failed syncing service %s", s.get("id"))

        return count

    @transaction.atomic
    def sync_appointments(self) -> int:
        appointments = self.client.get_appointments()
        count = 0

        for a in appointments:
            try:
                provider = Provider.objects.filter(
                    booking_system=self.booking_system,
                    external_id=str(a.get("providerId")),
                ).first()

                customer = Customer.objects.filter(
                    booking_system=self.booking_system,
                    external_id=str(a.get("customerId")),
                ).first()

                service = Service.objects.filter(
                    booking_system=self.booking_system,
                    external_id=str(a.get("serviceId")),
                ).first()

                if not (provider and customer and service):
                    logger.warning(
                        "Skipping appointment %s due to missing relations",
                        a.get("id"),
                    )
                    continue

                Appointment.objects.update_or_create(
                    booking_system=self.booking_system,
                    external_id=str(a["id"]),
                    defaults={
                        "provider": provider,
                        "customer": customer,
                        "service": service,
                        "start_time": a.get("start"),
                        "end_time": a.get("end"),
                    },
                )

                count += 1

            except Exception:
                logger.exception("Failed syncing appointment %s", a.get("id"))

        return count