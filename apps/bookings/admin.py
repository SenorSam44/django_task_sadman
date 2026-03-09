from django.contrib import admin
from .models import BookingSystem, Provider, Customer, Service, Appointment

# Register your models here.


@admin.register(BookingSystem)
class BookingSystemAdmin(admin.ModelAdmin):
    list_display = ("name", "base_url", "last_synced_at", "sync_status")


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ("__str__", "booking_system", "email", "external_id")
    list_filter = ("booking_system",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("__str__", "booking_system", "email", "external_id")
    list_filter = ("booking_system",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "booking_system", "price", "external_id")
    list_filter = ("booking_system",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "booking_system",
        "start_time",
        "provider",
        "customer",
        "service",
    )
    list_filter = ("booking_system", "start_time")
