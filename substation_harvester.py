import pandas as pd
import urllib.request
import urllib.error
from urllib.parse import urlencode
import json
import time

# configuration
BASE_URL = "https://connecteddata.nationalgrid.co.uk/api/3/action/datastore_search"
RESOURCE_ID = "2d95d878-7eb0-4ed4-9be3-4ac926aaf134"
MAX_LIMIT = 32000
OFFSET = 0
# Only harvest necessary fields
FIELDS = [
    "Substation Name",
    "Substation Number",
    "Latitude",
    "Longitude",
    "Licence Area",
    "Substation Rating",
    "Day Max Demand",
    "Night Max Demand"
]
HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI2OGtEcXlfQTJZQk5ZME5WWDZHUTNCWUFvdGJyNHJfWG0weFVrRVg2a2ZSTnFtelRHcTQxbWZoVWE5bkYwUjdva28xV1Bwb0ttRXRPYWtPSCIsImlhdCI6MTc3ODY3OTMyOH0.YenqxRhhnJQnDT3T7WWpAxr5OTd7PEEeYBdGjbc_Na8" 
        }
all_records = []

while True:
    params = {
        "resource_id": RESOURCE_ID,
        "limit": MAX_LIMIT,
        "offset": OFFSET,
        "fields": ",".join(FIELDS)
    }

    url = f"{BASE_URL}?{urlencode(params)}"
    req = urllib.request.Request(url, headers=HEADERS)

    print("Fetching...")

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))

            records = data["result"]["records"]

            if not records:
                break

            all_records.extend(records)

            print(f"Fetched {len(records)} rows at offset {OFFSET}")

            OFFSET += MAX_LIMIT

            time.sleep(0.2)
    except urllib.error.URLError as e:
        raise Exception(f"Error fetching data: {e}") from e

df = pd.DataFrame(all_records)
print("Total rows:", len(df))
df.to_parquet("./raw_data/national_grid_substations.parquet", index=False)