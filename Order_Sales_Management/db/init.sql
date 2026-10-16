BEGIN;

DROP SCHEMA IF EXISTS order_sales CASCADE;
CREATE SCHEMA order_sales;

CREATE TABLE order_sales.users (
    id                      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email                   VARCHAR(255) NOT NULL,
    password_hash           VARCHAR(255) NOT NULL,
    full_name               VARCHAR(255),
    role                    VARCHAR(20) NOT NULL DEFAULT 'customer'
                            CHECK (role IN ('admin', 'customer')),

    is_verified             BOOLEAN NOT NULL DEFAULT FALSE,
    verification_token_hash VARCHAR(255),
    verification_expires_at TIMESTAMPTZ,
    verification_attempts   INTEGER NOT NULL DEFAULT 0,
    
    reset_token_hash        VARCHAR(255),
    reset_token_expires_at  TIMESTAMPTZ,
    token_version           INTEGER NOT NULL DEFAULT 0,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_users_email_lower
    ON order_sales.users (LOWER(email));

CREATE TABLE order_sales.customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    user_id     INTEGER UNIQUE
                    REFERENCES order_sales.users(id)
                    ON DELETE SET NULL,
    cust_name        VARCHAR(255),
    email       VARCHAR(255),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE order_sales.products (
    product_id  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pro_name          VARCHAR(100) NOT NULL UNIQUE,
    current_price NUMERIC(12,2)
                    CHECK (current_price IS NULL OR current_price >= 0)
);

CREATE TABLE order_sales.orders (
    order_id     VARCHAR(20) PRIMARY KEY,
    customer_id  VARCHAR(20) NOT NULL
                    REFERENCES order_sales.customers(customer_id),
    order_date   DATE,
    order_status VARCHAR(20) NOT NULL DEFAULT 'Pending'
                    CHECK (order_status IN (
                        'Pending', 'Received', 'Shipped',
                        'Delivered', 'Cancelled', 'Returned'
                    )),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE order_sales.order_items (
    order_item_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id      VARCHAR(20) NOT NULL
                    REFERENCES order_sales.orders(order_id)
                    ON DELETE CASCADE,
    product_id    INTEGER NOT NULL
                    REFERENCES order_sales.products(product_id),
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    unit_price    NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
    UNIQUE (order_id, product_id)
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

CREATE INDEX idx_orders_customer_date
    ON order_sales.orders (customer_id, order_date);

CREATE INDEX idx_orders_status
    ON order_sales.orders (order_status);

CREATE INDEX idx_order_items_product
    ON order_sales.order_items (product_id);


CREATE OR REPLACE FUNCTION order_sales.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON order_sales.users
    FOR EACH ROW EXECUTE FUNCTION order_sales.set_updated_at();

CREATE TRIGGER trg_orders_updated_at
    BEFORE UPDATE ON order_sales.orders
    FOR EACH ROW EXECUTE FUNCTION order_sales.set_updated_at();
    
COMMIT;