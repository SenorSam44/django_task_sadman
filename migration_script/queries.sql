SELECT
    p.first_name || ' ' || p.last_name AS name,
    COUNT(a.id) AS total_appointments,
    SUM(s.price) AS total_revenue,
    COUNT(DISTINCT a.customer_id) AS unique_customers,
    AVG(s.price) AS average_appointment_value
FROM
    core_appointment a
JOIN
    core_provider p ON a.provider_id = p.id
JOIN
    core_service s ON a.service_id = s.id
WHERE
    a.booking_system_id = %s
    AND a.start_time BETWEEN %s AND %s
GROUP BY
    p.id, p.first_name, p.last_name
ORDER BY
    total_revenue DESC;