-- Enterprise logistics tracking schema (PostgreSQL / compatible)
-- Supports real-time GPS pings, shipment lifecycle, and analytics

CREATE SCHEMA IF NOT EXISTS logistics;

-- Dimension tables
CREATE TABLE logistics.dim_customer (
    customer_id       SERIAL PRIMARY KEY,
    customer_name     VARCHAR(255) NOT NULL UNIQUE,
    customer_tier     VARCHAR(32),
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE logistics.dim_supplier (
    supplier_id       SERIAL PRIMARY KEY,
    supplier_name     VARCHAR(255) NOT NULL UNIQUE,
    specialization    VARCHAR(64),
    gps_provider      VARCHAR(64),
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE logistics.dim_vehicle (
    vehicle_id        SERIAL PRIMARY KEY,
    registration      VARCHAR(32) NOT NULL UNIQUE,
    vehicle_type      VARCHAR(128),
    min_daily_km      NUMERIC(10,2),
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE logistics.dim_driver (
    driver_id         SERIAL PRIMARY KEY,
    driver_name       VARCHAR(255),
    mobile_no         VARCHAR(20),
    supplier_id       INT REFERENCES logistics.dim_supplier(supplier_id),
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE logistics.dim_location (
    location_id       SERIAL PRIMARY KEY,
    location_name     VARCHAR(255) NOT NULL,
    latitude          NUMERIC(10,6),
    longitude         NUMERIC(10,6),
    region            VARCHAR(64),
    UNIQUE (location_name, latitude, longitude)
);

-- Fact: shipment booking / lifecycle
CREATE TABLE logistics.fact_shipment (
    shipment_id           BIGSERIAL PRIMARY KEY,
    booking_id            VARCHAR(64) NOT NULL UNIQUE,
    shipment_type         VARCHAR(32),
    booking_ts            TIMESTAMPTZ NOT NULL,
    customer_id           INT REFERENCES logistics.dim_customer(customer_id),
    supplier_id           INT REFERENCES logistics.dim_supplier(supplier_id),
    vehicle_id            INT REFERENCES logistics.dim_vehicle(vehicle_id),
    driver_id             INT REFERENCES logistics.dim_driver(driver_id),
    origin_location_id    INT REFERENCES logistics.dim_location(location_id),
    dest_location_id      INT REFERENCES logistics.dim_location(location_id),
    material_code         VARCHAR(255),
    distance_km           NUMERIC(10,2),
    geo_distance_km       NUMERIC(10,2),
    route_detour_ratio    NUMERIC(8,4),
    trip_start_ts         TIMESTAMPTZ,
    trip_end_ts           TIMESTAMPTZ,
    planned_eta_ts        TIMESTAMPTZ,
    actual_eta_ts         TIMESTAMPTZ,
    is_ontime             BOOLEAN,
    wait_hours            NUMERIC(10,2),
    moving_hours          NUMERIC(10,2),
    unloading_hours       NUMERIC(10,2),
    delay_hours           NUMERIC(10,2),
    idle_days_proxy       NUMERIC(10,2),
    risk_score            NUMERIC(5,2),
    created_at            TIMESTAMPTZ DEFAULT NOW(),
    updated_at            TIMESTAMPTZ DEFAULT NOW()
);

-- Fact: GPS pings (high-frequency)
CREATE TABLE logistics.fact_gps_ping (
    ping_id           BIGSERIAL PRIMARY KEY,
    booking_id        VARCHAR(64) NOT NULL,
    ping_ts           TIMESTAMPTZ NOT NULL,
    latitude          NUMERIC(10,6) NOT NULL,
    longitude         NUMERIC(10,6) NOT NULL,
    speed_kmph        NUMERIC(8,2),
    heading_deg       NUMERIC(6,2),
    is_idle           BOOLEAN DEFAULT FALSE,
    gps_provider      VARCHAR(64),
    ingest_ts         TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_gps_booking_time ON logistics.fact_gps_ping (booking_id, ping_ts);
CREATE INDEX idx_shipment_supplier ON logistics.fact_shipment (supplier_id);
CREATE INDEX idx_shipment_route ON logistics.fact_shipment (origin_location_id, dest_location_id);

-- ML predictions store
CREATE TABLE logistics.fact_prediction (
    prediction_id     BIGSERIAL PRIMARY KEY,
    booking_id        VARCHAR(64) NOT NULL,
    model_name        VARCHAR(64) NOT NULL,
    model_version     VARCHAR(32),
    predicted_eta_ts  TIMESTAMPTZ,
    predicted_delay_h NUMERIC(10,2),
    late_probability  NUMERIC(6,4),
    risk_score        NUMERIC(5,2),
    scored_at         TIMESTAMPTZ DEFAULT NOW()
);

-- Materialized view for executive dashboard
CREATE MATERIALIZED VIEW logistics.mv_supplier_segment_kpi AS
SELECT
    s.supplier_id,
    CASE
        WHEN f.distance_km <= 100 THEN '0-100km'
        WHEN f.distance_km <= 300 THEN '100-300km'
        WHEN f.distance_km <= 600 THEN '300-600km'
        WHEN f.distance_km <= 1200 THEN '600-1200km'
        ELSE '1200km+'
    END AS distance_band,
    v.vehicle_type,
    COUNT(*) AS bookings,
    AVG(CASE WHEN f.is_ontime THEN 1.0 ELSE 0.0 END) AS ontime_rate,
    AVG(f.delay_hours) AS avg_delay_hours,
    AVG(f.trip_start_ts - f.booking_ts) AS avg_wait_interval
FROM logistics.fact_shipment f
JOIN logistics.dim_supplier s ON f.supplier_id = s.supplier_id
JOIN logistics.dim_vehicle v ON f.vehicle_id = v.vehicle_id
GROUP BY 1, 2, 3;
