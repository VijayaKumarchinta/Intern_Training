DO $$
BEGIN
  IF current_database() NOT IN ('order_sales', 'machine_sensor_db') THEN
  RAISE EXCEPTION 'Wrong database: %', current_database();
END IF;
END $$;

CREATE SCHEMA IF NOT EXISTS order_sales;
SET search_path TO order_sales;

CREATE TABLE IF NOT EXISTS users (
  id                        SERIAL PRIMARY KEY,
  email                     TEXT NOT NULL,
  password_hash             TEXT NOT NULL,
  full_name                 TEXT,
  role                      TEXT NOT NULL DEFAULT 'customer'
                              CHECK (role IN ('admin','customer')),
  is_verified               BOOLEAN NOT NULL DEFAULT FALSE,
  verification_token_hash   TEXT,
  verification_attempts     INTEGER NOT NULL DEFAULT 0,
  verification_expires_at   TIMESTAMPTZ,
  reset_token_hash          TEXT,
  reset_token_expires_at    TIMESTAMPTZ,          
  token_version             INTEGER NOT NULL DEFAULT 0,
  created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email_lower
  ON users (LOWER(email));

CREATE TABLE IF NOT EXISTS customers (
  customer_id  TEXT PRIMARY KEY,
  user_id      INTEGER UNIQUE REFERENCES users(id) ON DELETE SET NULL,
  cust_name    TEXT,
  email        TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()  
);

CREATE TABLE IF NOT EXISTS products (
  product_id    SERIAL PRIMARY KEY,
  pro_name      TEXT NOT NULL UNIQUE,
  current_price NUMERIC(12,2) NOT NULL DEFAULT 0
                  CHECK (current_price >= 0)
);

CREATE TABLE IF NOT EXISTS orders (
  order_id      TEXT PRIMARY KEY,
  customer_id   TEXT NOT NULL REFERENCES customers(customer_id),
  order_date    DATE,                             
  order_status  TEXT NOT NULL DEFAULT 'Pending'
                  CHECK (order_status IN
                    ('Pending','Received','Shipped','Cancelled','Delivered','Returned')),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_orders_customer  ON orders (customer_id);
CREATE INDEX IF NOT EXISTS ix_orders_date      ON orders (order_date);
CREATE INDEX IF NOT EXISTS ix_orders_status    ON orders (order_status);

CREATE TABLE IF NOT EXISTS order_items (
  order_item_id  SERIAL PRIMARY KEY,
  order_id       TEXT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
  product_id     INTEGER NOT NULL REFERENCES products(product_id),
  quantity       INTEGER NOT NULL CHECK (quantity > 0),
  unit_price     NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
  UNIQUE (order_id, product_id)
);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_orders_updated_at ON orders;
CREATE TRIGGER trg_orders_updated_at
  BEFORE UPDATE ON orders
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();