#!/usr/bin/env python3
"""
Script to load FMUCD.csv data into Supabase database.
"""

import os
import csv
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# CSV file path
CSV_FILE = "/home/sradmin/ai-predictive-maintenance-capstone/FMUCD.csv"

# Table name in Supabase
TABLE_NAME = "fmucd"

# Batch size for inserts
BATCH_SIZE = 1000


def clean_value(value, expected_type="text"):
    """Clean and convert CSV values to appropriate types."""
    if value == "" or value is None:
        return None

    if expected_type == "float":
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    elif expected_type == "int":
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    else:
        return value


def process_row(row):
    """Process a CSV row into a dictionary for Supabase insert."""
    return {
        "university_id": clean_value(row.get("UniversityID"), "int"),
        "country": clean_value(row.get("Country")),
        "state_province": clean_value(row.get("State/Province")),
        "building_id": clean_value(row.get("BuildingID")),
        "building_name": clean_value(row.get("BuildingName")),
        "size": clean_value(row.get("Size"), "float"),
        "type": clean_value(row.get("Type")),
        "built_year": clean_value(row.get("BuiltYear"), "int"),
        "fci": clean_value(row.get("FCI (facility condition index)"), "float"),
        "crv": clean_value(row.get("CRV (current replacement value)"), "float"),
        "dmc": clean_value(row.get("DMC (deferred maintenance cost)"), "float"),
        "system_code": clean_value(row.get("SystemCode")),
        "system_description": clean_value(row.get("SystemDescription")),
        "subsystem_code": clean_value(row.get("SubsystemCode")),
        "subsystem_description": clean_value(row.get("SubsystemDescription")),
        "descriptive_code": clean_value(row.get("DescriptiveCode")),
        "component_description": clean_value(row.get("ComponentDescription")),
        "wo_id": clean_value(row.get("WOID")),
        "wo_description": clean_value(row.get("WODescription")),
        "wo_priority": clean_value(row.get("WOPriority"), "int"),
        "wo_start_date": clean_value(row.get("WOStartDate")),
        "wo_end_date": clean_value(row.get("WOEndDate")),
        "wo_duration": clean_value(row.get("WODuration"), "float"),
        "ppm_upm": clean_value(row.get("PPM/UPM")),
        "labor_cost": clean_value(row.get("LaborCost"), "float"),
        "material_cost": clean_value(row.get("MaterialCost"), "float"),
        "other_cost": clean_value(row.get("OtherCost"), "float"),
        "total_cost": clean_value(row.get("TotalCost"), "float"),
        "labor_hours": clean_value(row.get("LaborHours"), "float"),
        "min_temp_c": clean_value(row.get("MinTemp.(°C)"), "float"),
        "max_temp_c": clean_value(row.get("MaxTemp.(°C)"), "float"),
        "atmospheric_pressure_hpa": clean_value(row.get("Atmospheric pressure(hPa)"), "float"),
        "humidity_pct": clean_value(row.get("Humidity(%)"), "float"),
        "wind_speed_ms": clean_value(row.get("WindSpeed(m/s)"), "float"),
        "wind_degree": clean_value(row.get("WindDegree"), "float"),
        "precipitation_mm": clean_value(row.get("Precipitation(mm)"), "float"),
        "snow_mm": clean_value(row.get("Snow(mm)"), "float"),
        "cloudness_pct": clean_value(row.get("Cloudness(%)"), "float"),
    }


def main():
    # Initialize Supabase client with service role key
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    print(f"Loading data from {CSV_FILE}...")
    print(f"Target table: {TABLE_NAME}")

    batch = []
    total_inserted = 0
    errors = 0

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):
            processed = process_row(row)
            batch.append(processed)

            # Insert batch when it reaches BATCH_SIZE
            if len(batch) >= BATCH_SIZE:
                try:
                    response = supabase.table(TABLE_NAME).insert(batch).execute()
                    total_inserted += len(batch)
                    print(f"Inserted {total_inserted} rows...")
                except Exception as e:
                    errors += 1
                    print(f"Error inserting batch at row {i}: {e}")
                    # Try inserting rows one by one to find problematic ones
                    for single_row in batch:
                        try:
                            supabase.table(TABLE_NAME).insert(single_row).execute()
                            total_inserted += 1
                        except Exception as inner_e:
                            print(f"  Failed row: {single_row.get('wo_id')} - {inner_e}")

                batch = []

        # Insert remaining rows
        if batch:
            try:
                response = supabase.table(TABLE_NAME).insert(batch).execute()
                total_inserted += len(batch)
            except Exception as e:
                print(f"Error inserting final batch: {e}")
                for single_row in batch:
                    try:
                        supabase.table(TABLE_NAME).insert(single_row).execute()
                        total_inserted += 1
                    except Exception as inner_e:
                        print(f"  Failed row: {single_row.get('wo_id')} - {inner_e}")

    print(f"\nComplete! Total rows inserted: {total_inserted}")
    if errors > 0:
        print(f"Batch errors encountered: {errors}")


if __name__ == "__main__":
    main()
