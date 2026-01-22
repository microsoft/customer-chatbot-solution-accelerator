# from azure.keyvault.secrets import SecretClient
import argparse
import os
import re
import time

from azure.identity import AzureCliCredential, get_bearer_token_provider
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    VectorSearch,
    VectorSearchProfile,
)
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


INDEX_NAME = "policies_index"

# Delete the search index

# search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
# openai_resource_url = os.getenv("AZURE_OPENAI_ENDPOINT")
# embedding_model = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")

search_endpoint = args.ai_search_endpoint
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
# openai_api_base = os.getenv("AZURE_OPENAI_ENDPOINT")

# search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
openai_api_base = args.azure_openai_endpoint
search_endpoint = args.ai_search_endpoint

credential = get_azure_credential()
search_client = SearchClient(
    endpoint=search_endpoint, index_name=INDEX_NAME, credential=credential
)


# Utility functions
def get_embeddings(text: str, openai_api_base, openai_api_version):
    model_id = "text-embedding-ada-002"
    # token_provider = get_bearer_token_provider(
    #     get_azure_credential(client_id=MANAGED_IDENTITY_CLIENT_ID),
    #     "https://cognitiveservices.azure.com/.default"
    # )
    token_provider = get_bearer_token_provider(
        AzureCliCredential(), "https://cognitiveservices.azure.com/.default"
    )
    client = AzureOpenAI(
        api_version=openai_api_version,
        azure_endpoint=openai_api_base,
        azure_ad_token_provider=token_provider,
    )
    embedding = client.embeddings.create(input=text, model=model_id).data[0].embedding
    return embedding


def clean_spaces_with_regex(text):
    cleaned_text = re.sub(r"\s+", " ", text)
    cleaned_text = re.sub(r"\.{2,}", ".", cleaned_text)
    return cleaned_text


def chunk_data(text, tokens_per_chunk=1024):
    text = clean_spaces_with_regex(text)
    sentences = text.split(". ")
    chunks, current_chunk, current_chunk_token_count = [], "", 0
    for sentence in sentences:
        tokens = sentence.split()
        if current_chunk_token_count + len(tokens) <= tokens_per_chunk:
            current_chunk += (". " if current_chunk else "") + sentence
            current_chunk_token_count += len(tokens)
        else:
            chunks.append(current_chunk)
            current_chunk, current_chunk_token_count = sentence, len(tokens)
    if current_chunk:
        chunks.append(current_chunk)
    return chunks


def prepare_search_doc(content, document_id, path_name):
    docs = []
    try:
        v_contentVector = get_embeddings(
            str(content), openai_api_base, openai_api_version
        )
    except Exception:
        time.sleep(30)
        try:
            v_contentVector = get_embeddings(
                str(content), openai_api_base, openai_api_version
            )
        except Exception:
            v_contentVector = []

    docs.append(
        {
            "id": document_id,
            "content": content,
            "sourceurl": path_name,
            "contentVector": v_contentVector,
        }
    )
    return docs


docs = []
counter = 0
# List all .txt files in the policies folder
folder_path = "infra/data/policies/"
txt_files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]

# Loop through and read each file
for filename in txt_files:
    file_path = os.path.join(folder_path, filename)
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        id = filename.split(".txt")[0].strip()
        docs.extend(prepare_search_doc(content, id, file_path))
        counter += 1
        if docs != [] and counter % 20 == 0:
            result = search_client.upload_documents(documents=docs)
            docs = []
            print(f"{counter} uploaded to Azure Search.")

if docs != []:
    result = search_client.upload_documents(documents=docs)
    print(f"{len(docs)} uploaded to Azure Search.")

# df_products = pd.read_csv('infra/data/products/products.csv')
# docs = []
# counter = 0
# for _, row in df_products.iterrows():
#     print('Uploading productId:', row['ProductID'])
#     content = f'ProductID: {row["ProductID"]}. ProductName: {row["ProductName"]}. ProductCategory: {row["ProductCategory"]}. Price: {row["Price"]}. ProductDescription: {row["ProductDescription"]}. ProductPunchLine: {row["ProductPunchLine"]}. ImageURL: {row["ImageURL"]}.'
#     docs.extend(prepare_search_doc(content, row['ProductID'], row['ImageURL']))
#     # print(docs)
#     counter += 1
#     if docs != [] and counter % 20 == 0:
#         result = search_client.upload_documents(documents=docs)
#         docs = []
#         print(f'{counter} uploaded to Azure Search.')
#     break

# if docs != []:
#     result = search_client.upload_documents(documents=docs)
#     print(f'{len(docs)} uploaded to Azure Search.')
