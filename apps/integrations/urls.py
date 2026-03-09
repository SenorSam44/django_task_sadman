from django.urls import path

from .views import (
    AppointmentListView,
    ConnectView,
    CustomerListView,
    ProviderListView,
    ServiceListView,
    StatusView,
    SyncStatusView,
    SyncTriggerView,
)

urlpatterns = [
    # Registration & status
    path("booking-systems/connect/", ConnectView.as_view(), name="connect"),
    path("booking-systems/<int:id>/status/", StatusView.as_view(), name="status"),
    # Synced data
    path(
        "booking-systems/<int:id>/providers/",
        ProviderListView.as_view(),
        name="providers",
    ),
    path(
        "booking-systems/<int:id>/customers/",
        CustomerListView.as_view(),
        name="customers",
    ),
    path(
        "booking-systems/<int:id>/services/", ServiceListView.as_view(), name="services"
    ),
    path(
        "booking-systems/<int:id>/appointments/",
        AppointmentListView.as_view(),
        name="appointments",
    ),
    # Sync triggers (Task 3.3)
    path(
        "booking-systems/<int:id>/sync/", SyncTriggerView.as_view(), name="sync_trigger"
    ),
    path(
        "booking-systems/<int:id>/sync/status/",
        SyncStatusView.as_view(),
        name="sync_status",
    ),
]
