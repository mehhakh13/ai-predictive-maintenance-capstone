-- SQL to create the fmucd table in Supabase
-- Run this in the Supabase SQL Editor before running the Python script

CREATE TABLE IF NOT EXISTS fmucd (
    id BIGSERIAL PRIMARY KEY,
    university_id INTEGER,
    country TEXT,
    state_province TEXT,
    building_id TEXT,
    building_name TEXT,
    size DOUBLE PRECISION,
    type TEXT,
    built_year INTEGER,
    fci DOUBLE PRECISION,
    crv DOUBLE PRECISION,
    dmc DOUBLE PRECISION,
    system_code TEXT,
    system_description TEXT,
    subsystem_code TEXT,
    subsystem_description TEXT,
    descriptive_code TEXT,
    component_description TEXT,
    wo_id TEXT,
    wo_description TEXT,
    wo_priority INTEGER,
    wo_start_date TIMESTAMP,
    wo_end_date TIMESTAMP,
    wo_duration DOUBLE PRECISION,
    ppm_upm TEXT,
    labor_cost DOUBLE PRECISION,
    material_cost DOUBLE PRECISION,
    other_cost DOUBLE PRECISION,
    total_cost DOUBLE PRECISION,
    labor_hours DOUBLE PRECISION,
    min_temp_c DOUBLE PRECISION,
    max_temp_c DOUBLE PRECISION,
    atmospheric_pressure_hpa DOUBLE PRECISION,
    humidity_pct DOUBLE PRECISION,
    wind_speed_ms DOUBLE PRECISION,
    wind_degree DOUBLE PRECISION,
    precipitation_mm DOUBLE PRECISION,
    snow_mm DOUBLE PRECISION,
    cloudness_pct DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_fmucd_building_id ON fmucd(building_id);
CREATE INDEX IF NOT EXISTS idx_fmucd_wo_id ON fmucd(wo_id);
CREATE INDEX IF NOT EXISTS idx_fmucd_wo_start_date ON fmucd(wo_start_date);
CREATE INDEX IF NOT EXISTS idx_fmucd_system_code ON fmucd(system_code);

-- Enable Row Level Security (optional - disable for service role access)
-- ALTER TABLE fmucd ENABLE ROW LEVEL SECURITY;
