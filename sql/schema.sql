CREATE TABLE IF NOT EXISTS source_orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    order_date TIMESTAMP NOT NULL,
    amount NUMERIC(18,2) NOT NULL CHECK (amount >= 0),
    status VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    order_date TIMESTAMP NOT NULL,
    amount NUMERIC(18,2) NOT NULL,
    status VARCHAR(30) NOT NULL,
    order_year INT NOT NULL,
    order_month INT NOT NULL,
    loaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fact_orders_customer
    ON fact_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_orders_order_date
    ON fact_orders(order_date);
