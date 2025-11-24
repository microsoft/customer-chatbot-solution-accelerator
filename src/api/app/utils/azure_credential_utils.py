import os
from azure.identity import ManagedIdentityCredential, DefaultAzureCredential
from azure.identity.aio import ManagedIdentityCredential as AioManagedIdentityCredential, DefaultAzureCredential as AioDefaultAzureCredential

async def get_azure_credential_async(client_id=None):
    if os.getenv("APP_ENV", "prod").lower() == 'dev':
        return AioDefaultAzureCredential()
    else:
        return AioManagedIdentityCredential(client_id=client_id)

def get_azure_credential(client_id=None):
    if os.getenv("APP_ENV", "prod").lower() == 'dev':
        return DefaultAzureCredential()
    else:
        return ManagedIdentityCredential(client_id=client_id)



