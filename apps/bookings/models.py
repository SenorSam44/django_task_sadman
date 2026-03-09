from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BookingSystem(TimestampedModel):
    name = models.CharField(max_length=255)
    base_url = models.URLField()
    credentials = models.JSONField(
        default=dict
    )  # {"username": "...", "password": "..."}
    last_synced_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sync_status = models.CharField(max_length=50, default="ok")

    def __str__(self) -> str:
        return self.name


class Provider(TimestampedModel):
    booking_system = models.ForeignKey(
        BookingSystem, on_delete=models.CASCADE, related_name="providers"
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    external_id = models.CharField(max_length=255)
    extra_data = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["booking_system", "external_id"],
                name="unique_provider_external_id",
            )
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Customer(TimestampedModel):
    booking_system = models.ForeignKey(
        BookingSystem, on_delete=models.CASCADE, related_name="customers"
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    external_id = models.CharField(max_length=255)
    extra_data = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["booking_system", "external_id"],
                name="unique_customer_external_id",
            )
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Service(TimestampedModel):
    booking_system = models.ForeignKey(
        BookingSystem, on_delete=models.CASCADE, related_name="services"
    )
    name = models.CharField(max_length=255)
    duration_minutes = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    external_id = models.CharField(max_length=255)
    extra_data = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["booking_system", "external_id"],
                name="unique_service_external_id",
            )
        ]

    def __str__(self) -> str:
        return self.name


class Appointment(TimestampedModel):
    booking_system = models.ForeignKey(
        BookingSystem, on_delete=models.CASCADE, related_name="appointments"
    )
    provider = models.ForeignKey(
        Provider, null=True, on_delete=models.SET_NULL, related_name="appointments"
    )
    customer = models.ForeignKey(
        Customer, null=True, on_delete=models.SET_NULL, related_name="appointments"
    )
    service = models.ForeignKey(
        Service, null=True, on_delete=models.SET_NULL, related_name="appointments"
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=50, default="confirmed")
    location = models.CharField(max_length=255, blank=True)
    external_id = models.CharField(max_length=255)
    extra_data = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["booking_system", "external_id"],
                name="unique_appointment_external_id",
            )
        ]
        indexes = [
            models.Index(fields=["start_time"], name="appt_start_idx"),
            models.Index(fields=["provider"], name="appt_provider_idx"),
            models.Index(fields=["service"], name="appt_service_idx"),
            models.Index(
                fields=["booking_system", "start_time"], name="appt_bs_start_idx"
            ),
        ]

    def __str__(self) -> str:
        return f"Appointment {self.external_id} at {self.start_time}"
