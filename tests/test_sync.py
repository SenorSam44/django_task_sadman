import pytest
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.bookings.models import BookingSystem, Provider, Customer, Service, Appointment
from apps.integrations.sync import DataSyncHandler


@pytest.mark.django_db
class TestDataSyncHandler(TestCase):

    def _make_bs(self) -> BookingSystem:
        return BookingSystem.objects.create(
            name="Test",
            base_url="http://test",
            credentials={"username": "u", "password": "p"},
        )

    # ── Provider sync ────────────────────────────────────────────────────────

    @patch("apps.integrations.sync.BookingSystemClient")
    def test_sync_providers_creates_record(self, MockClient):
        bs = self._make_bs()
        MockClient.return_value.get_providers.return_value = [
            {
                "id": "1",
                "firstName": "John",
                "lastName": "Doe",
                "email": "j@d.com",
                "phone": None,  # null should be coerced to ""
            }
        ]
        handler = DataSyncHandler(bs)
        count = handler.sync_providers()

        assert count == 1
        assert bs.providers.count() == 1
        prov = bs.providers.first()
        assert prov.phone == ""  # FIX: null coerced to empty string
        assert prov.external_id == "1"

    @patch("apps.integrations.sync.BookingSystemClient")
    def test_sync_providers_upserts(self, MockClient):
        """Re-running sync updates the existing record rather than duplicating it."""
        bs = self._make_bs()
        provider_data = [
            {
                "id": "1",
                "firstName": "John",
                "lastName": "Doe",
                "email": "j@d.com",
                "phone": "",
            }
        ]
        MockClient.return_value.get_providers.return_value = provider_data
        handler = DataSyncHandler(bs)
        handler.sync_providers()

        # Change the name and sync again
        provider_data[0]["firstName"] = "Jonathan"
        handler.sync_providers()

        assert bs.providers.count() == 1  # No duplicate
        assert bs.providers.first().first_name == "Jonathan"

    @patch("apps.integrations.sync.BookingSystemClient")
    def test_sync_providers_skips_bad_record_continues(self, MockClient):
        """One broken record should not roll back the others."""
        bs = self._make_bs()
        MockClient.return_value.get_providers.return_value = [
            {
                "id": "1",
                "firstName": "Good",
                "lastName": "One",
                "email": "g@o.com",
                "phone": "",
            },
            # Missing 'id' key — will raise KeyError, should be caught
            {"firstName": "Bad", "lastName": "Record", "email": None, "phone": None},
            {
                "id": "3",
                "firstName": "Also",
                "lastName": "Good",
                "email": "a@g.com",
                "phone": "",
            },
        ]
        handler = DataSyncHandler(bs)
        count = handler.sync_providers()

        # 2 good records should succeed; bad one is skipped
        assert count == 2

    # ── Service sync ─────────────────────────────────────────────────────────

    @patch("apps.integrations.sync.BookingSystemClient")
    def test_sync_services_maps_duration_correctly(self, MockClient):
        """The API field 'duration' must map to the model field 'duration_minutes'."""
        bs = self._make_bs()
        MockClient.return_value.get_services.return_value = [
            {
                "id": "10",
                "name": "Haircut",
                "duration": 30,
                "price": "25.00",
                "currency": "USD",
            }
        ]
        handler = DataSyncHandler(bs)
        count = handler.sync_services()

        assert count == 1
        svc = bs.services.first()
        assert svc.duration_minutes == 30  # Would be 0/error with old bug

    # ── Customer sync ────────────────────────────────────────────────────────

    @patch("apps.integrations.sync.BookingSystemClient")
    def test_sync_customers(self, MockClient):
        bs = self._make_bs()
        MockClient.return_value.get_customers.return_value = [
            {
                "id": "5",
                "firstName": "Alice",
                "lastName": "B",
                "email": "a@b.com",
                "phone": None,
            }
        ]
        handler = DataSyncHandler(bs)
        count = handler.sync_customers()

        assert count == 1
        cust = bs.customers.first()
        assert cust.phone == ""

    # ── Appointment sync ─────────────────────────────────────────────────────

    @patch("apps.integrations.sync.BookingSystemClient")
    def test_sync_appointments_skips_missing_relations(self, MockClient):
        """Appointments referencing non-existent providers/customers/services are skipped."""
        bs = self._make_bs()
        MockClient.return_value.get_appointments.return_value = [
            {
                "id": "100",
                "providerId": "999",  # doesn't exist
                "customerId": "999",
                "serviceId": "999",
                "start": "2026-01-10 09:00:00",
                "end": "2026-01-10 09:30:00",
                "location": "",
                "status": "confirmed",
            }
        ]
        handler = DataSyncHandler(bs)
        count = handler.sync_appointments()
        assert count == 0
        assert bs.appointments.count() == 0

    @patch("apps.integrations.sync.BookingSystemClient")
    def test_sync_appointments_full_flow(self, MockClient):
        """Happy path: all relations exist, appointment is created."""
        bs = self._make_bs()
        provider = Provider.objects.create(
            booking_system=bs,
            first_name="P",
            last_name="P",
            email="p@p.com",
            external_id="1",
        )
        customer = Customer.objects.create(
            booking_system=bs,
            first_name="C",
            last_name="C",
            email="c@c.com",
            external_id="2",
        )
        service = Service.objects.create(
            booking_system=bs,
            name="Cut",
            duration_minutes=30,
            price="20.00",
            currency="USD",
            external_id="3",
        )
        MockClient.return_value.get_appointments.return_value = [
            {
                "id": "42",
                "providerId": "1",
                "customerId": "2",
                "serviceId": "3",
                "start": "2026-01-10 09:00:00",
                "end": "2026-01-10 09:30:00",
                "location": "Main Branch",
                "status": "confirmed",
            }
        ]
        handler = DataSyncHandler(bs)
        count = handler.sync_appointments()

        assert count == 1
        appt = bs.appointments.first()
        assert appt.external_id == "42"
        assert appt.provider == provider
        assert appt.customer == customer
        assert appt.service == service
