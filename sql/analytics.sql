-- Business-facing analytics queries used to validate the curated dataset.

SELECT
    order_year,
    order_month,
    COUNT(*) AS order_count,
    SUM(amount) AS revenue,
    AVG(amount) AS average_order_value
FROM fact_orders
GROUP BY order_year, order_month
ORDER BY order_year, order_month;

SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(amount) AS customer_revenue
FROM fact_orders
GROUP BY customer_id
ORDER BY customer_revenue DESC
LIMIT 10;
