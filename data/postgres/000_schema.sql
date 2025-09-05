CREATE TABLE IF NOT EXISTS inventory_items (
  id SERIAL PRIMARY KEY,
  sku TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  quantity INTEGER NOT NULL DEFAULT 0,
  location TEXT,
  reorder_point INTEGER DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tasks (
  id SERIAL PRIMARY KEY,
  kind TEXT NOT NULL,          -- pick, pack, putaway, cycle_count
  status TEXT NOT NULL DEFAULT 'pending',
  assignee TEXT,
  payload JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS safety_incidents (
  id SERIAL PRIMARY KEY,
  severity TEXT,
  description TEXT,
  reported_by TEXT,
  occurred_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS equipment_telemetry (
  ts TIMESTAMPTZ NOT NULL,
  equipment_id TEXT NOT NULL,
  metric TEXT NOT NULL,
  value DOUBLE PRECISION NOT NULL
);

-- User authentication and authorization tables
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  full_name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('admin', 'manager', 'supervisor', 'operator', 'viewer')),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended', 'pending')),
  hashed_password TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  last_login TIMESTAMPTZ
);

-- User sessions for token management
CREATE TABLE IF NOT EXISTS user_sessions (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  refresh_token_hash TEXT NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  is_revoked BOOLEAN DEFAULT FALSE
);

-- Audit log for user actions
CREATE TABLE IF NOT EXISTS audit_log (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  action TEXT NOT NULL,
  resource_type TEXT,
  resource_id TEXT,
  details JSONB DEFAULT '{}'::jsonb,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname=timescaledb) THEN
    CREATE EXTENSION IF NOT EXISTS timescaledb;
  END IF;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

DO $$
BEGIN
  PERFORM create_hypertable(equipment_telemetry,ts, if_not_exists=>TRUE);
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- Sample data
INSERT INTO inventory_items (sku, name, quantity, location, reorder_point) VALUES
  ('SKU123', 'Blue Pallet Jack', 14, 'Aisle A3', 5),
  ('SKU456', 'RF Scanner', 6, 'Cage C1', 2),
  ('SKU789', 'Safety Vest', 25, 'Dock D2', 10),
  ('SKU101', 'Forklift Battery', 3, 'Maintenance Bay', 1),
  ('SKU202', 'Conveyor Belt', 8, 'Assembly Line', 3),
  ('SKU303', 'Packaging Tape', 50, 'Packaging Station', 20),
  ('SKU404', 'Label Printer', 2, 'Office', 1),
  ('SKU505', 'Hand Truck', 12, 'Loading Dock', 4)
ON CONFLICT (sku) DO UPDATE SET
  name = EXCLUDED.name,
  quantity = EXCLUDED.quantity,
  location = EXCLUDED.location,
  reorder_point = EXCLUDED.reorder_point,
  updated_at = now();

-- Sample users (passwords are 'password123' hashed with bcrypt)
INSERT INTO users (username, email, full_name, role, status, hashed_password) VALUES
  ('admin', 'admin@warehouse.com', 'System Administrator', 'admin', 'active', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzqK2a'),
  ('manager1', 'manager1@warehouse.com', 'John Manager', 'manager', 'active', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzqK2a'),
  ('supervisor1', 'supervisor1@warehouse.com', 'Jane Supervisor', 'supervisor', 'active', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzqK2a'),
  ('operator1', 'operator1@warehouse.com', 'Bob Operator', 'operator', 'active', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzqK2a'),
  ('viewer1', 'viewer1@warehouse.com', 'Alice Viewer', 'viewer', 'active', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzqK2a')
ON CONFLICT (username) DO UPDATE SET
  email = EXCLUDED.email,
  full_name = EXCLUDED.full_name,
  role = EXCLUDED.role,
  status = EXCLUDED.status,
  updated_at = now();
