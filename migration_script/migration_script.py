"""
Migration: Add performance indexes for analytics queries.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # Depends on the initial migration that created the Appointment table
        ("bookings", "0001_initial"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["booking_system", "start_time"],
                name="appt_bs_start_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["provider"],
                name="appt_provider_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["service"],
                name="appt_service_idx",
            ),
        ),
        # ── appt_start_idx ───────────────────────────────────────────────────
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(
                fields=["start_time"],
                name="appt_start_idx",
            ),
        ),
    ]
