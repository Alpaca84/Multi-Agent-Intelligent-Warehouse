-- Create inventory_movements table for historical demand data
-- This table stores all inventory movements (inbound, outbound, adjustments)

CREATE TABLE IF NOT EXISTS inventory_movements (
    id SERIAL PRIMARY KEY,
    sku TEXT NOT NULL,
    movement_type TEXT NOT NULL CHECK (movement_type IN ('inbound', 'outbound', 'adjustment')),
    quantity INTEGER NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    location TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_inventory_movements_sku ON inventory_movements(sku);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_timestamp ON inventory_movements(timestamp);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_type ON inventory_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_sku_timestamp ON inventory_movements(sku, timestamp);

-- Create a view for daily demand aggregation
CREATE OR REPLACE VIEW daily_demand AS
SELECT 
    sku,
    DATE(timestamp) as date,
    SUM(quantity) as total_demand,
    COUNT(*) as movement_count,
    AVG(quantity) as avg_quantity_per_movement
FROM inventory_movements 
WHERE movement_type = 'outbound'
GROUP BY sku, DATE(timestamp)
ORDER BY sku, date;

-- Create a view for weekly demand aggregation
CREATE OR REPLACE VIEW weekly_demand AS
SELECT 
    sku,
    DATE_TRUNC('week', timestamp) as week_start,
    SUM(quantity) as total_demand,
    COUNT(*) as movement_count,
    AVG(quantity) as avg_quantity_per_movement
FROM inventory_movements 
WHERE movement_type = 'outbound'
GROUP BY sku, DATE_TRUNC('week', timestamp)
ORDER BY sku, week_start;

-- Create a view for monthly demand aggregation
CREATE OR REPLACE VIEW monthly_demand AS
SELECT 
    sku,
    DATE_TRUNC('month', timestamp) as month_start,
    SUM(quantity) as total_demand,
    COUNT(*) as movement_count,
    AVG(quantity) as avg_quantity_per_movement
FROM inventory_movements 
WHERE movement_type = 'outbound'
GROUP BY sku, DATE_TRUNC('month', timestamp)
ORDER BY sku, month_start;

-- Create a view for brand-level aggregation
CREATE OR REPLACE VIEW brand_demand AS
SELECT 
    SUBSTRING(sku FROM 1 FOR 3) as brand,
    DATE_TRUNC('month', timestamp) as month_start,
    SUM(quantity) as total_demand,
    COUNT(DISTINCT sku) as product_count,
    AVG(quantity) as avg_quantity_per_movement
FROM inventory_movements 
WHERE movement_type = 'outbound'
GROUP BY SUBSTRING(sku FROM 1 FOR 3), DATE_TRUNC('month', timestamp)
ORDER BY brand, month_start;
