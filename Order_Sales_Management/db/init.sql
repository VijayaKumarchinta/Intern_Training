BEGIN;

DROP SCHEMA IF EXISTS order_sales CASCADE;
CREATE SCHEMA order_sales;

CREATE TABLE order_sales.users (
    id                  SERIAL PRIMARY KEY,
    email               VARCHAR(255) UNIQUE NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,
    full_name           VARCHAR(255),
    role                VARCHAR(20) NOT NULL DEFAULT 'customer'
                        CHECK (role IN ('admin','customer')),
    is_verified         BOOLEAN NOT NULL DEFAULT FALSE,
    verification_token  VARCHAR(255),
    reset_token         VARCHAR(255),
    reset_token_expires TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE order_sales.customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    user_id     INTEGER REFERENCES order_sales.users(id) ON DELETE SET NULL,
    name        VARCHAR(255),
    email       VARCHAR(255),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE order_sales.orders (
    order_id          VARCHAR(20) PRIMARY KEY,
    order_date        DATE,
    customer_id       VARCHAR(20),
    product           VARCHAR(100),
    quantity          NUMERIC(10,2),
    unit_price        NUMERIC(12,2),
    order_status      VARCHAR(20),
    is_valid          BOOLEAN NOT NULL DEFAULT FALSE,
    validation_errors TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE order_sales.staging_orders (
    order_id     TEXT,
    order_date   TEXT,
    customer_id  TEXT,
    product      TEXT,
    quantity     TEXT,
    unit_price   TEXT,
    order_status TEXT
);

CREATE INDEX idx_orders_customer ON order_sales.orders(customer_id);
CREATE INDEX idx_orders_status   ON order_sales.orders(order_status);

COMMIT;