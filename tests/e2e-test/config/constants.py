import os

from dotenv import load_dotenv

__all__ = [
    "WEB_URL",
    "json_file_path",
    "admin_page_title",
    "upload_file_success_message",
    "upload_page_url",
    "upload_url_success_message",
    "unsupported_file_message",
    "no_files_to_delete_message",
    "user_page_title",
    "invalid_response",
]

load_dotenv()
WEB_URL = os.getenv("url") or os.getenv("web_url")
if not WEB_URL:
    raise ValueError("WEB_URL environment variable is not set. Please set 'url' or 'web_url' environment variable.")
if WEB_URL.endswith("/"):
    WEB_URL = WEB_URL[:-1]


# Get the absolute path to the repository root
repo_root = os.getenv("GITHUB_WORKSPACE", os.getcwd())

# Construct the absolute path to the JSON file
# note: may have to remove 'tests/e2e-test' from below when running locally
json_file_path = os.path.join(
    repo_root,"tests/e2e-test","testdata", "golden_path_data.json"
    )


# Admin Page input data
admin_page_title = "Chat with your data Solution Accelerator"
upload_file_success_message = "Embeddings computation in progress."
upload_page_url = "https://plasticsmartcities.org/public-awareness/"
upload_url_success_message = "Embeddings added successfully for"
unsupported_file_message = "application/json files are not allowed."
no_files_to_delete_message = "No files to delete"

# Web User Page input data
user_page_title = "Azure AI"
invalid_response = "The requested information is not available in the retrieved data. Please try another query or topic.AI-generated content may be incorrect"
