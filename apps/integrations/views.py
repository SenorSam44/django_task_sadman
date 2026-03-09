import logging
from datetime import datetime, timedelta

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.timezone import make_aware
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Appointment, BookingSystem, Customer, Provider, Service
from .client import BookingSystemClient
from .serializers import (
    AppointmentSerializer,
    BookingSystemSerializer,
    ConnectSerializer,
    CustomerSerializer,
    ProviderSerializer,
    ServiceSerializer,
)
from .tasks import sync_booking_system_task

logger = logging.getLogger(__name__)


class ConnectView(APIView):
    """
    POST /api/booking-systems/connect/
    Registers a new booking system after verifying credentials work.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ConnectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "data": None,
                    "errors": [{"message": str(v)} for v in serializer.errors.values()],
                    "meta": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        # Test the connection BEFORE persisting — fail fast with a clear error
        client = BookingSystemClient(
            data["base_url"], data["username"], data["password"]
        )
        if not client.test_connection():
            return Response(
                {
                    "data": None,
                    "errors": [
                        {
                            "message": "Could not connect to the booking system. Check base_url and credentials."
                        }
                    ],
                    "meta": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        bs = BookingSystem.objects.create(
            name=data["name"],
            base_url=data["base_url"],
            credentials={"username": data["username"], "password": data["password"]},
        )
        return Response(
            {"data": BookingSystemSerializer(bs).data, "errors": [], "meta": None},
            status=status.HTTP_201_CREATED,
        )


class StatusView(APIView):
    """GET /api/booking-systems/{id}/status/"""

    permission_classes = [AllowAny]

    def get(self, request, id):
        bs = get_object_or_404(BookingSystem, id=id)
        data = {
            "connection_status": bs.sync_status,
            "last_synced_at": bs.last_synced_at,
            "record_counts": {
                "providers": bs.providers.count(),
                "customers": bs.customers.count(),
                "services": bs.services.count(),
                "appointments": bs.appointments.count(),
            },
        }
        return Response(data)


class ProviderListView(generics.ListAPIView):
    """GET /api/booking-systems/{id}/providers/?search=name"""

    serializer_class = ProviderSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        bs = get_object_or_404(BookingSystem, id=self.kwargs["id"])
        qs = bs.providers.all()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) | Q(last_name__icontains=search)
            )
        return qs.order_by("id")


class CustomerListView(generics.ListAPIView):
    """GET /api/booking-systems/{id}/customers/?search=name"""

    serializer_class = CustomerSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        bs = get_object_or_404(BookingSystem, id=self.kwargs["id"])
        qs = bs.customers.all()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) | Q(last_name__icontains=search)
            )
        return qs.order_by("id")


class ServiceListView(generics.ListAPIView):
    """GET /api/booking-systems/{id}/services/"""

    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        bs = get_object_or_404(BookingSystem, id=self.kwargs["id"])
        return bs.services.all().order_by("id")


class AppointmentListView(generics.ListAPIView):
    """GET /api/booking-systems/{id}/appointments/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD"""

    serializer_class = AppointmentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        bs = get_object_or_404(BookingSystem, id=self.kwargs["id"])
        qs = bs.appointments.all()
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        if start_date:
            try:
                qs = qs.filter(
                    start_time__gte=make_aware(
                        datetime.strptime(start_date, "%Y-%m-%d")
                    )
                )
            except ValueError:
                pass
        if end_date:
            try:
                # Include the full end day
                end_dt = make_aware(
                    datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                ) - timedelta(seconds=1)
                qs = qs.filter(start_time__lte=end_dt)
            except ValueError:
                pass
        return qs.order_by("id")


class SyncTriggerView(APIView):
    """
    POST /api/booking-systems/{id}/sync/
    Triggers a full async sync. Returns the Celery task ID immediately.
    """

    permission_classes = [AllowAny]

    def post(self, request, id):
        bs = get_object_or_404(BookingSystem, id=id)
        if not bs.is_active:
            return Response(
                {
                    "data": None,
                    "errors": [{"message": "Booking system is inactive."}],
                    "meta": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        task = sync_booking_system_task.delay(bs.id)
        logger.info(
            "Manual sync triggered for booking system %s, task_id=%s", id, task.id
        )
        return Response(
            {"data": {"task_id": task.id}, "errors": [], "meta": None},
            status=status.HTTP_202_ACCEPTED,
        )


class SyncStatusView(APIView):
    """
    GET /api/booking-systems/{id}/sync/status/
    Returns current sync status and last error info.
    """

    permission_classes = [AllowAny]

    def get(self, request, id):
        bs = get_object_or_404(BookingSystem, id=id)
        return Response(
            {
                "data": {
                    "sync_status": bs.sync_status,
                    "last_synced_at": bs.last_synced_at,
                    "is_active": bs.is_active,
                },
                "errors": [],
                "meta": None,
            }
        )
