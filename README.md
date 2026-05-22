# uk-energy-data
This repository builds a structured UK energy dataset using data from the National Grid Open Data platform and stores it in a PostgreSQL database hosted on AWS RDS.

The dataset currently focuses on distribution substation data, sourced from:

https://connecteddata.nationalgrid.co.uk/dataset/distribution-substations

## Architecture
Source: National Grid CKAN API
Storage: AWS RDS (PostgreSQL)
Processing: Python (Pandas-based ETL)
Load method: Bulk ingestion using PostgreSQL COPY (Better performance compared to row by row upsert using sqlachemy)

The ETL pipeline extracts raw data from the API, transforms it using Pandas, and loads it into a structured relational database for fast querying and analysis.

## Database
The PostgreSQL database is hosted on AWS RDS and provides a structured schema for querying energy infrastructure data efficiently.

## Scripts
Migration scripts are numbered and must be run in order:

| Script | Description |
|---|---|
| `scripts/01-roles.sql` | Creates database users and access privileges |
| `scripts/02-ddl.sql` | Creates all tables |

## Seeds
Reference data is stored in the `seeds/` folder as CSV files and should be loaded after the DDL scripts have been run.


Example command to load seed data using psql:
```bash
psql -h <host> -U <user> -d postgres -c "\COPY public.vehicle_profiles(id, make, model, trim, model_year, battery_capacity_kwh, vehicle_class, chemistry, voltage_architecture, \"peak_dc_power_kW\", curve_type, curve_points, source_url, notes) OVERRIDING SYSTEM VALUE FROM 'seeds/01-vehicle_profiles.csv' CSV"
```

## Setup Instructions
To replicate this project:
1. Set up AWS account
2. Create a Postgres RDS instance on AWS
3. Run `scripts/01-roles.sql` to create database users
4. Run `scripts/02-ddl.sql` to create the schema
5. Load seed data from the `seeds/` folder
6. Create National Grid account and obtain API key
7. Install the packages in `requirements.txt`
8. Run `substation_harvester.py`
9. Run `substation_transform_load.py`
