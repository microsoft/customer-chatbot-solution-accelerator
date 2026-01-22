import argparse
import csv
import os
import sys
from time import sleep
from typing import Any, Dict

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure_credential_utils import get_azure_credential
from dotenv import load_dotenv

load_dotenv()


p = argparse.ArgumentParser()
p.add_argument("--cosmosdb_account", required=True)
args = p.parse_args()

# ENDPOINT = f"https://{os.getenv('AZURE_COSMOSDB_ACCOUNT')}.documents.azure.com:443/"

ENDPOINT = f"https://{args.cosmosdb_account}.documents.azure.com:443/"
print(f"Cosmos DB Endpoint: {ENDPOINT}")
DB_NAME = os.getenv("AZURE_COSMOSDB_DATABASE", "ecommerce_db")
CONTAINER_NAME = "products"
CSV_PATH = "infra/data/products/products.csv"
PARTITION_KEY_PATH = "/productId"

if not ENDPOINT:
    sys.exit("Missing COSMOS_ENDPOINT in environment variables.")

# credential = DefaultAzureCredential()


credential = get_azure_credential()
# Shared credential
# credential = get_azure_credential(client_id=MANAGED_IDENTITY_CLIENT_ID)
# credential = get_azure_credential()

# Create Cosmos client using Entra ID / Managed Identity
client = CosmosClient(ENDPOINT, credential=credential)


def get_or_create_database(db_name: str):
    try:
        database = client.create_database_if_not_exists(id=db_name)
        print(f"Database '{db_name}' ready.")
        return database
    except exceptions.CosmosHttpResponseError as e:
        sys.exit(f"Error creating database: {e}")


def get_or_create_container(database, container_name: str, partition_key_path: str):
    try:
        container = database.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path=partition_key_path),
            # offer_throughput=400
        )
        print(
            f"Container '{container_name}' ready with partition key '{partition_key_path}'."
        )
        return container
    except exceptions.CosmosHttpResponseError as e:
        sys.exit(f"Error creating container: {e}")


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    item = dict(row)
    for k, v in list(item.items()):
        if isinstance(v, str):
            item[k] = v.strip()

    # Ensure 'id' exists (Cosmos DB requirement)
    if not item.get("id"):
        item["id"] = item.get("productId") or item.get("productId")
    if not item["id"]:
        raise ValueError("Each item must have a unique 'id' or 'productId'.")

    # Cast Price to float
    if "Price" in item and item["Price"] != "":
        try:
            item["Price"] = float(item["Price"])
        except ValueError:
            pass
    return item


def upsert_with_retry(container, item: Dict[str, Any], max_retries: int = 6):
    backoff = 1.0
    for attempt in range(1, max_retries + 1):
        try:
            return container.upsert_item(item)
        except exceptions.CosmosHttpResponseError as e:
            status = getattr(e, "status_code", None)
            if status in (429, 408, 500, 502, 503, 504):
                sleep(backoff)
                backoff = min(backoff * 2, 16)
                continue
            if status in (401, 403):
                raise SystemExit(
                    "Unauthorized. Ensure your identity has 'Cosmos DB Built-in Data Contributor' role."
                ) from e
            raise


print("Connecting to Cosmos DB (keyless)...")
database = get_or_create_database(DB_NAME)
container = get_or_create_container(database, CONTAINER_NAME, PARTITION_KEY_PATH)

print(f"Importing from '{CSV_PATH}' to container '{CONTAINER_NAME}'...")
count = 0
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        item = normalize_row(row)
        upsert_with_retry(container, item)
        count += 1

print(f"Done! Upserted {count} documents into '{CONTAINER_NAME}'.")
