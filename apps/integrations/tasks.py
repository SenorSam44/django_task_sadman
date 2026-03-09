from typing import Dict
from celery import shared_task
from django.utils import timezone

from apps.bookings.models import BookingSystem
from .sync import DataSyncHandler


@shared_task(bind=True, max_retries=3)
def sync_booking_system_task(self, booking_system_id: int) -> Dict:
    bs = None
    try:
        bs = BookingSystem.objects.get(id=booking_system_id)
        bs.sync_status = "in_progress"
        bs.save()

        handler = DataSyncHandler(bs)
        summary = handler.sync_all()

        bs.last_synced_at = timezone.now()
        bs.sync_status = "ok"
        bs.save()
        return summary

    except Exception as e:
        if bs:
            bs.sync_status = f"error: {str(e)}"
            bs.save()

        # Retry with exponential backoff
        countdown = 60 * 2**self.request.retries
        raise self.retry(exc=e, countdown=countdown)


@shared_task(bind=True, max_retries=3)
def sync_providers_task(self, booking_system_id: int) -> int:
    try:
        bs = BookingSystem.objects.get(id=booking_system_id)
        return DataSyncHandler(bs).sync_providers()
    except Exception as e:
        countdown = 60 * 2**self.request.retries
        raise self.retry(exc=e, countdown=countdown)


@shared_task(bind=True, max_retries=3)
def sync_appointments_task(self, booking_system_id: int) -> int:
    try:
        bs = BookingSystem.objects.get(id=booking_system_id)
        return DataSyncHandler(bs).sync_appointments()
    except Exception as e:
        countdown = 60 * 2**self.request.retries
        raise self.retry(exc=e, countdown=countdown)


@shared_task
def sync_active_booking_systems() -> None:
    """
    Fire off sync tasks for all active booking systems.
    This avoids blocking by not calling `.get()`.
    """
    for bs in BookingSystem.objects.filter(is_active=True):
        sync_booking_system_task.delay(bs.id)