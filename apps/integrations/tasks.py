from typing import Dict
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.utils import timezone
from retrying import retry

from .models import BookingSystem
from .sync import DataSyncHandler


@retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000)
def retry_on_failure(exception):
    return isinstance(exception, Exception)  # Broad, but as per bonus


@shared_task(bind=True, max_retries=3)
def sync_booking_system_task(self, booking_system_id: int) -> Dict:
    try:
        bs = BookingSystem.objects.get(id=booking_system_id)
        bs.sync_status = 'in_progress'
        bs.save()
        handler = DataSyncHandler(bs)
        summary = handler.sync_all()
        bs.last_synced_at = timezone.now()
        bs.sync_status = 'ok'
        bs.save()
        return summary
    except Exception as e:
        bs.sync_status = f'error: {str(e)}'
        bs.save()
        self.retry(exc=e, countdown=60 * 2 ** self.request.retries)  # Exponential

@shared_task
def sync_providers_task(booking_system_id: int) -> int:
    bs = BookingSystem.objects.get(id=booking_system_id)
    return DataSyncHandler(bs).sync_providers()

@shared_task
def sync_appointments_task(booking_system_id: int) -> int:
    bs = BookingSystem.objects.get(id=booking_system_id)
    return DataSyncHandler(bs).sync_appointments()

@shared_task
def sync_active_booking_systems() -> Dict:
    results = {}
    for bs in BookingSystem.objects.filter(is_active=True):
        summary = sync_booking_system_task.delay(bs.id).get()
        results[bs.id] = summary
    return results
