"""Central configuration for logistics analytics pipeline."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = PROJECT_ROOT / "Transportation & Logistics Tracking Dataset.xlsx"
PRIMARY_SHEET = "Primary Data"
DICT_SHEET = "Data Dictionary"

# Operational thresholds (tunable per enterprise SLA)
DISTANCE_BINS = [0, 100, 300, 600, 1200, float("inf")]
DISTANCE_LABELS = ["0-100km", "100-300km", "300-600km", "600-1200km", "1200km+"]
URBAN_DISTANCE_KM = 150
LONG_HAUL_DISTANCE_KM = 600

RANDOM_STATE = 42
ML_TEST_SIZE = 0.2

# Column mapping (source -> canonical)
COLUMN_MAP = {
    "Gps Provider": "gps_provider",
    "Booking ID": "booking_id",
    "Shipment Type": "shipment_type",
    "Booking Date": "booking_date",
    "Vehicle Registration": "vehicle_registration",
    "Origin Location": "origin_location",
    "Destination Location": "destination_location",
    "Origin Location Latitude": "origin_lat",
    "Origin Location Longitude": "origin_lon",
    "Destination Location Latitude": "dest_lat",
    "Destination Location Longitude": "dest_lon",
    "Data Ping time": "gps_ping_time",
    "Planned ETA": "planned_eta",
    "Current Location": "current_location",
    "Actual ETA": "actual_eta",
    "Current Location Latitude": "current_lat",
    "Curren Location Longitude": "current_lon",
    "Ontime": "ontime_flag",
    "Trip Start Date": "trip_start",
    "Trip End Date": "trip_end",
    "Transportation Distance (KM)": "distance_km",
    "Vehicle Type": "vehicle_type",
    "Minimum Kms To Be Covered In A Day": "min_daily_km",
    "Driver Name": "driver_name",
    "Driver Mobile No": "driver_mobile",
    "Customer Name": "customer_name",
    "Supplier Name": "supplier_name",
    "Material Shipped": "material_shipped",
}
