# API_DISCOVERY.md

Notes from exploring the **EasyAppointments REST API (v1)** while building the booking sync integration.

Docs: https://easyappointments.org/documentation/rest-api/

---

## API Basics

Base URL format:

```
http://<host>/index.php/api/v1/<resource>
```

The API follows standard REST conventions:

| Method | Use |
|---|---|
| GET | fetch resources |
| POST | create |
| PUT | update |
| DELETE | delete |

Responses are JSON.

---

## Authentication

Uses **HTTP Basic Authentication**.

Each request must include:

```
Authorization: Basic base64(username:password)
```

Example:

```bash
curl http://host/index.php/api/v1/providers --user admin:password
```

Requires **administrator credentials**. API key auth via Bearer token is also supported if configured in the admin panel.

---

## Core Resources

| Resource | Endpoint |
|---|---|
| Providers | `/api/v1/providers` |
| Customers | `/api/v1/customers` |
| Services | `/api/v1/services` |
| Appointments | `/api/v1/appointments` |

All support standard REST operations (`GET`, `POST`, `PUT`, `DELETE`).

### Key fields per resource

**Provider** — `id`, `firstName`, `lastName`, `email`, `phone`, `services[]`, `settings.workingPlan`

**Customer** — `id`, `firstName`, `lastName`, `email`, `phone`, `timezone`

**Service** — `id`, `name`, `duration` (minutes), `price`, `currency`, `attendantsNumber`

**Appointment** — `id`, `start`, `end`, `providerId`, `customerId`, `serviceId`, `location`

Note: appointments reference related objects by **ID only**, not embedded objects.

---

## Pagination

The API supports cursor-style pagination via query parameters:

```
?page=<number>&length=<page_size>
```

Example:

```
GET /api/v1/appointments?page=1&length=100
```

- Default page size is **20**
- Returns an empty array `[]` when past the last page (not a 404)
- Our client uses `length=100` and stops when the response length is less than the page size

---

## Filtering & Query Helpers

| Parameter | Purpose | Example |
|---|---|---|
| `?q=<keyword>` | Keyword search | `?q=john` |
| `?sort=+field` / `?sort=-field` | Sort asc/desc | `?sort=-id` |
| `?fields=a,b,c` | Reduce payload | `?fields=id,start,end` |
| `?with=customer,provider` | Embed related objects | `?with=service` |
| `?from=YYYY-MM-DD` | Appointment start filter | `?from=2026-01-01` |
| `?till=YYYY-MM-DD` | Appointment end filter | `?till=2026-03-31` |

---

## Response Format

Success — returns the resource directly as JSON:

```json
{ "id": 1, "firstName": "John", "lastName": "Doe" }
```

Error:

```json
{ "code": 404, "message": "The requested record was not found!" }
```

---

## Rate Limiting

- The API returns **HTTP 429** when rate limited
- Response includes a `Retry-After` header (seconds to wait)
- Our client respects this header and retries automatically
- The seed script also includes a `time.sleep(30)` fallback for 429s

---

## Quirks & Notes

- **camelCase** in API (`firstName`, `providerId`), **snake_case** in our Django models
- `duration` in the API maps to `duration_minutes` in our Service model — easy to miss
- Optional string fields (`phone`, `address`, `notes`) can return `null` — must be coerced to `""` for `NOT NULL` CharField columns
- Authentication is required for every request; unauthenticated requests return 401
- The `services[]` array on a Provider response contains full service objects, not just IDs
- Provider `settings.workingPlan` is a nested object — stored in `extra_data` JSONField
- No bulk endpoints — all writes are single-record `POST`/`PUT`
