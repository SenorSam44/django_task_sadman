"""
Management command for Task 4.1 — Analytics Report

Usage:
    python manage.py generate_report --booking_system_id=1 \
        --start_date=2026-01-01 --end_date=2026-03-07
"""

import json
from datetime import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Avg, Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncMonth

from apps.bookings.models import Appointment, BookingSystem


class DecimalEncoder(json.JSONEncoder):
    """Serialise Decimal values that json.dumps can't handle natively."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class Command(BaseCommand):
    help = "Generate an analytics report for a booking system over a date range."

    def add_arguments(self, parser):
        parser.add_argument("--booking_system_id", type=int, required=True)
        parser.add_argument("--start_date", type=str, required=True, help="YYYY-MM-DD")
        parser.add_argument("--end_date", type=str, required=True, help="YYYY-MM-DD")

    def handle(self, *args, **options):
        bs_id = options["booking_system_id"]
        start_str = options["start_date"]
        end_str = options["end_date"]

        try:
            bs = BookingSystem.objects.get(id=bs_id)
        except BookingSystem.DoesNotExist:
            raise CommandError(f"BookingSystem with id={bs_id} does not exist.")

        try:
            start_dt = datetime.strptime(start_str, "%Y-%m-%d")
            end_dt = datetime.strptime(end_str, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )
        except ValueError as exc:
            raise CommandError(f"Invalid date format: {exc}")

        appts = Appointment.objects.filter(
            booking_system=bs,
            start_time__gte=start_dt,
            start_time__lte=end_dt,
            service__isnull=False,
        ).select_related("provider", "customer", "service")

        summary_qs = appts.aggregate(
            total_appointments=Count("id"),
            unique_customers=Count("customer_id", distinct=True),
            total_revenue=Sum("service__price"),
            avg_appointment_value=Avg("service__price"),
        )

        total_revenue = summary_qs["total_revenue"] or Decimal("0")
        total_appts = summary_qs["total_appointments"] or 0
        avg_value = (
            round(total_revenue / total_appts, 2) if total_appts else Decimal("0")
        )

        monthly_qs = (
            appts.annotate(month=TruncMonth("start_time"))
            .values("month")
            .annotate(
                appointments=Count("id"),
                unique_customers=Count("customer_id", distinct=True),
                revenue=Sum("service__price"),
            )
            .order_by("month")
        )

        monthly_breakdown = [
            {
                "month": row["month"].strftime("%Y-%m"),
                "appointments": row["appointments"],
                "unique_customers": row["unique_customers"],
                "revenue": float(row["revenue"] or 0),
            }
            for row in monthly_qs
        ]

        top_providers_qs = (
            appts.filter(provider__isnull=False)
            .values("provider__first_name", "provider__last_name")
            .annotate(
                total_appointments=Count("id"),
                total_revenue=Sum("service__price"),
            )
            .order_by("-total_revenue")[:5]
        )

        top_providers = [
            {
                "name": f"{row['provider__first_name']} {row['provider__last_name']}",
                "total_appointments": row["total_appointments"],
                "total_revenue": float(row["total_revenue"] or 0),
            }
            for row in top_providers_qs
        ]

        top_services_qs = (
            appts.values("service__name")
            .annotate(
                times_booked=Count("id"),
                total_revenue=Sum("service__price"),
            )
            .order_by("-total_revenue")[:5]
        )

        top_services = [
            {
                "name": row["service__name"],
                "times_booked": row["times_booked"],
                "total_revenue": float(row["total_revenue"] or 0),
            }
            for row in top_services_qs
        ]

        report = {
            "booking_system": bs.name,
            "period": f"{start_str} to {end_str}",
            "summary": {
                "total_appointments": total_appts,
                "unique_customers": summary_qs["unique_customers"] or 0,
                "total_revenue": float(total_revenue),
                "avg_appointment_value": float(avg_value),
            },
            "monthly_breakdown": monthly_breakdown,
            "top_providers": top_providers,
            "top_services": top_services,
        }

        self.stdout.write(json.dumps(report, indent=2, cls=DecimalEncoder))
