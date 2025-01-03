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

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
from functools import wraps
from msal import ConfidentialClientApplication
from flask_session import Session
from uuid import uuid4
from threading import Thread

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.search.documents import SearchClient, IndexDocumentsBatch
from azure.search.documents.models import VectorizedQuery
from azure.core.exceptions import AzureError
from azure.core.polling import LROPoller


#from openai import AzureOpenAI


ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'docx', 'xlsx', 'xls', 'csv', 'pptx', 'html', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'heif', 'md', 'json'
}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

#define the models that you want to be available in the app
MODELS = [
    {"value": "gpt-4o", "label": "GPT-4o", "max_tokens_k": 125},
    {"value": "gpt-4", "label": "GPT-4", "max_tokens_k": 16},
    #{"value": "gpt-3.5-turbo", "label": "GPT-3.5 Turbo"},
    # Add more models as needed
]


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


# client = AzureOpenAI(endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"), api_key=os.getenv("AZURE_OPENAI_KEY"),api_version="2024-07-01-preview")
# deployments = client.list_deployments()
# print('-----------------------------')
# print(f"Deployed models: {deployments}")
# print('-----------------------------')

AZURE_AI_SEARCH_ENDPOINT = os.getenv('AZURE_AI_SEARCH_ENDPOINT')
AZURE_AI_SEARCH_KEY = os.getenv('AZURE_AI_SEARCH_KEY')
AZURE_AI_SEARCH_USER_INDEX = os.getenv('AZURE_AI_SEARCH_USER_INDEX')

BING_SEARCH_ENDPOINT = os.getenv('BING_SEARCH_ENDPOINT')
BING_SEARCH_KEY = os.getenv('BING_SEARCH_KEY')

# Initialize Azure Cosmos DB client
cosmos_endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
cosmos_key = os.getenv("AZURE_COSMOS_KEY")
cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
database_name = os.getenv("AZURE_COSMOS_DB_NAME")
container_name = os.getenv("AZURE_COSMOS_CONVERSATIONS_CONTAINER_NAME")
database = cosmos_client.create_database_if_not_exists(database_name)
documents_container_name = os.getenv("AZURE_COSMOS_DOCUMENTS_CONTAINER_NAME", "documents")
# Retrieve account properties
database_account = cosmos_client.get_database_account()
if hasattr(database_account, 'consistency_policy') and database_account.consistency_policy:
    is_serverless= False
else:
    is_serverless = True

if is_serverless:
    print("The database is serverless.")
    container = database.create_container_if_not_exists(
        id=container_name,
        partition_key=PartitionKey(path="/id")
    )
    documents_container = database.create_container_if_not_exists(
        id=documents_container_name,
        partition_key=PartitionKey(path="/id")
    )    
else:
    print("The database is not serverless.")
    container = database.create_container_if_not_exists(
        id=container_name,
        partition_key=PartitionKey(path="/id"),
        offer_throughput=400
    )
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
if is_serverless:
    settings_container = database.create_container_if_not_exists(
        id=settings_container_name,
        partition_key=PartitionKey(path="/id")
    )
else:
    settings_container = database.create_container_if_not_exists(
        id=settings_container_name,
        partition_key=PartitionKey(path="/id"),
        offer_throughput=400
    )    

def get_settings():
    try:
        settings_item = settings_container.read_item(
            item="app_settings",
            partition_key="app_settings"
        )
        print("Successfully retrieved settings.")
        if 'models' not in settings_item:
            settings_item['models'] = MODELS

        return settings_item
    except CosmosResourceNotFoundError:
        # If settings do not exist, return default settings
        default_settings = {
            'id': 'app_settings',
            'app_title': 'AI Chat Application',
            'max_file_size_mb': 16,
            'conversation_history_limit': 10,
            'default_system_prompt': '',
            'llm_model': 'gpt-3.5-turbo',
            'use_external_apis': False,
            'external_chunking_api': '',
            'external_embedding_api': '',
            'logo_path': 'images/logo.svg',
            'show_logo': False,
            'models': MODELS
        }
        settings_container.create_item(body=default_settings)
        print("Default settings created and returned.")
        return default_settings
    except Exception as e:
        print(f"Error retrieving settings: {str(e)}")
        return None

def update_settings(new_settings):
    try:
        settings_item = get_settings()
        settings_item.update(new_settings)
        settings_container.upsert_item(settings_item)
        print("Settings updated successfully.")
        return True
    except Exception as e:
        print(f"Error updating settings: {str(e)}")
        return False
    
