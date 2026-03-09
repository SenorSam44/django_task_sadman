from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils.timezone import make_aware
from datetime import datetime, timedelta

from apps.bookings.models import BookingSystem, Provider, Customer, Service, Appointment
from .serializers import (
    ConnectSerializer,
    BookingSystemSerializer,
    ProviderSerializer,
    CustomerSerializer,
    ServiceSerializer,
    AppointmentSerializer,
)


class ConnectView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ConnectSerializer(data=request.data)
        if serializer.is_valid():
            bs = BookingSystem.objects.create(
                name=serializer.validated_data["name"],
                base_url=serializer.validated_data["base_url"],
                credentials={
                    "username": serializer.validated_data["username"],
                    "password": serializer.validated_data["password"],
                },
            )
            return Response(
                BookingSystemSerializer(bs).data, status=status.HTTP_201_CREATED
            )
        return Response(
            {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )


class StatusView(APIView):
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
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        bs = get_object_or_404(BookingSystem, id=self.kwargs["id"])
        return bs.services.all().order_by(
            "id"
        )  # Added order_by to fix unordered queryset warning


class AppointmentListView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        bs = get_object_or_404(BookingSystem, id=self.kwargs["id"])
        qs = bs.appointments.all()
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        if start_date:
            try:
                start_dt = make_aware(datetime.strptime(start_date, "%Y-%m-%d"))
                qs = qs.filter(start_time__gte=start_dt)
            except ValueError:
                pass  # Optional: Handle invalid date format
        if end_date:
            try:
                end_dt = make_aware(
                    datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                ) - timedelta(seconds=1)
                qs = qs.filter(start_time__lte=end_dt)
            except ValueError:
                pass
        return qs.order_by("id")
