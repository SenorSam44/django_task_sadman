from typing import Dict, Any
from django.db import transaction, IntegrityError
from django.utils import timezone
import logging

from apps.bookings.models import BookingSystem, Provider
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

    # Placeholder for sync_all (expand later)
    def sync_all(self) -> Dict[str, int]:
        summary = {"providers": self.sync_providers()}
        self.booking_system.last_synced_at = timezone.now()
        self.booking_system.sync_status = "ok"
        self.booking_system.save()
        return summary
