# booking-sync
Here is a **cleaner merged version** — still short, still “senior engineer in a hurry”, but with redundant sections removed and grouped logically. It reads like **real internal engineering notes**, not a school report.

---

# API_DISCOVERY.md

Notes from exploring the **EasyAppointments REST API (v1)** while building the booking sync integration.

Docs:
[https://easyappointments.org/documentation/rest-api/](https://easyappointments.org/documentation/rest-api/)

---

# API Basics

Base URL format:

```
http://<host>/index.php/api/v1/<resource>
```

Examples:

```
/api/v1/providers
/api/v1/customers
/api/v1/services
/api/v1/appointments
```

The API follows standard REST conventions:

| Method | Use             |
| ------ | --------------- |
| GET    | fetch resources |
| POST   | create          |
| PUT    | update          |
| DELETE | delete          |

Responses are JSON. ([Easy!Appointments][1])

---

# Authentication

Uses **Basic Authentication**.

Each request must include:

```
Authorization: Basic base64(username:password)
```

Example:

```
curl http://host/index.php/api/v1/providers --user admin:password
```

Requires **administrator credentials**.

API key auth is also supported via **Bearer token** if configured. ([Easy!Appointments][1])

---

# Core Resources

The sync integration mainly interacts with four resources.

| Resource     | Endpoint               |
| ------------ | ---------------------- |
| Providers    | `/api/v1/providers`    |
| Customers    | `/api/v1/customers`    |
| Services     | `/api/v1/services`     |
| Appointments | `/api/v1/appointments` |

All support typical REST operations:

```
GET /resource
GET /resource/{id}
POST /resource
PUT /resource/{id}
DELETE /resource/{id}
```

Example resource fields:

### Provider

```
id
firstName
lastName
email
phone
services[]
```

### Customer

```
id
firstName
lastName
email
phone
```

### Service

```
id
name
duration
price
currency
```

### Appointment

```
id
start
end
providerId
customerId
serviceId
```

Appointments reference other objects by **IDs rather than embedded objects**. ([Easy!Appointments][1])

---

# Query Helpers (Filtering / Pagination)

The API supports several query parameters for GET requests.

### Pagination

```
?page=<number>
&length=<page_size>
```

Example:

```
/api/v1/appointments?page=1&length=20
```

Default page size is **20**. ([Easy!Appointments][1])

---

### Search

```
?q=<keyword>
```

Example:

```
/api/v1/customers?q=john
```

---

### Sorting

```
?sort=+field
?sort=-field
```

Example:

```
/api/v1/appointments?sort=-id
```

Multiple fields allowed.

---

### Field Selection

Reduce payload size:

```
?fields=id,start,end
```

---

### Include Related Data

```
?with=customer,provider,service
```

Embeds related resources. ([Easy!Appointments][1])

---

# Response Format

Most responses return the requested resource JSON.

Example:

```
{
  "id": 1,
  "firstName": "John",
  "lastName": "Doe"
}
```

Errors are returned like:

```
{
  "code": 404,
  "message": "The requested record was not found!"
}
```

---

# Observations / Quirks
* Basic Auth required
* Standard Laravel REST resources
* Filtering via `q`, `sort`, `fields`
* Relations via IDs
* JSON responses
* No Pagination
* API uses camelCase, Internal models usually use snake_case.

