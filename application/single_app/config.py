# config.py

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
import markdown2
import re

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory, send_file, Markup
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
from functools import wraps
from msal import ConfidentialClientApplication
from flask_session import Session
from uuid import uuid4
from threading import Thread
from openai import AzureOpenAI, RateLimitError
from cryptography.fernet import Fernet, InvalidToken
from urllib.parse import quote

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.search.documents import SearchClient, IndexDocumentsBatch
from azure.search.documents.models import VectorizedQuery
from azure.core.exceptions import AzureError, ResourceNotFoundError, HttpResponseError
from azure.core.polling import LROPoller
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.identity import ClientSecretCredential
from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions, TextCategory

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SESSION_TYPE'] = 'filesystem'
app.config['VERSION'] = '0.197.14'
Session(app)

CLIENTS = {}
CLIENTS_LOCK = threading.Lock()

ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'docx', 'xlsx', 'xls', 'csv', 'pptx', 'html', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'heif', 'md', 'json'
}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

# Azure AD Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
APP_URI = f"api://{CLIENT_ID}"
CLIENT_SECRET = os.getenv("MICROSOFT_PROVIDER_AUTHENTICATION_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.us/{TENANT_ID}"
SCOPE = ["User.Read"]  # Adjust scope according to your needs
MICROSOFT_PROVIDER_AUTHENTICATION_SECRET = os.getenv("MICROSOFT_PROVIDER_AUTHENTICATION_SECRET")    

BING_SEARCH_ENDPOINT = os.getenv("BING_SEARCH_ENDPOINT")

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

settings_container_name = "settings"
settings_container = database.create_container_if_not_exists(
    id=settings_container_name,
    partition_key=PartitionKey(path="/id"),
    offer_throughput=400
)

groups_container_name = "groups"
groups_container = database.create_container_if_not_exists(
    id=groups_container_name,
    partition_key=PartitionKey(path="/id"),
    offer_throughput=400
)

group_documents_container_name = "group_documents"
group_documents_container = database.create_container_if_not_exists(
    id=group_documents_container_name,
    partition_key=PartitionKey(path="/id"),
    offer_throughput=400
)

user_settings_container_name = "user_settings"
user_settings_container = database.create_container_if_not_exists(
    id=user_settings_container_name,
    partition_key=PartitionKey(path="/id"),
    offer_throughput=400
)

safety_container_name = "safety"
safety_container = database.create_container_if_not_exists(
    id=safety_container_name,
    partition_key=PartitionKey(path="/id"),
    offer_throughput=400
)

def initialize_clients(settings):
    """
    Initialize/re-initialize all your clients based on the provided settings.
    Store them in a global dictionary so they're accessible throughout the app.
    """
    with CLIENTS_LOCK:
        form_recognizer_endpoint = settings.get("azure_document_intelligence_endpoint")
        form_recognizer_key = settings.get("azure_document_intelligence_key")

        azure_ai_search_endpoint = settings.get("azure_ai_search_endpoint")
        azure_ai_search_key = settings.get("azure_ai_search_key")

        document_intelligence_client = DocumentAnalysisClient(
            endpoint=form_recognizer_endpoint,
            credential=AzureKeyCredential(form_recognizer_key)
        )

        search_client_user = SearchClient(
            endpoint=azure_ai_search_endpoint,
            index_name="simplechat-user-index",
            credential=AzureKeyCredential(azure_ai_search_key)
        )

        search_client_group = SearchClient(
            endpoint=azure_ai_search_endpoint,
            index_name="simplechat-group-index",
            credential=AzureKeyCredential(azure_ai_search_key)
        )

        # 2) Content Safety init if enabled
        if settings.get("enable_content_safety"):
            safety_endpoint = settings.get("content_safety_endpoint", "")
            safety_key = settings.get("content_safety_key", "")

            if safety_endpoint and safety_key:
                try:
                    content_safety_client = ContentSafetyClient(
                        endpoint=safety_endpoint,
                        credential=AzureKeyCredential(safety_key)
                    )
                    CLIENTS["content_safety_client"] = content_safety_client
                except Exception as e:
                    print(f"Failed to initialize Content Safety client: {e}")
            else:
                print("Content Safety enabled, but endpoint/key not provided.")
        else:
            if "content_safety_client" in CLIENTS:
                del CLIENTS["content_safety_client"]

        CLIENTS["document_intelligence_client"] = document_intelligence_client
        CLIENTS["search_client_user"] = search_client_user
        CLIENTS["search_client_group"] = search_client_group