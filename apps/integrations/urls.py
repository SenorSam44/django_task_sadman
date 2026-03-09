from django.urls import path
from .views import (
    ConnectView, StatusView, ProviderListView, CustomerListView,
    ServiceListView, AppointmentListView
)

urlpatterns = [
    path('booking-systems/connect/', ConnectView.as_view(), name='connect'),
    path('booking-systems/<int:id>/status/', StatusView.as_view(), name='status'),
    path('booking-systems/<int:id>/providers/', ProviderListView.as_view(), name='providers'),
    path('booking-systems/<int:id>/customers/', CustomerListView.as_view(), name='customers'),
    path('booking-systems/<int:id>/services/', ServiceListView.as_view(), name='services'),
    path('booking-systems/<int:id>/appointments/', AppointmentListView.as_view(), name='appointments'),
]