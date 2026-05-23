import csv
import json
import sys
from pathlib import Path

from psycopg2.extras import execute_values, Json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils import get_database_connection_details, aws_to_psycopg2_format, return_dbConn_psycopg2

CSV_PATH = Path(__file__).resolve().parent / "seeds/01-vehicle_profiles.csv"
TABLE = "vehicle_profiles"
SECRET_NAME = "dev/sense-energy"

# CSV column order (first column is the seed id — not inserted)
CSV_COLUMNS = [
    "_seed_id",
    "make",
    "model",
    "trim",
    "model_year",
    "total_battery_capacity_kwh",
    "usable_battery_capacity_kwh",
    "vehicle_class",
    "chemistry",
    "peak_dc_power_kW",
    "curve_type",
    "curve_points",
    "source_url",
    "notes",
]

DB_COLUMNS = [c for c in CSV_COLUMNS if c != "_seed_id"]


def parse_rows():
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for raw in csv.reader(f):
            if not any(raw):
                continue
            d = dict(zip(CSV_COLUMNS, raw))
            rows.append((
                d["make"].strip(),
                d["model"].strip(),
                d["trim"].strip() or None,
                int(d["model_year"].strip()),
                float(d["total_battery_capacity_kwh"].strip()),
                float(d["usable_battery_capacity_kwh"].strip()),
                d["vehicle_class"].strip(),
                d["chemistry"].strip(),
                float(d["peak_dc_power_kW"].strip()),
                d["curve_type"].strip(),
                Json(json.loads(d["curve_points"].strip())),
                d["source_url"].strip() or None,
                d["notes"].strip() or None,
            ))
    return rows


def main():
    db_params = get_database_connection_details(SECRET_NAME)
    conn = return_dbConn_psycopg2(aws_to_psycopg2_format(db_params))

    rows = parse_rows()

    # Columns that are part of the unique constraint — excluded from the SET clause
    conflict_cols = {"make", "model", "trim", "model_year", "total_battery_capacity_kwh"}
    update_cols = [c for c in DB_COLUMNS if c not in conflict_cols]

    col_list = ", ".join(f'"{c}"' for c in DB_COLUMNS)
    set_clause = ", ".join(f'"{c}" = EXCLUDED."{c}"' for c in update_cols)

    sql = f"""
        INSERT INTO {TABLE} ({col_list})
        VALUES %s
        ON CONFLICT ON CONSTRAINT uq_vehicle_variant DO UPDATE SET
            {set_clause}
    """

    with conn.cursor() as cur:
        execute_values(cur, sql, rows)

    conn.commit()
    conn.close()
    print(f"Loaded {len(rows)} vehicle profiles into '{TABLE}'.")


if __name__ == "__main__":
    main()
