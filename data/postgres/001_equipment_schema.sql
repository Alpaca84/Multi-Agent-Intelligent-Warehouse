-- Equipment & Asset Operations Schema
-- This separates equipment/assets from inventory items

-- Equipment assets (master)
CREATE TABLE IF NOT EXISTS equipment_assets (
  asset_id TEXT PRIMARY KEY,      -- e.g., "FL-07", "AMR-001", "CHG-05"
  type TEXT NOT NULL,             -- forklift, amr, agv, conveyor, scanner, charger, humanoid
  model TEXT,                     -- "Toyota 8FGU25", "MiR-250", "Honeywell CT60"
  zone TEXT,                      -- "Zone A", "Loading Dock", "Assembly Line"
  status TEXT NOT NULL DEFAULT 'available', -- available, assigned, charging, maintenance, out_of_service
  owner_user TEXT,                -- current holder (for scanners, etc.)
  next_pm_due TIMESTAMPTZ,        -- next preventive maintenance due
  last_maintenance TIMESTAMPTZ,   -- last maintenance performed
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Equipment assignments (who/what/when)
CREATE TABLE IF NOT EXISTS equipment_assignments (
  id BIGSERIAL PRIMARY KEY,
  asset_id TEXT NOT NULL REFERENCES equipment_assets(asset_id) ON DELETE CASCADE,
  task_id TEXT,                   -- optional task reference
  assignee TEXT,                  -- user or system that has the equipment
  assignment_type TEXT NOT NULL,  -- task, zone, user, maintenance
  assigned_at TIMESTAMPTZ DEFAULT now(),
  released_at TIMESTAMPTZ,        -- when assignment ended
  notes TEXT
);

-- Equipment telemetry (Timescale hypertable) - updated schema
CREATE TABLE IF NOT EXISTS equipment_telemetry (
  ts TIMESTAMPTZ NOT NULL,
  asset_id TEXT NOT NULL,
  metric TEXT NOT NULL,           -- battery_soc, temp_c, speed, location_x, location_y, etc.
  value DOUBLE PRECISION NOT NULL,
  unit TEXT,                      -- %, °C, m/s, m, etc.
  quality_score DOUBLE PRECISION DEFAULT 1.0 -- data quality indicator
);

-- Create Timescale hypertable for telemetry
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname=timescaledb) THEN
    CREATE EXTENSION IF NOT EXISTS timescaledb;
  END IF;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

DO $$
BEGIN
  PERFORM create_hypertable('equipment_telemetry','ts', if_not_exists=>TRUE);
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- Equipment maintenance records
CREATE TABLE IF NOT EXISTS equipment_maintenance (
  id BIGSERIAL PRIMARY KEY,
  asset_id TEXT NOT NULL REFERENCES equipment_assets(asset_id) ON DELETE CASCADE,
  maintenance_type TEXT NOT NULL, -- preventive, corrective, emergency, inspection
  description TEXT,
  performed_by TEXT,              -- technician or system
  performed_at TIMESTAMPTZ DEFAULT now(),
  duration_minutes INTEGER,       -- how long maintenance took
  parts_used JSONB DEFAULT '[]'::jsonb, -- list of parts/supplies used
  cost DECIMAL(10,2),             -- maintenance cost
  notes TEXT,
  next_due TIMESTAMPTZ           -- when next maintenance is due
);

-- Equipment performance metrics
CREATE TABLE IF NOT EXISTS equipment_performance (
  id BIGSERIAL PRIMARY KEY,
  asset_id TEXT NOT NULL REFERENCES equipment_assets(asset_id) ON DELETE CASCADE,
  metric_name TEXT NOT NULL,      -- uptime, efficiency, utilization, etc.
  metric_value DOUBLE PRECISION NOT NULL,
  measurement_period TEXT NOT NULL, -- daily, weekly, monthly
  measured_at TIMESTAMPTZ DEFAULT now(),
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Sample equipment data
INSERT INTO equipment_assets (asset_id, type, model, zone, status, owner_user, next_pm_due) VALUES
  ('FL-01', 'forklift', 'Toyota 8FGU25', 'Zone A', 'available', NULL, now() + interval '30 days'),
  ('FL-02', 'forklift', 'Toyota 8FGU25', 'Zone B', 'assigned', 'operator1', now() + interval '15 days'),
  ('FL-03', 'forklift', 'Hyster H2.5XM', 'Loading Dock', 'maintenance', NULL, now() + interval '7 days'),
  ('AMR-001', 'amr', 'MiR-250', 'Zone A', 'available', NULL, now() + interval '45 days'),
  ('AMR-002', 'amr', 'MiR-250', 'Zone B', 'charging', NULL, now() + interval '30 days'),
  ('AGV-01', 'agv', 'Kiva Systems', 'Assembly Line', 'assigned', 'operator2', now() + interval '60 days'),
  ('SCN-01', 'scanner', 'Honeywell CT60', 'Zone A', 'assigned', 'operator1', now() + interval '90 days'),
  ('SCN-02', 'scanner', 'Honeywell CT60', 'Zone B', 'available', NULL, now() + interval '90 days'),
  ('CHG-01', 'charger', 'Forklift Charger', 'Charging Station', 'available', NULL, now() + interval '180 days'),
  ('CHG-02', 'charger', 'AMR Charger', 'Charging Station', 'available', NULL, now() + interval '180 days'),
  ('CONV-01', 'conveyor', 'Belt Conveyor 3m', 'Assembly Line', 'available', NULL, now() + interval '120 days'),
  ('HUM-01', 'humanoid', 'Boston Dynamics Stretch', 'Zone A', 'maintenance', NULL, now() + interval '14 days')
ON CONFLICT (asset_id) DO UPDATE SET
  type = EXCLUDED.type,
  model = EXCLUDED.model,
  zone = EXCLUDED.zone,
  status = EXCLUDED.status,
  owner_user = EXCLUDED.owner_user,
  next_pm_due = EXCLUDED.next_pm_due,
  updated_at = now();

-- Sample telemetry data (last 24 hours)
INSERT INTO equipment_telemetry (ts, asset_id, metric, value, unit, quality_score) VALUES
  -- Forklift FL-01 data
  (now() - interval '1 hour', 'FL-01', 'battery_soc', 85.5, '%', 1.0),
  (now() - interval '1 hour', 'FL-01', 'temp_c', 22.3, '°C', 1.0),
  (now() - interval '1 hour', 'FL-01', 'speed', 0.0, 'm/s', 1.0),
  (now() - interval '1 hour', 'FL-01', 'location_x', 125.5, 'm', 1.0),
  (now() - interval '1 hour', 'FL-01', 'location_y', 67.2, 'm', 1.0),
  
  -- AMR-001 data
  (now() - interval '30 minutes', 'AMR-001', 'battery_soc', 92.1, '%', 1.0),
  (now() - interval '30 minutes', 'AMR-001', 'temp_c', 24.1, '°C', 1.0),
  (now() - interval '30 minutes', 'AMR-001', 'speed', 1.2, 'm/s', 1.0),
  (now() - interval '30 minutes', 'AMR-001', 'location_x', 89.3, 'm', 1.0),
  (now() - interval '30 minutes', 'AMR-001', 'location_y', 45.7, 'm', 1.0),
  
  -- Charger CHG-01 data
  (now() - interval '15 minutes', 'CHG-01', 'temp_c', 28.5, '°C', 1.0),
  (now() - interval '15 minutes', 'CHG-01', 'voltage', 48.2, 'V', 1.0),
  (now() - interval '15 minutes', 'CHG-01', 'current', 15.3, 'A', 1.0),
  (now() - interval '15 minutes', 'CHG-01', 'power', 737.46, 'W', 1.0);

-- Sample assignments
INSERT INTO equipment_assignments (asset_id, task_id, assignee, assignment_type, assigned_at) VALUES
  ('FL-02', 'TASK-001', 'operator1', 'task', now() - interval '2 hours'),
  ('AMR-001', 'TASK-002', 'system', 'task', now() - interval '1 hour'),
  ('SCN-01', NULL, 'operator1', 'user', now() - interval '4 hours'),
  ('AGV-01', 'TASK-003', 'operator2', 'task', now() - interval '30 minutes');

-- Sample maintenance records
INSERT INTO equipment_maintenance (asset_id, maintenance_type, description, performed_by, performed_at, duration_minutes, cost) VALUES
  ('FL-03', 'corrective', 'Hydraulic leak repair', 'tech1', now() - interval '2 days', 120, 450.00),
  ('HUM-01', 'preventive', 'Monthly inspection and calibration', 'tech2', now() - interval '1 day', 90, 200.00),
  ('CHG-01', 'inspection', 'Electrical safety check', 'tech1', now() - interval '3 days', 30, 75.00);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_equipment_assets_type ON equipment_assets(type);
CREATE INDEX IF NOT EXISTS idx_equipment_assets_status ON equipment_assets(status);
CREATE INDEX IF NOT EXISTS idx_equipment_assets_zone ON equipment_assets(zone);
CREATE INDEX IF NOT EXISTS idx_equipment_assignments_asset_id ON equipment_assignments(asset_id);
CREATE INDEX IF NOT EXISTS idx_equipment_assignments_assignee ON equipment_assignments(assignee);
CREATE INDEX IF NOT EXISTS idx_equipment_telemetry_asset_id ON equipment_telemetry(asset_id);
CREATE INDEX IF NOT EXISTS idx_equipment_telemetry_metric ON equipment_telemetry(metric);
CREATE INDEX IF NOT EXISTS idx_equipment_maintenance_asset_id ON equipment_maintenance(asset_id);
CREATE INDEX IF NOT EXISTS idx_equipment_performance_asset_id ON equipment_performance(asset_id);
