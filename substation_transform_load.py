import pandas as pd
from io import StringIO
from utils import get_database_connection_details, aws_to_psycopg2_format, return_dbConn_psycopg2

# Target PostgreSQL table
TABLE_NAME = "substation"

# read raw data
df = pd.read_parquet("./raw_data/national_grid_substations.parquet")

# standardised raw data column names
df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("-", "_")
)

COLUMN_MAPPING = {
    "substation_name": "name",
    "substation_number": "substation_id",
    "latitude": "latitude",
    "longitude": "longitude",
    "licence_area": "region",
    "substation_rating": "rating",
    "day_max_demand": "day_max_demand",
    "night_max_demand": "night_max_demand"
}

# Rename matching columns
df = df.rename(columns=COLUMN_MAPPING)

# drop null substation_id
df = df.dropna(subset=["substation_id"])

# Mapping data type
df = df.assign(
    substation_id=lambda x: pd.to_numeric(x["substation_id"], errors="coerce").astype("Int64"),
    latitude=lambda x: pd.to_numeric(x["latitude"], errors="coerce"),
    longitude=lambda x: pd.to_numeric(x["longitude"], errors="coerce"),
    rating=lambda x: pd.to_numeric(x["rating"], errors="coerce"),
    day_max_demand=lambda x: pd.to_numeric(x["day_max_demand"], errors="coerce"),
    night_max_demand=lambda x: pd.to_numeric(x["night_max_demand"], errors="coerce")   
)

# CREATE DATABASE CONNECTION
db_conn_params = get_database_connection_details("dev/sense-energy")
dbParamDetails = aws_to_psycopg2_format(db_conn_params)
dbConn = return_dbConn_psycopg2(dbParamDetails)
print(f"Writing data to PostgreSQL table: {TABLE_NAME}")


buffer = StringIO()
df.to_csv(buffer, index=False, header=False)
buffer.seek(0)

# Using copy for better performance in upserting values. The order is must match input df
with dbConn.cursor() as cur:
    cur.copy_expert("""
        COPY substation (
            name, substation_id, latitude, longitude, region,
            rating, day_max_demand, night_max_demand
        )
        FROM STDIN WITH CSV
    """, buffer)

dbConn.commit()
print("Data loaded successfully.")