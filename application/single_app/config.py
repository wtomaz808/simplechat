import os
import requests
import uuid
import tempfile
import json
import openai
import pandas as pd
import time
import threading
import random
import base64

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory, send_file
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
from functools import wraps
from msal import ConfidentialClientApplication
from flask_session import Session
from uuid import uuid4
from threading import Thread
from openai import AzureOpenAI
from cryptography.fernet import Fernet, InvalidToken

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.search.documents import SearchClient, IndexDocumentsBatch
from azure.search.documents.models import VectorizedQuery
from azure.core.exceptions import AzureError
from azure.core.polling import LROPoller

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SESSION_TYPE'] = 'filesystem'
app.config['VERSION'] = '0.162.noencryption'
Session(app)

ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'docx', 'xlsx', 'xls', 'csv', 'pptx', 'html', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'heif', 'md', 'json'
}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

# Azure AD Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("MICROSOFT_PROVIDER_AUTHENTICATION_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.us/{TENANT_ID}"
SCOPE = ["User.Read"]  # Adjust scope according to your needs

# Azure Document Intelligence Configuration
AZURE_DI_ENDPOINT = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
AZURE_DI_KEY = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

document_intelligence_client_old = DocumentIntelligenceClient(
    endpoint=AZURE_DI_ENDPOINT,
    credential=AzureKeyCredential(AZURE_DI_KEY)
)

azure_fr_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
azure_fr_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

document_intelligence_client = DocumentAnalysisClient(
    endpoint=azure_fr_endpoint,
    credential=AzureKeyCredential(azure_fr_key)
)

# Configure Azure OpenAI
openai.api_type = "azure"
openai.api_key = os.getenv("AZURE_OPENAI_KEY")
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
llm_model = os.getenv("AZURE_OPENAI_LLM_MODEL")
embedding_model = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")

AZURE_OPENAI_GPT_KEY = os.getenv("AZURE_OPENAI_GPT_KEY")
AZURE_OPENAI_EMBEDDING_KEY = os.getenv("AZURE_OPENAI_EMBEDDING_KEY")
AZURE_OPENAI_IMAGE_GEN_KEY = os.getenv("AZURE_OPENAI_IMAGE_GEN_KEY")

AZURE_AI_SEARCH_ENDPOINT = os.getenv('AZURE_AI_SEARCH_ENDPOINT')
AZURE_AI_SEARCH_KEY = os.getenv('AZURE_AI_SEARCH_KEY')
AZURE_AI_SEARCH_USER_INDEX = os.getenv('AZURE_AI_SEARCH_USER_INDEX')

BING_SEARCH_ENDPOINT = os.getenv("BING_SEARCH_ENDPOINT")
BING_SEARCH_KEY = os.getenv("BING_SEARCH_KEY")

# Initialize Azure Cosmos DB client
cosmos_endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
cosmos_key = os.getenv("AZURE_COSMOS_KEY")
cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
database_name = os.getenv("AZURE_COSMOS_DB_NAME")
container_name = os.getenv("AZURE_COSMOS_CONVERSATIONS_CONTAINER_NAME")
database = cosmos_client.create_database_if_not_exists(database_name)
container = database.create_container_if_not_exists(
    id=container_name,
    partition_key=PartitionKey(path="/id"),
    offer_throughput=400
)
documents_container_name = os.getenv("AZURE_COSMOS_DOCUMENTS_CONTAINER_NAME", "documents")
documents_container = database.create_container_if_not_exists(
    id=documents_container_name,
    partition_key=PartitionKey(path="/id"),
    offer_throughput=400
)

search_client_user = SearchClient(
    endpoint=AZURE_AI_SEARCH_ENDPOINT,
    index_name=AZURE_AI_SEARCH_USER_INDEX,
    credential=AzureKeyCredential(AZURE_AI_SEARCH_KEY)
)

settings_container_name = "settings"
settings_container = database.create_container_if_not_exists(
    id=settings_container_name,
    partition_key=PartitionKey(path="/id"),
    offer_throughput=400
)

