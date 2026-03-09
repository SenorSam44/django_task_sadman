# Booking Sync

A Django backend that integrates with third-party appointment booking systems (Easy!Appointments), syncs data into a local database, and exposes a REST API with analytics.

## Stack

- **Django 6** + **Django REST Framework** — API layer
- **PostgreSQL 16** — primary database
- **Celery 5** + **Redis 7** — async task queue and beat scheduler
- **PDM** — dependency management

---

## Quick Start

### Prerequisites
- Docker & Docker Compose

### 1. Clone and start

```bash
git clone https://github.com/SenorSam44/django_task_sadman
cd booking-sync
make up          # builds images, runs migrations, starts all services
```

### 2. Create a superuser (optional, for admin panel)

```bash
make createsuperuser
```

### 3. Run the Easy!Appointments third-party system

```bash
# In a separate directory
docker compose -f docker-compose.easyappointments.yml up -d
# Then seed sample data
python seed_data.py
```

---

## Makefile Commands

```bash
make up               # Build and start all containers
make down             # Stop all containers
make down up          # Restart
make logs             # Tail logs
make shell            # Bash into the django container
make migrate          # Run migrations
make makemigrations   # Generate new migrations
make createsuperuser  # Create Django admin user
```

---

## API Reference

All responses use a standardised envelope:

```json
{
  "data": "...",
  "errors": [],
  "meta": { "page": 1, "total_pages": 5, "total_count": 100 }
}
```

Error responses:
```json
{ "data": null, "errors": [{ "message": "..." }], "meta": null }
```

### Endpoints

| Method | URL | Description |
|---|---|---|
| `POST` | `/api/booking-systems/connect/` | Register a booking system (tests connection first) |
| `GET` | `/api/booking-systems/{id}/status/` | Connection status and record counts |
| `GET` | `/api/booking-systems/{id}/providers/` | List providers (paginated, `?search=name`) |
| `GET` | `/api/booking-systems/{id}/customers/` | List customers (paginated, `?search=name`) |
| `GET` | `/api/booking-systems/{id}/services/` | List services (paginated) |
| `GET` | `/api/booking-systems/{id}/appointments/` | List appointments (paginated, `?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`) |
| `POST` | `/api/booking-systems/{id}/sync/` | Trigger async full sync, returns `task_id` |
| `GET` | `/api/booking-systems/{id}/sync/status/` | Current sync status and `last_synced_at` |

### Example: Connect a booking system

```bash
curl -X POST http://localhost:8000/api/booking-systems/connect/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Salon",
    "base_url": "http://localhost:8888",
    "username": "admin",
    "password": "admin123"
  }'
```

### Example: Trigger sync

```bash
curl -X POST http://localhost:8000/api/booking-systems/1/sync/
# Returns: { "data": { "task_id": "abc-123" }, ... }
```

---

## Analytics Report (Task 4)

```bash
python manage.py generate_report \
  --booking_system_id=1 \
  --start_date=2026-01-01 \
  --end_date=2026-03-07
```

Outputs JSON with summary, monthly breakdown, top 5 providers, and top 5 services by revenue.

---

## Running Tests

```bash
# Inside the container
make shell
pdm run pytest

# Or directly
docker compose exec django pdm run pytest -v
```
