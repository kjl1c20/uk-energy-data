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

## Setup Instructions
To replicate this project:
1. Set up AWS account
2. Create a Postgres RDS instance on AWS
3. Execute the ERD model script
4. Create National Grid account and obtain API key
5. Install the packages in the `requirement.txt`
6. Run `substation_harvester.py`
7. Run `substation_transform_load.py`
