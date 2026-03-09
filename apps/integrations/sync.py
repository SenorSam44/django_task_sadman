import logging
from typing import Any, Dict

from django.db import transaction
from django.utils import timezone

from apps.bookings.models import Appointment, BookingSystem, Customer, Provider, Service
from .client import BookingSystemClient

logger = logging.getLogger(__name__)


class DataSyncHandler:
    def __init__(self, booking_system: BookingSystem) -> None:
        self.booking_system = booking_system
        self.client = BookingSystemClient(
            booking_system.base_url,
            booking_system.credentials.get("username", ""),
            booking_system.credentials.get("password", ""),
        )

    def _coerce_null(self, value: Any, default: Any = "") -> Any:
        """Coerce None to a safe default to avoid DB constraint violations."""
        return value if value is not None else default

    def _extra_data(self, item: Dict, exclude_keys: list) -> Dict:
        """Extract remaining fields into extra_data."""
        return {k: v for k, v in item.items() if k not in exclude_keys}

    def sync_all(self) -> Dict[str, int]:
        """Run full sync in dependency order. Returns per-entity counts."""
        summary: Dict[str, int] = {}
        summary["providers"] = self.sync_providers()
        summary["customers"] = self.sync_customers()
        summary["services"] = self.sync_services()
        summary["appointments"] = self.sync_appointments()
        return summary

    def sync_providers(self) -> int:
        """
        Sync providers with per-record transaction safety.
        Each record is wrapped individually so one failure never rolls back others.
        """
        data = self.client.get_providers()
        count = 0
        for item in data:
            try:
                with transaction.atomic():
                    Provider.objects.update_or_create(
                        booking_system=self.booking_system,
                        external_id=str(item["id"]),
                        defaults={
                            "first_name": self._coerce_null(item.get("firstName")),
                            "last_name": self._coerce_null(item.get("lastName")),
                            "email": self._coerce_null(item.get("email")),
                            "phone": self._coerce_null(item.get("phone")),
                            "extra_data": self._extra_data(
                                item, ["id", "firstName", "lastName", "email", "phone"]
                            ),
                        },
                    )
                    count += 1
            except Exception:
                logger.exception("Failed to sync provider %s", item.get("id"))
        return count

    def sync_customers(self) -> int:
        """Sync customers with per-record transaction safety."""
        data = self.client.get_customers()
        count = 0
        for item in data:
            try:
                with transaction.atomic():
                    Customer.objects.update_or_create(
                        booking_system=self.booking_system,
                        external_id=str(item["id"]),
                        defaults={
                            "first_name": self._coerce_null(item.get("firstName")),
                            "last_name": self._coerce_null(item.get("lastName")),
                            "email": self._coerce_null(item.get("email")),
                            "phone": self._coerce_null(item.get("phone")),
                            "extra_data": self._extra_data(
                                item, ["id", "firstName", "lastName", "email", "phone"]
                            ),
                        },
                    )
                    count += 1
            except Exception:
                logger.exception("Failed to sync customer %s", item.get("id"))
        return count

    def sync_services(self) -> int:
        """Sync services with per-record transaction safety."""
        data = self.client.get_services()
        count = 0
        for item in data:
            try:
                with transaction.atomic():
                    Service.objects.update_or_create(
                        booking_system=self.booking_system,
                        external_id=str(item["id"]),
                        defaults={
                            "name": self._coerce_null(item.get("name")),
                            # FIX: correct field name is duration_minutes, API field is duration
                            "duration_minutes": self._coerce_null(
                                item.get("duration"), 0
                            ),
                            "price": self._coerce_null(item.get("price"), 0),
                            "currency": self._coerce_null(item.get("currency"), "USD"),
                            "extra_data": self._extra_data(
                                item, ["id", "name", "duration", "price", "currency"]
                            ),
                        },
                    )
                    count += 1
            except Exception:
                logger.exception("Failed to sync service %s", item.get("id"))
        return count

    def sync_appointments(self) -> int:
        """
        Sync appointments with per-record transaction safety.
        Skips any appointment whose provider, customer, or service isn't locally present.
        """
        data = self.client.get_appointments()
        count = 0
        for item in data:
            try:
                provider = Provider.objects.filter(
                    booking_system=self.booking_system,
                    external_id=str(item.get("providerId")),
                ).first()
                customer = Customer.objects.filter(
                    booking_system=self.booking_system,
                    external_id=str(item.get("customerId")),
                ).first()
                service = Service.objects.filter(
                    booking_system=self.booking_system,
                    external_id=str(item.get("serviceId")),
                ).first()

                if not (provider and customer and service):
                    logger.warning(
                        "Skipping appointment %s — missing provider=%s customer=%s service=%s",
                        item.get("id"),
                        provider,
                        customer,
                        service,
                    )
                    continue

                with transaction.atomic():
                    Appointment.objects.update_or_create(
                        booking_system=self.booking_system,
                        external_id=str(item["id"]),
                        defaults={
                            "provider": provider,
                            "customer": customer,
                            "service": service,
                            "start_time": item.get("start"),
                            "end_time": item.get("end"),
                            "location": self._coerce_null(item.get("location")),
                            "status": self._coerce_null(
                                item.get("status"), "confirmed"
                            ),
                            "extra_data": self._extra_data(
                                item,
                                [
                                    "id",
                                    "providerId",
                                    "customerId",
                                    "serviceId",
                                    "start",
                                    "end",
                                    "location",
                                    "status",
                                ],
                            ),
                        },
                    )
                    count += 1
            except Exception:
                logger.exception("Failed to sync appointment %s", item.get("id"))
        return count
