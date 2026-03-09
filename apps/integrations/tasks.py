import logging
from typing import Dict

from celery import shared_task
from django.utils import timezone

from apps.bookings.models import BookingSystem
from .sync import DataSyncHandler

logger = logging.getLogger(__name__)

# Max length of BookingSystem.sync_status field is 50 chars
_STATUS_MAX = 50


def _truncate_error(exc: Exception) -> str:
    """Build a safe sync_status error string that fits in 50 chars."""
    msg = f"error: {str(exc)}"
    return msg[:_STATUS_MAX]


@shared_task(bind=True, max_retries=3)
def sync_booking_system_task(self, booking_system_id: int) -> Dict:
    """
    Full sync in dependency order: providers → customers → services → appointments.
    Updates last_synced_at only if ALL steps succeed.
    On failure: logs, sets sync_status='error: ...', stops chain.
    """
    bs = None
    try:
        bs = BookingSystem.objects.get(id=booking_system_id)
        bs.sync_status = "in_progress"
        bs.save(update_fields=["sync_status"])

        handler = DataSyncHandler(bs)

        # Steps must run in order — appointments depend on the others existing
        summary: Dict = {}
        summary["providers"] = handler.sync_providers()
        summary["customers"] = handler.sync_customers()
        summary["services"] = handler.sync_services()
        summary["appointments"] = handler.sync_appointments()

        # Only mark success after ALL steps complete
        bs.last_synced_at = timezone.now()
        bs.sync_status = "ok"
        bs.save(update_fields=["last_synced_at", "sync_status"])

        logger.info(
            "Sync complete for booking system %s: %s", booking_system_id, summary
        )
        return summary

    except Exception as exc:
        logger.exception("Sync failed for booking system %s", booking_system_id)
        if bs is not None:
            bs.sync_status = _truncate_error(exc)
            bs.save(update_fields=["sync_status"])
        # Exponential backoff: 60s, 120s, 240s
        countdown = 60 * (2**self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)


@shared_task(bind=True, max_retries=3)
def sync_providers_task(self, booking_system_id: int) -> int:
    """Sync only providers for a given booking system."""
    try:
        bs = BookingSystem.objects.get(id=booking_system_id)
        return DataSyncHandler(bs).sync_providers()
    except Exception as exc:
        logger.exception(
            "sync_providers_task failed for booking system %s", booking_system_id
        )
        countdown = 60 * (2**self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)


@shared_task(bind=True, max_retries=3)
def sync_appointments_task(self, booking_system_id: int) -> int:
    """Sync only appointments for a given booking system."""
    try:
        bs = BookingSystem.objects.get(id=booking_system_id)
        return DataSyncHandler(bs).sync_appointments()
    except Exception as exc:
        logger.exception(
            "sync_appointments_task failed for booking system %s", booking_system_id
        )
        countdown = 60 * (2**self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)


@shared_task
def sync_active_booking_systems() -> None:
    """
    Beat task: fires sync_booking_system_task for every active booking system.
    Registered in settings.CELERY_BEAT_SCHEDULE — runs every 6 hours.
    """
    ids = BookingSystem.objects.filter(is_active=True).values_list("id", flat=True)
    for bs_id in ids:
        sync_booking_system_task.delay(bs_id)
    logger.info("Queued sync for %d active booking system(s)", len(ids))
