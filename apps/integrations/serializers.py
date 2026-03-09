from rest_framework import serializers
from apps.bookings.models import BookingSystem, Provider, Customer, Service, Appointment


class ConnectSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=255)
    base_url = serializers.URLField(required=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class BookingSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingSystem
        fields = ["id", "name", "base_url", "last_synced_at", "sync_status"]


class ProviderSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    class Meta:
        model = Provider
        fields = ["id", "name", "email", "phone", "external_id"]


class CustomerSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    class Meta:
        model = Customer
        fields = ["id", "name", "email", "phone", "external_id"]


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "duration_minutes", "price", "currency", "external_id"]


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            "id",
            "start_time",
            "end_time",
            "status",
            "location",
            "external_id",
            "provider",
            "customer",
            "service",
        ]
