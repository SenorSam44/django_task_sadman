import pytest
from unittest.mock import patch
from django.test import TestCase
from apps.bookings.models import BookingSystem
from apps.integrations.sync import DataSyncHandler


@pytest.mark.django_db
class TestDataSyncHandler(TestCase):
    @patch('core.sync.BookingSystemClient')
    def test_sync_providers(self, mock_client):
        bs = BookingSystem.objects.create(name='Test', base_url='http://test', credentials={})
        mock_client.return_value.get_providers.return_value = [
            {'id': '1', 'firstName': 'John', 'lastName': 'Doe', 'email': 'j@d.com', 'phone': None}
        ]
        handler = DataSyncHandler(bs)
        count = handler.sync_providers()
        assert count == 1
        assert bs.providers.count() == 1
        prov = bs.providers.first()
        assert prov.phone == ''  # Coerced null
