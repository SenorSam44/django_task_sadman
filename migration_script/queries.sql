-- Task 4.2 — Raw SQL Analytics Query
--
-- Returns per-provider stats for a given booking system and date range.
-- Parameters: %(booking_system_id)s, %(start_date)s, %(end_date)s
--
-- Table names follow Django's convention: <app_label>_<model_name>
--   bookings_appointment, bookings_provider, bookings_service

SELECT
    p.first_name || ' ' || p.last_name   AS name,
    COUNT(a.id)                           AS total_appointments,
    SUM(s.price)                          AS total_revenue,
    COUNT(DISTINCT a.customer_id)         AS unique_customers,
    ROUND(AVG(s.price), 2)               AS avg_appointment_value
FROM bookings_appointment a
JOIN bookings_provider p  ON a.provider_id = p.id
JOIN bookings_service  s  ON a.service_id  = s.id
WHERE
    a.booking_system_id = %(booking_system_id)s
    AND a.start_time BETWEEN %(start_date)s AND %(end_date)s
GROUP BY
    p.id,
    p.first_name,
    p.last_name
ORDER BY
    total_revenue DESC;
