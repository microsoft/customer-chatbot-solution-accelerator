# from azure.keyvault.secrets import SecretClient
import argparse
import time

import pandas as pd
from azure.identity import AzureCliCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    AzureOpenAIVectorizer, AzureOpenAIVectorizerParameters,
    HnswAlgorithmConfiguration, SearchField, SearchFieldDataType, SearchIndex,
    SemanticConfiguration, SemanticField, SemanticPrioritizedFields,
    SemanticSearch, VectorSearch, VectorSearchProfile)
from azure_credential_utils import get_azure_credential
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

p = argparse.ArgumentParser()
p.add_argument("--ai_search_endpoint", required=True)
p.add_argument("--azure_openai_endpoint", required=True)
p.add_argument("--embedding_model_name", required=True)
args = p.parse_args()


INDEX_NAME = "products_index"

# Delete the search index

# search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
# openai_resource_url = os.getenv("AZURE_OPENAI_ENDPOINT")
# embedding_model = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")


search_endpoint = args.ai_search_endpoint
print("Search Endpoint:", search_endpoint)
openai_resource_url = args.azure_openai_endpoint
embedding_model = args.embedding_model_name

credential = get_azure_credential()
# Shared credential
# credential = get_azure_credential(client_id=MANAGED_IDENTITY_CLIENT_ID)
# credential = get_azure_credential()

search_index_client = SearchIndexClient(search_endpoint, credential=credential)
search_index_client.delete_index(INDEX_NAME)


def create_search_index():
    """
    Creates or updates an Azure Cognitive Search index configured for:
    - Text fields
    - Vector search using Azure OpenAI embeddings
    - Semantic search using prioritized fields
    """

    index_client = SearchIndexClient(endpoint=search_endpoint, credential=credential)

    # Define index schema
    fields = [
        SearchField(name="id", type=SearchFieldDataType.String, key=True),
        SearchField(name="content", type=SearchFieldDataType.String),
        SearchField(name="sourceurl", type=SearchFieldDataType.String),
        SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            vector_search_dimensions=1536,
            vector_search_profile_name="myHnswProfile",
        ),
    ]

    # Define vector search settings
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="myHnsw")],
        profiles=[
            VectorSearchProfile(
                name="myHnswProfile",
                algorithm_configuration_name="myHnsw",
                vectorizer_name="myOpenAI",
            )
        ],
        vectorizers=[
            AzureOpenAIVectorizer(
                vectorizer_name="myOpenAI",
                kind="azureOpenAI",
                parameters=AzureOpenAIVectorizerParameters(
                    resource_url=openai_resource_url,
                    deployment_name=embedding_model,
                    model_name=embedding_model,
                ),
            )
        ],
    )

    # Define semantic configuration
    semantic_config = SemanticConfiguration(
        name="my-semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            keywords_fields=[SemanticField(field_name="id")],
            content_fields=[SemanticField(field_name="content")],
        ),
    )

    # Create the semantic settings with the configuration
    semantic_search = SemanticSearch(configurations=[semantic_config])

    # Define and create the index
    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search,
    )

    result = index_client.create_or_update_index(index)
    print(f"Search index '{result.name}' created or updated successfully.")


create_search_index()


openai_api_version = "2025-01-01-preview"
openai_api_base = args.azure_openai_endpoint
search_endpoint = args.ai_search_endpoint

credential = get_azure_credential()
search_client = SearchClient(
    endpoint=search_endpoint, index_name=INDEX_NAME, credential=credential
)


def get_embeddings_batch(
    texts: list, openai_api_base, openai_api_version, batch_size=50
):
    """Get embeddings for multiple texts in batches"""
    model_id = "text-embedding-ada-002"
    token_provider = get_bearer_token_provider(
        AzureCliCredential(), "https://cognitiveservices.azure.com/.default"
    )
    client = AzureOpenAI(
        api_version=openai_api_version,
        azure_endpoint=openai_api_base,
        azure_ad_token_provider=token_provider,
    )

    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            response = client.embeddings.create(input=batch, model=model_id)
            batch_embeddings = [data.embedding for data in response.data]
            all_embeddings.extend(batch_embeddings)
        except Exception as e:
            print(f"Batch embedding failed: {e}, retrying individual items...")
            # Fallback to individual processing for this batch
            for text in batch:
                try:
                    embedding = (
                        client.embeddings.create(input=text, model=model_id)
                        .data[0]
                        .embedding
                    )
                    all_embeddings.append(embedding)
                except Exception:
                    all_embeddings.append([])
            time.sleep(1)
    return all_embeddings


df_products = pd.read_csv("infra/data/products/products.csv")
# Prepare all content first
print("Preparing content for batch processing...")
all_content = []
all_product_ids = []
all_images = []

for _, row in df_products.iterrows():
    content = f'productId: {row["productId"]}. ProductName: {row["title"]}. ProductCategory: {row["category"]}. Price: {row["price"]}. ProductDescription: {row["description"]}. ProductPunchLine: {row["punchLine"]}. ImageURL: {row["image"]}.'
    all_content.append(content)
    all_product_ids.append(row["productId"])
    all_images.append(row["image"])

# Get all embeddings in batches
print(f"Getting embeddings for {len(all_content)} products in batches...")
all_embeddings = get_embeddings_batch(all_content, openai_api_base, openai_api_version)

# Prepare documents for upload
docs = []
for i, (content, product_id, image, embedding) in enumerate(
    zip(all_content, all_product_ids, all_images, all_embeddings)
):
    print(f"Preparing document {i+1}/{len(all_content)}: productId {product_id}")
    docs.append(
        {
            "id": product_id,
            "content": content,
            "sourceurl": image,
            "contentVector": embedding,
        }
    )

    # Upload in batches of 20
    if len(docs) == 20:
        search_client.upload_documents(documents=docs)
        print(f"{i+1} documents uploaded to Azure Search.")
        docs = []

# Upload remaining documents
if docs:
    search_client.upload_documents(documents=docs)
    print(f"Final {len(docs)} documents uploaded to Azure Search.")
