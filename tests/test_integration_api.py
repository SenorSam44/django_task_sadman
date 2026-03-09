import pytest
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.urls import reverse
from apps.bookings.models import BookingSystem, Provider, Customer, Service, Appointment
from django.utils import timezone
from datetime import timedelta

@pytest.mark.django_db
class TestAPIEndpoints(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.defaults['HTTP_ACCEPT'] = 'application/json'
        self.bs = BookingSystem.objects.create(
            name="Test System",
            base_url="http://test.com",
            credentials={"username": "test", "password": "test"},
            last_synced_at=timezone.now(),
            sync_status="ok"
        )
        self.provider = Provider.objects.create(
            booking_system=self.bs,
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            phone="123456",
            external_id="1"
        )
        self.customer = Customer.objects.create(
            booking_system=self.bs,
            first_name="Jane",
            last_name="Smith",
            email="jane@test.com",
            phone="654321",
            external_id="1"
        )
        self.service = Service.objects.create(
            booking_system=self.bs,
            name="Haircut",
            duration_minutes=30,
            price=20.00,
            currency="USD",
            external_id="1"
        )
        start_time = timezone.now()
        self.appointment = Appointment.objects.create(
            booking_system=self.bs,
            provider=self.provider,
            customer=self.customer,
            service=self.service,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=30),
            external_id="1"
        )
        self.connect_url = reverse('connect')
        self.status_url = reverse('status', kwargs={'id': self.bs.id})
        self.providers_url = reverse('providers', kwargs={'id': self.bs.id})
        self.customers_url = reverse('customers', kwargs={'id': self.bs.id})
        self.services_url = reverse('services', kwargs={'id': self.bs.id})
        self.appointments_url = reverse('appointments', kwargs={'id': self.bs.id})

    def test_connect_post_valid(self):
        data = {"name": "New System", "base_url": "http://new.com", "username": "admin", "password": "admin123"}
        response = self.client.post(self.connect_url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['name'] == "New System"
        assert response.data['errors'] == []
        assert response.data['meta'] is None
        assert BookingSystem.objects.filter(name="New System").exists()

    def test_connect_post_invalid(self):
        data = {"name": "Invalid"}
        response = self.client.post(self.connect_url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        print(response.data)
        assert response.data['data'] is None
        assert len(response.data['errors']) == 3  # base_url, username, password
        assert response.data['meta'] is None

    def test_status_get(self):
        response = self.client.get(self.status_url)
        assert response.status_code == status.HTTP_200_OK
        print(response.data)
        # assert response.data['data']['connection_status'] == "ok"
        # assert response.data['data']['record_counts']['providers'] == 1
        assert response.data['errors'] == []
        assert response.data['meta'] is None

    def test_status_get_invalid_id(self):
        invalid_url = reverse('status', kwargs={'id': 999})
        response = self.client.get(invalid_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        print(response)
        assert response.data['data'] is None
        assert len(response.data['errors']) == 1
        assert 'No BookingSystem matches' in response.data['errors'][0]['message']
        assert response.data['meta'] is None

    def test_providers_list(self):
        response = self.client.get(self.providers_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['name'] == "John Doe"
        assert response.data['meta']['total_count'] == 1
        assert response.data['errors'] == []

    def test_providers_search(self):
        response = self.client.get(f"{self.providers_url}?search=John")
        assert len(response.data['data']) == 1
        response = self.client.get(f"{self.providers_url}?search=Nonexistent")
        assert len(response.data['data']) == 0

    def test_customers_list(self):
        response = self.client.get(self.customers_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['name'] == "Jane Smith"

    def test_customers_search(self):
        response = self.client.get(f"{self.customers_url}?search=Jane")
        assert len(response.data['data']) == 1
        response = self.client.get(f"{self.customers_url}?search=Nonexistent")
        assert len(response.data['data']) == 0

    def test_services_list(self):
        response = self.client.get(self.services_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['name'] == "Haircut"

    def test_appointments_list(self):
        response = self.client.get(self.appointments_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1
        assert 'external_id' in response.data['data'][0]

    def test_appointments_filter_date(self):
        today = timezone.now().date().isoformat()
        tomorrow = (timezone.now().date() + timedelta(days=1)).isoformat()
        response = self.client.get(f"{self.appointments_url}?start_date={today}&end_date={tomorrow}")
        assert len(response.data['data']) == 1
        past_date = (timezone.now().date() - timedelta(days=1)).isoformat()
        response = self.client.get(f"{self.appointments_url}?start_date={past_date}&end_date={past_date}")
        assert len(response.data['data']) == 0

    def test_pagination(self):
        for i in range(25):
            Provider.objects.create(
                booking_system=self.bs,
                first_name=f"Test{i}",
                last_name="User",
                email=f"test{i}@test.com",
                external_id=str(i+2)
            )
        response = self.client.get(f"{self.providers_url}?page=1")
        print(f"pagination: {response.data}")
        assert len(response.data['data']) == 20
        assert response.data['meta']['total_pages'] > 1
