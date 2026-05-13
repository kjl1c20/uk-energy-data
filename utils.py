import os
from pathlib import Path
from sqlalchemy import create_engine
import psycopg2
from dotenv import load_dotenv
from pyiceberg.catalog import load_catalog
import json
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig
from botocore.exceptions import ClientError
from urllib.parse import quote_plus as urlquote
import logging
import sys
import traceback
import boto3

load_dotenv(Path(__file__).resolve().parent / ".env")

SENSE_CATALOG_URL = "https://catalog.sdr-sense.org.uk/api/catalog"

def connect_to_warehouse(warehouse_slug):
    """Connect to a specific SENSE organisation catalog."""
    client_id = os.environ.get("SENSE_CLIENT_ID")
    client_secret = os.environ.get("SENSE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError(
            "Set SENSE_CLIENT_ID and SENSE_CLIENT_SECRET in .env "
            "(or export them in the environment)."
        )

    return load_catalog(
        "sense",
        **{
            "type": "rest",
            "uri": SENSE_CATALOG_URL,
            "credential": f"{client_id}:{client_secret}",
            "scope": "PRINCIPAL_ROLE:ALL",
            "warehouse": warehouse_slug,
        }
    )

def get_database_connection_details(secret_name: str) -> dict:
    """Retrieve database connection details from AWS Secrets Manager."""
    region_name = "eu-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    logger = logging.getLogger()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    cache_config = SecretCacheConfig() # See below for defaults
    cache = SecretCache(config=cache_config, client=client)
    
    #print(cache)

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_string = cache.get_secret_string(secret_name)
        get_secret_value_response = json.loads(get_secret_value_string)
        #print(secret_name)
        #get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        if e.response["Error"]["Code"] == "DecryptionFailureException":
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response["Error"]["Code"] == "InternalServiceErrorException":
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response["Error"]["Code"] == "InvalidParameterException":
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response["Error"]["Code"] == "InvalidRequestException":
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response["Error"]["Code"] == "ResourceNotFoundException":
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        else:
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        '''if "SecretString" in get_secret_value_response:
            secret = get_secret_value_response["SecretString"]
            return ast.literal_eval(
                secret
            )  # evaluate the string as a python dictionary
        else:
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response["SecretBinary"]
            )'''
        return get_secret_value_response


def aws_to_psycopg2_format(db_conn_params: dict) -> dict:
    """Create psycopg2 connection dictionary from AWS Secrets Manager db connection dict."""
    #  create a new dictionary to contain fields with the right name and information
    dbParams = {}
    #  name of db connection used in quantAnalytics/ name of db connection stored in Secrets manager
    dbParams["type"] = "postgresql"
    dbParams["host"] = db_conn_params["host"]
    dbParams["port"] = db_conn_params["port"]
    dbParams["user"] = db_conn_params["username"]
    dbParams["passwd"] = db_conn_params["password"]
    dbParams["database"] = "postgres"   # db_conn_params["dbname"]
    dbParams["schema"] = "public"
    return dbParams



def return_dbConn_psycopg2(dbParamDetails):
    """Return connection to database given dictionary of details."""
    dbConn = psycopg2.connect(
        host=dbParamDetails["host"],
        port=dbParamDetails["port"],
        dbname=dbParamDetails["database"],
        user=dbParamDetails["user"],
        password=dbParamDetails["passwd"],
        # keepalive = 1,
             
    )
    return dbConn


def return_dbConn_sqlalchemy(dbParamDetails):
    db_URI = "postgresql+psycopg2://%s:%s@%s:%s/%s" % (
        dbParamDetails["user"],
        urlquote(dbParamDetails["passwd"]),
        dbParamDetails["host"],
        dbParamDetails["port"],
        dbParamDetails["database"],
    )
    engine = create_engine(db_URI, connect_args = {'connect_timeout': 1200})
    return engine


def exception_handler(e):
    #Little helper function, given an exeption 'e' it will output the full trace to logs
    logging.error(f"Raised error is {e}")
    exception_type, exception_object, exception_traceback = sys.exc_info()
    error_traces = traceback.extract_tb(exception_traceback)
    traceback_count = 1
    for error_trace in error_traces:
        logging.error(f"Traceback level {traceback_count} = {error_trace}")
        traceback_count += 1