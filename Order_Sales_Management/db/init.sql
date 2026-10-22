-- db/init.sql - machine_sensor_db, guarded, no DROP, idempotent

DO $$
BEGIN
    IF current_database() NOT IN ('machine_sensor_db', 'order_sales_test_db') THEN
        RAISE EXCEPTION 'init.sql refused: connected to %, expected machine_sensor_db or order_sales_test_db', current_database();
    END IF;
END $$;

CREATE SCHEMA IF NOT EXISTS order_sales;

CREATE TABLE IF NOT EXISTS order_sales.users (
    id                       SERIAL PRIMARY KEY,
    email                    VARCHAR(255) NOT NULL,
    password_hash            VARCHAR(255) NOT NULL,
    full_name                VARCHAR(255),
    role                     VARCHAR(20)  NOT NULL DEFAULT 'customer',
    is_verified              BOOLEAN      NOT NULL DEFAULT FALSE,
    verification_token_hash  VARCHAR(255),
    verification_expires_at  TIMESTAMPTZ,
    verification_attempts    INTEGER      NOT NULL DEFAULT 0,
    reset_token_hash         VARCHAR(255),
    reset_token_expires_at   TIMESTAMPTZ,
    token_version            INTEGER      NOT NULL DEFAULT 0,
    created_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT users_role_check CHECK (role IN ('admin', 'customer'))
);
CREATE UNIQUE INDEX IF NOT EXISTS users_email_lower_uq
    ON order_sales.users (LOWER(email));

CREATE TABLE IF NOT EXISTS order_sales.customers (
    customer_id  VARCHAR(20) PRIMARY KEY,
    user_id      INTEGER UNIQUE REFERENCES order_sales.users(id) ON DELETE SET NULL,
    cust_name    VARCHAR(255),
    email        VARCHAR(255),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_sales.products (
    product_id     SERIAL PRIMARY KEY,
    pro_name       VARCHAR(100) NOT NULL UNIQUE,
    current_price  NUMERIC(12,2)
);

CREATE TABLE IF NOT EXISTS order_sales.orders (
    order_id     VARCHAR(20) PRIMARY KEY,
    customer_id  VARCHAR(20) NOT NULL REFERENCES order_sales.customers(customer_id),
    order_date   DATE,
    order_status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_sales.order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id      VARCHAR(20) NOT NULL REFERENCES order_sales.orders(order_id) ON DELETE CASCADE,
    product_id    INTEGER     NOT NULL REFERENCES order_sales.products(product_id),
    quantity      INTEGER     NOT NULL CHECK (quantity > 0),
    unit_price    NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    CONSTRAINT uq_order_product UNIQUE (order_id, product_id)
);

INSERT INTO order_sales.products (pro_name, current_price) VALUES
    ('Wireless Mouse',            19.99),
    ('Mechanical Keyboard',       89.99),
    ('USB-C Hub',                 34.50),
    ('Laptop Stand',              25.00),
    ('Noise-Cancel Headphones',  149.99)
ON CONFLICT (pro_name) DO UPDATE
    SET current_price = EXCLUDED.current_price
    WHERE order_sales.products.current_price IS NULL
       OR order_sales.products.current_price = 0;