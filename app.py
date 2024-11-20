import os
import requests
import openai
import uuid
import tempfile
import json

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
from datetime import datetime, timezone
from functools import wraps
from msal import ConfidentialClientApplication
from flask_session import Session

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.search.documents import SearchClient, IndexDocumentsBatch
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError

# Initialize Flask app
app = Flask(__name__)

# Flask Session Configuration
app.config['SECRET_KEY'] = os.urandom(32) 
app.config['SESSION_TYPE'] = 'filesystem'  # Use filesystem session storage
app.config['VERSION'] = '0.83b'
Session(app)

# Allowed extensions and max file size
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'xlsx', 'pptx', 'html', 'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'heif', 'md', 'json'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

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

AZURE_AI_SEARCH_ENDPOINT = os.getenv('AZURE_AI_SEARCH_ENDPOINT')
AZURE_AI_SEARCH_KEY = os.getenv('AZURE_AI_SEARCH_KEY')
AZURE_AI_SEARCH_USER_INDEX = os.getenv('AZURE_AI_SEARCH_USER_INDEX')

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

# ------------------- Helper Functions -------------------

def get_settings():
    try:
        settings_item = settings_container.read_item(
            item="app_settings",
            partition_key="app_settings"
        )
        print("Successfully retrieved settings.")
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
            'logo_path': 'images/default_logo.png',
            'show_logo': False 
        }
        settings_container.create_item(body=default_settings)
        print("Default settings created and returned.")
        return default_settings
    except Exception as e:
        app.logger.error(f"Error retrieving settings: {str(e)}", exc_info=True)
        print(f"Error retrieving settings: {str(e)}")
        return None



def update_settings(new_settings):
    try:
        settings_item = get_settings()
        settings_item.update(new_settings)
        settings_container.upsert_item(settings_item)
        # Update app.config with new MAX_CONTENT_LENGTH
        app.config['MAX_CONTENT_LENGTH'] = new_settings['max_file_size_mb'] * 1024 * 1024
        print("Settings updated successfully.")
        return True
    except Exception as e:
        app.logger.error(f"Error updating settings: {str(e)}", exc_info=True)
        print(f"Error updating settings: {str(e)}")
        return False


@app.context_processor
def inject_settings():
    settings = get_settings()
    return dict(app_settings=settings)


def allowed_file(filename, allowed_extensions=None):
    if not allowed_extensions:
        allowed_extensions = ALLOWED_EXTENSIONS
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def extract_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_markdown_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_content_with_azure_di(file_path):
    try:
        with open(file_path, "rb") as f:
            poller = document_intelligence_client.begin_analyze_document(
                model_id="prebuilt-read",
                document=f
            )
        result = poller.result()

        extracted_text = ""

        if result.content:
            extracted_text = result.content
        else:
            # Fallback if content is not directly available
            for page in result.pages:
                for line in page.lines:
                    extracted_text += line.content + "\n"
                extracted_text += "\n"

        print(f"Content extracted successfully from {file_path}.")
        return extracted_text

    except Exception as e:
        # Log the error with stack trace
        app.logger.error(f"Error extracting content with Azure DI: {str(e)}", exc_info=True)
        print(f"Error extracting content with Azure DI: {str(e)}")
        # Raise the exception to be handled by the calling function
        raise

def add_system_message_to_conversation(conversation_id, user_id, content):
    try:
        # Retrieve the conversation document
        conversation_item = container.read_item(
            item=conversation_id,
            partition_key=conversation_id
        )

        # Append the system message
        conversation_item['messages'].append({
            "role": "system",
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        conversation_item['last_updated'] = datetime.utcnow().isoformat()

        # Upsert the document
        container.upsert_item(conversation_item)
        print(f"System message added to conversation {conversation_id} successfully.")

    except Exception as e:
        print(f"Error adding system message to conversation: {str(e)}")
        raise e

def chunk_text(text, chunk_size=2000, overlap=200):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    print(f"Text chunked into {len(chunks)} chunks.")
    return chunks

def generate_embedding(text):
    print("Function generate_embedding called")
    print(f"Text input for embedding: {text[:100]}...")  # Print the first 100 characters of the text to avoid excessive output

    try:
        # Make the call to OpenAI for embedding generation
        response = openai.Embedding.create(
            input=text,
            engine=embedding_model
        )
        print("OpenAI API call successful")

        # Extract embedding from the response
        embedding = response['data'][0]['embedding']
        print(f"Embedding generated successfully: Length {len(embedding)}")
        return embedding

    except Exception as e:
        print(f"Error in generating embedding: {str(e)}")
        return None

def process_document_and_store_chunks(extracted_text, file_name, user_id):
    settings = get_settings()
    use_external_apis = settings.get('use_external_apis', False)
    external_chunking_api = settings.get('external_chunking_api', '')
    external_embedding_api = settings.get('external_embedding_api', '')

    if use_external_apis:
        # Call external chunking API
        response = requests.post(f"{external_chunking_api}/chunk", json={'text': extracted_text})
        chunks = response.json().get('chunks', [])
    else:
        # Use local chunking
        chunks = chunk_text(extracted_text)

    print("Function process_document_and_store_chunks called")
    document_id = str(uuid.uuid4())  # Unique ID for the document
    print(f"Generated document ID: {document_id}")
    
    # Chunk the extracted text
    chunks = chunk_text(extracted_text)
    print(f"Total chunks created: {len(chunks)}")

    # Check if there's an existing version of this document
    existing_document_query = """
        SELECT c.version 
        FROM c 
        WHERE c.file_name = @file_name AND c.user_id = @user_id
    """
    parameters = [{"name": "@file_name", "value": file_name}, {"name": "@user_id", "value": user_id}]
    print(f"Querying existing document with parameters: {parameters}")
    
    existing_document = list(documents_container.query_items(query=existing_document_query, parameters=parameters, enable_cross_partition_query=True))
    print(f"Existing document found: {existing_document}")

    # Determine the new version number
    if existing_document:
        version = existing_document[0]['version'] + 1
        print(f"New version determined: {version} (existing document found)")
    else:
        version = 1
        print(f"New version determined: {version} (no existing document)")

    # Get the current time in UTC
    current_time = datetime.now(timezone.utc)

    # Format it to the desired string format
    formatted_time = current_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    # Store document metadata
    document_metadata = {
        "id": document_id,
        "file_name": file_name,
        "user_id": user_id,
        "upload_date": formatted_time,
        "version": version,
        "type": "document_metadata"
    }
    print(f"Document metadata to be upserted: {document_metadata}")
    documents_container.upsert_item(document_metadata)
    print("Document metadata upserted successfully.")

    chunk_documents = []
    
    # Process each chunk
    for idx, chunk_text_content in enumerate(chunks):
        chunk_id = f"{document_id}_{idx}"  # Create a unique chunk ID
        print(f"Processing chunk {idx} with ID: {chunk_id}")

        # Generate embedding
        if use_external_apis:
            # Call external embedding API
            response = requests.post(f"{external_embedding_api}/embed", json={'text': chunk_text_content})
            embedding = response.json().get('embedding')
        else:
            # Generate embedding locally
            embedding = generate_embedding(chunk_text_content)
        print(f"Generated embedding for chunk {idx}")

        # Create chunk document with versioning
        chunk_document = {
            "id": chunk_id,
            "document_id": document_id,
            "chunk_id": str(idx),
            "chunk_text": chunk_text_content,
            "embedding": embedding,
            "file_name": file_name,
            "user_id": user_id,
            "chunk_sequence": idx,
            "upload_date": formatted_time,
            "version": version
        }
        print(f"Chunk document created for chunk {idx}: {chunk_document}")
        chunk_documents.append(chunk_document)

    # Upload the chunk documents to Azure Cognitive Search
    print(f"Uploading {len(chunk_documents)} chunk documents to Azure Cognitive Search")
    search_client_user.upload_documents(documents=chunk_documents)
    print("Chunks uploaded successfully")

def get_user_documents(user_id):
    try:
        # Query to get the latest version of each document for the user
        query = """
            SELECT c.file_name, c.id, c.upload_date, c.user_id, c.version
            FROM c
            WHERE c.user_id = @user_id
        """
        parameters = [{"name": "@user_id", "value": user_id}]
        
        documents = list(documents_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        print(f"Retrieved {len(documents)} documents for user {user_id}.")

        # Dictionary to keep track of the latest version for each file
        latest_documents = {}

        for doc in documents:
            file_name = doc['file_name']
            # If this file_name is not in the dict or if this version is greater, update
            if file_name not in latest_documents or doc['version'] > latest_documents[file_name]['version']:
                latest_documents[file_name] = doc
                
        # Convert the dict to a list for the response
        print("Successfully processed user documents.")
        return jsonify({"documents": list(latest_documents.values())}), 200
    except Exception as e:
        print(f"Error retrieving documents: {str(e)}")
        return jsonify({'error': f'Error retrieving documents: {str(e)}'}), 500

def get_user_document(user_id, document_id):
    print(f"Function get_user_document called for user_id: {user_id}, document_id: {document_id}")

    try:
        # Query to retrieve the latest version of the document
        latest_version_query = """
            SELECT TOP 1 *
            FROM c 
            WHERE c.id = @document_id AND c.user_id = @user_id
            ORDER BY c.version DESC
        """
        parameters = [
            {"name": "@document_id", "value": document_id},
            {"name": "@user_id", "value": user_id}
        ]
        print(f"Query parameters: {parameters}")

        # Execute the query to fetch the document
        document_results = list(documents_container.query_items(
            query=latest_version_query, 
            parameters=parameters, 
            enable_cross_partition_query=True
        ))

        print(f"Query executed, document_results: {document_results}")

        if not document_results:
            print("Document not found or access denied")
            return jsonify({'error': 'Document not found or access denied'}), 404

        print(f"Returning latest version of document: {document_results[0]}")
        return jsonify(document_results[0]), 200  # Return the latest version of the document

    except Exception as e:
        print(f"Error retrieving document: {str(e)}")
        return jsonify({'error': f'Error retrieving document: {str(e)}'}), 500

def get_latest_version(document_id, user_id):
    print(f"Function get_latest_version called for document_id: {document_id}, user_id: {user_id}")

    # Query to retrieve all versions of the document
    query = """
        SELECT c.version
        FROM c 
        WHERE c.id = @document_id AND c.user_id = @user_id
    """
    parameters = [
        {"name": "@document_id", "value": document_id},
        {"name": "@user_id", "value": user_id}
    ]
    print(f"Query parameters: {parameters}")

    try:
        # Execute the query
        results = list(documents_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        print(f"Query results: {results}")

        # Determine the maximum version from the retrieved results
        if results:
            max_version = max(item['version'] for item in results)
            print(f"Latest version found: {max_version}")
            return max_version
        else:
            print("No version found for the document.")
            return None

    except Exception as e:
        print(f"Error retrieving latest version: {str(e)}")
        return None

def get_user_document_version(user_id, document_id, version):
    try:
        # Query to retrieve the specific version of the document
        query = """
            SELECT *
            FROM c 
            WHERE c.id = @document_id AND c.user_id = @user_id AND c.version = @version
        """
        parameters = [
            {"name": "@document_id", "value": document_id},
            {"name": "@user_id", "value": user_id},
            {"name": "@version", "value": version}
        ]
        
        document_results = list(documents_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        if not document_results:
            print("Document version not found.")
            return jsonify({'error': 'Document version not found'}), 404

        print(f"Returning document version: {version}")
        return jsonify(document_results[0]), 200  # Return the specific version of the document

    except Exception as e:
        print(f"Error retrieving document version: {str(e)}")
        return jsonify({'error': f'Error retrieving document version: {str(e)}'}), 500

def delete_user_document(user_id, document_id):
    """Delete a document from the user's documents in Cosmos DB."""
    try:
        # Attempt to read the document to ensure it exists and belongs to the user
        document_item = documents_container.read_item(
            item=document_id,
            partition_key=document_id  # Use document_id as the partition key
        )

        # Verify that the document belongs to the user
        if document_item.get('user_id') != user_id:
            raise Exception("Unauthorized access to document")

        # Delete the document
        documents_container.delete_item(
            item=document_id,
            partition_key=document_id  # Use document_id as the partition key
        )
        print(f"Document {document_id} deleted successfully.")
    except CosmosResourceNotFoundError:
        # Document not found
        print("Document not found.")
        raise Exception("Document not found")
    except Exception as e:
        app.logger.error(f"Error deleting document: {str(e)}", exc_info=True)
        print(f"Error deleting document: {str(e)}")
        raise

def delete_user_document_chunks(document_id):
    """Delete document chunks from Azure Cognitive Search index."""
    try:
        # Retrieve documents to delete based on document_id
        results = search_client_user.search(
            search_text="*",
            filter=f"document_id eq '{document_id}'",
            select=["id"]
        )

        ids_to_delete = [doc['id'] for doc in results]

        if not ids_to_delete:
            app.logger.info(f"No chunks found for document_id: {document_id}")
            print(f"No chunks found for document_id: {document_id}")
            return

        # Prepare documents to delete
        documents_to_delete = [{"id": doc_id} for doc_id in ids_to_delete]

        # Create an IndexDocumentsBatch object
        batch = IndexDocumentsBatch()

        # Add delete actions to the batch
        batch.add_delete_actions(documents_to_delete)

        # Execute the batch delete operation
        result = search_client_user.index_documents(batch)
        print(f"Document chunks for {document_id} deleted successfully.")
    except Exception as e:
        app.logger.error(f"Error deleting document chunks: {str(e)}", exc_info=True)
        print(f"Error deleting document chunks: {str(e)}")
        raise

def delete_user_document_version(user_id, document_id, version):
    # Query to find the specific version of the document
    query = """
        SELECT c.id 
        FROM c 
        WHERE c.id = @document_id AND c.user_id = @user_id AND c.version = @version
    """
    parameters = [
        {"name": "@document_id", "value": document_id},
        {"name": "@user_id", "value": user_id},
        {"name": "@version", "value": version}
    ]
    documents = list(documents_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

    # Delete the specific document version
    for doc in documents:
        documents_container.delete_item(doc['id'], partition_key=doc['user_id'])
        print(f"Deleted document version {version} for document_id {document_id}.")

def delete_user_document_version_chunks(document_id, version):
    # Use Azure AI Search to delete chunks for the specific document version
    search_client_user.delete_documents(
        actions=[
            {"@search.action": "delete", "id": chunk['id']} for chunk in 
            search_client_user.search(
                search_text="*",
                filter=f"document_id eq '{document_id}' and version eq {version}",
                select="id"  # Only select the ID for deletion
            )
        ]
    )
    print(f"Deleted chunks for document_id {document_id}, version {version}.")

def hybrid_search(query, user_id, top_n=3):
    try:
        # Generate the query embedding
        query_embedding = generate_embedding(query)

        if query_embedding is None:
            print("Failed to generate query embedding.")
            return None

        # Create a vectorized query
        vector_query = VectorizedQuery(vector=query_embedding, k_nearest_neighbors=top_n, fields="embedding")

        # Perform the hybrid search
        results = search_client_user.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=f"user_id eq '{user_id}'",
            select=["id", "chunk_text", "chunk_id", "file_name", "user_id", "version", "chunk_sequence", "upload_date"]
        )

        # Step 4: Collect top_n results
        limited_results = []
        for i, result in enumerate(results):
            if i >= top_n:
                break
            limited_results.append(result)

        # Extract documents from results
        documents = [doc for doc in limited_results]
        print(f"Hybrid search completed successfully with {len(documents)} results.")
        return documents

    except Exception as e:
        print(f"Error during hybrid search: {str(e)}")
        return None

def get_document_versions(user_id, document_id):
    try:
        # Query to retrieve all versions of the document for the user
        query = """
            SELECT c.id, c.file_name, c.version, c.upload_date
            FROM c 
            WHERE c.id = @document_id AND c.user_id = @user_id
            ORDER BY c.version DESC
        """
        parameters = [
            {"name": "@document_id", "value": document_id},
            {"name": "@user_id", "value": user_id}
        ]

        versions_results = list(documents_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        if not versions_results:
            print("No versions found for the document.")
            return []
        print(f"Retrieved {len(versions_results)} versions for document {document_id}.")
        return versions_results

    except Exception as e:
        print(f'Error retrieving document versions: {str(e)}')
        return []

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            print("User not logged in. Redirecting to login page.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_id():
    """Helper function to get the current user's unique ID."""
    user = session.get('user')
    if user:
        return user.get('oid')  # Object ID provided by Azure AD
    return None

# ------------------- Custom Filters -------------------

@app.template_filter('to_datetime')
def to_datetime_filter(value):
    return datetime.fromisoformat(value)

@app.template_filter('format_datetime')
def format_datetime_filter(value):
    return value.strftime('%Y-%m-%d %H:%M')

# ------------------- User Authentication Routes -------------------

@app.route('/login')
def login():
    """Initiate the Azure AD login process."""
    msal_app = ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
    )
    # Generate the authorization URL
    auth_url = msal_app.get_authorization_request_url(
        scopes=SCOPE,
        redirect_uri=url_for('authorized', _external=True, _scheme='https')
    )
    print("Redirecting to Azure AD for authentication.")
    return redirect(auth_url)

@app.route('/getAToken')  # This path should match REDIRECT_PATH
def authorized():
    """Handle the redirect from Azure AD and acquire tokens."""
    msal_app = ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
    )
    # Get the authorization code from the query parameters
    code = request.args.get('code')
    if not code:
        print("Authorization code not found.")
        return "Authorization code not found", 400
    result = msal_app.acquire_token_by_authorization_code(
        code=code,
        scopes=SCOPE,
        redirect_uri=url_for('authorized', _external=True, _scheme='https')
    )
    if "error" in result:
        error_description = result.get("error_description", result.get("error"))
        print(f"Login failure: {error_description}")
        return f"Login failure: {error_description}", 500
    # Store the user information in the session
    session["user"] = result.get("id_token_claims")
    session["access_token"] = result.get("access_token")
    print("User logged in successfully.")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """Log the user out and clear the session."""
    session.clear()
    # Optionally, redirect the user to Azure AD logout endpoint
    logout_url = f"{AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri={url_for('index', _external=True)}"
    print("User logged out. Redirecting to Azure AD logout endpoint.")
    return redirect(logout_url)

@app.route('/profile')
@login_required
def profile():
    """Display the user's profile information."""
    user = session.get('user')
    return render_template('profile.html', user=user)

# ------------------- Routes -------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    settings = get_settings()
    if request.method == 'POST':
        # Process form data
        app_title = request.form.get('app_title', 'AI Chat Application')
        max_file_size_mb = int(request.form.get('max_file_size_mb', 16))
        conversation_history_limit = int(request.form.get('conversation_history_limit', 10))
        default_system_prompt = request.form.get('default_system_prompt', '')
        llm_model = request.form.get('llm_model', 'gpt-3.5-turbo')
        use_external_apis = request.form.get('use_external_apis') == 'on'
        external_chunking_api = request.form.get('external_chunking_api', '')
        external_embedding_api = request.form.get('external_embedding_api', '')
        show_logo = request.form.get('show_logo') == 'on'  # Get the show_logo setting

        # Handle logo upload
        logo_file = request.files.get('logo_file')
        if logo_file and allowed_file(logo_file.filename, allowed_extensions={'png', 'jpg', 'jpeg'}):
            filename = secure_filename(logo_file.filename)
            # Save the uploaded logo file as 'custom_logo.png'
            logo_path = os.path.join(app.root_path, 'static', 'images', 'custom_logo.png')
            os.makedirs(os.path.dirname(logo_path), exist_ok=True)
            logo_file.save(logo_path)
            # Update the settings to use the custom logo
            logo_path_relative = 'images/custom_logo.png'
        else:
            # Use the default logo if no custom logo is uploaded
            logo_path_relative = 'images/default_logo.png'

        # Update settings
        new_settings = {
            'app_title': app_title,
            'max_file_size_mb': max_file_size_mb,
            'conversation_history_limit': conversation_history_limit,
            'default_system_prompt': default_system_prompt,
            'llm_model': llm_model,
            'use_external_apis': use_external_apis,
            'external_chunking_api': external_chunking_api,
            'external_embedding_api': external_embedding_api,
            'logo_path': logo_path_relative,
            'show_logo': show_logo  # Include the new setting
        }
        update_settings(new_settings)
        settings.update(new_settings)

        app.config['MAX_CONTENT_LENGTH'] = new_settings['max_file_size_mb'] * 1024 * 1024
        print("Admin settings updated successfully.")

        return redirect(url_for('admin_settings'))

    return render_template('admin_settings.html', settings=settings)



@app.route('/chat', methods=['GET'])
@login_required
def chat():
    conversation_id = request.args.get('conversation_id')
    messages = []
    user_id = get_current_user_id()
    if not user_id:
        print("User not authenticated.")
        return redirect(url_for('login'))

    if conversation_id:
        try:
            conversation_item = container.read_item(
                item=conversation_id,
                partition_key=conversation_id
            )
            messages = conversation_item['messages']
            print(f"Loaded conversation {conversation_id} successfully.")
        except Exception:
            conversation_id = None  # If conversation not found, start a new one
            print(f"Conversation {conversation_id} not found.")

    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        conversation_item = {
            'id': conversation_id,
            'user_id': user_id,
            'messages': [],
            'last_updated': datetime.utcnow().isoformat()
        }
        container.upsert_item(conversation_item)
        print(f"Started new conversation {conversation_id}.")

    return render_template('chat.html', conversation_id=conversation_id, messages=messages)

@app.route('/api/get_messages', methods=['GET'])
@login_required
def api_get_messages():
    conversation_id = request.args.get('conversation_id')
    user_id = get_current_user_id()
    if not user_id:
        print("User not authenticated.")
        return jsonify({'error': 'User not authenticated'}), 401
    if not conversation_id:
        print("No conversation_id provided.")
        return jsonify({'error': 'No conversation_id provided'}), 400
    try:
        conversation_item = container.read_item(
            item=conversation_id,
            partition_key=conversation_id
        )
        messages = conversation_item.get('messages', [])
        print(f"Retrieved messages for conversation {conversation_id}.")
        return jsonify({'messages': messages})
    except CosmosResourceNotFoundError:
        # Conversation does not exist yet; return empty messages
        print(f"Conversation {conversation_id} not found.")
        return jsonify({'messages': []})
    except Exception:
        print(f"Error retrieving conversation {conversation_id}.")
        return jsonify({'error': 'Conversation not found'}), 404

@app.route('/api/chat', methods=['POST'])
@login_required
def chat_api():
    settings = get_settings()
    data = request.get_json()
    user_id = get_current_user_id()
    if not user_id:
        print("User not authenticated.")
        return jsonify({'error': 'User not authenticated'}), 401

    user_message = data['message']
    conversation_id = data.get('conversation_id')
    hybrid_search_enabled = data.get('hybrid_search', True)  # Default to True if not provided

    # Convert hybrid_search_enabled to boolean if necessary
    if isinstance(hybrid_search_enabled, str):
        hybrid_search_enabled = hybrid_search_enabled.lower() == 'true'

    # Retrieve or create the conversation
    if not conversation_id:
        # Generate a new conversation ID
        conversation_id = str(uuid.uuid4())
        conversation_item = {
            'id': conversation_id,
            'user_id': user_id,
            'messages': [],
            'last_updated': datetime.utcnow().isoformat()
        }
        print(f"Started new conversation {conversation_id}.")
    else:
        # Retrieve existing conversation
        try:
            conversation_item = container.read_item(
                item=conversation_id,
                partition_key=conversation_id
            )
            print(f"Retrieved conversation {conversation_id}.")
        except CosmosResourceNotFoundError:
            # Start a new conversation if not found
            conversation_id = str(uuid.uuid4())
            conversation_item = {
                'id': conversation_id,
                'user_id': user_id,
                'messages': [],
                'last_updated': datetime.utcnow().isoformat()
            }
            print(f"Conversation {conversation_id} not found. Started new conversation.")
        except Exception as e:
            print(f"Error retrieving conversation {conversation_id}: {str(e)}", exc_info=True)
            return jsonify({'error': 'An error occurred'}), 500

    # Append the new user message
    conversation_item['messages'].append({'role': 'user', 'content': user_message})

    # Update the conversation title if it's the first user message
    if conversation_item.get('title') == 'New Conversation':
        new_title = user_message.strip()
        if len(new_title) > 30:
            new_title = new_title[:27] + '...'
        conversation_item['title'] = new_title

    if len(conversation_item['messages']) == 1 and settings.get('default_system_prompt'):
        conversation_item['messages'].insert(0, {'role': 'system', 'content': settings.get('default_system_prompt')})

    # If hybrid search is enabled, perform it and include the results
    if hybrid_search_enabled:
        search_results = hybrid_search(user_message, user_id, top_n=3)
        if search_results:
            # Construct a system prompt with retrieved chunks and citations
            retrieved_texts = []
            for doc in search_results:
                chunk_text = doc['chunk_text']
                file_name = doc['file_name']
                version = doc['version']
                chunk_sequence = doc['chunk_sequence']
                page_number = doc.get('page_number') or chunk_sequence  # Use page number if available
                citation_id = doc['id']  # Use the chunk's unique ID

                # Create a readable citation string with embedded citation ID
                citation = f"(Source: {file_name}, Page: {page_number}) [#{citation_id}]"

                # Append the chunk text with the citation
                retrieved_texts.append(f"{chunk_text}\n{citation}")
            # Combine all retrieved texts
            retrieved_content = "\n\n".join(retrieved_texts)
            # Create the system prompt with examples
            system_prompt = (
                "You are an AI assistant provided with the following document excerpts and their sources.\n"
                "When you answer the user's question, please cite the sources by including the citations provided after each excerpt.\n"
                "Use the format (Source: filename, Page: page number) [#ID] for citations, where ID is the unique identifier provided.\n"
                "Ensure your response is informative and includes citations using this format.\n\n"
                "For example:\n"
                "User: What is the policy on double dipping?\n"
                "Assistant: The policy prohibits entities from using federal funds received through one program to apply for additional funds through another program, commonly known as 'double dipping' (Source: PolicyDocument.pdf, Page: 12) [#123abc].\n\n"
                f"{retrieved_content}"
            )
            # Add system prompt to conversation
            conversation_item['messages'].append({'role': 'system', 'content': system_prompt})
            print("System prompt with hybrid search results added to conversation.")

            container.upsert_item(body=conversation_item)

    # Limit the conversation history
    conversation_history_limit = settings.get('conversation_history_limit', 10)
    conversation_history = conversation_item['messages'][-conversation_history_limit:]

    # Prepare conversation history for API
    allowed_roles = ['system', 'assistant', 'user', 'function', 'tool']
    conversation_history_for_api = []
    for msg in conversation_history:
        if msg['role'] in allowed_roles:
            conversation_history_for_api.append(msg)
        elif msg['role'] == 'file':
            # Modify 'file' messages to be 'system' messages
            file_content = msg.get('file_content', '')
            filename = msg.get('filename', 'uploaded_file')
            # Optionally limit the length of file content to avoid exceeding token limits
            max_file_content_length = 50000  # Adjust as needed based on token limits
            if len(file_content) > max_file_content_length:
                file_content = file_content[:max_file_content_length] + '...'

            # Create a system message with the file content
            system_message = {
                'role': 'system',
                'content': f"The user has uploaded a file named '{filename}' with the following content:\n\n{file_content}\n\nPlease use this information to assist the user."
            }
            conversation_history_for_api.append(system_message)
        else:
            # Ignore messages with other roles
            continue

    # Generate AI response
    response = openai.ChatCompletion.create(
        engine=settings.get('llm_model', 'gpt-4o'),
        messages=conversation_history_for_api
    )

    ai_message = response['choices'][0]['message']['content']
    conversation_item['messages'].append({'role': 'assistant', 'content': ai_message})
    conversation_item['last_updated'] = datetime.utcnow().isoformat()

    # Upsert the conversation item in Cosmos DB
    container.upsert_item(body=conversation_item)
    print("AI response generated and conversation updated.")

    return jsonify({
        'reply': ai_message,
        'conversation_id': conversation_id,
        'conversation_title': conversation_item['title']
    })

@app.route('/chats', methods=['GET'])
@login_required
def chats():
    """Route to display the new chats.html page."""
    user_id = get_current_user_id()
    if not user_id:
        print("User not authenticated.")
        return redirect(url_for('login'))
    return render_template('chats.html')

@app.route('/api/get_conversations', methods=['GET'])
@login_required
def get_conversations():
    user_id = get_current_user_id()
    if not user_id:
        print("User not authenticated.")
        return jsonify({'error': 'User not authenticated'}), 401
    query = f"SELECT c.id, c.title, c.last_updated FROM c WHERE c.user_id = '{user_id}' ORDER BY c.last_updated DESC"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    print(f"Retrieved {len(items)} conversations for user {user_id}.")
    return jsonify({'conversations': items})


@app.route('/api/create_conversation', methods=['POST'])
@login_required
def create_conversation():
    user_id = get_current_user_id()
    if not user_id:
        print("User not authenticated.")
        return jsonify({'error': 'User not authenticated'}), 401

    conversation_id = str(uuid.uuid4())
    conversation_item = {
        'id': conversation_id,
        'user_id': user_id,
        'messages': [],
        'last_updated': datetime.utcnow().isoformat(),
        'title': 'New Conversation'  # Add this line
    }
    container.upsert_item(conversation_item)
    print(f"Created new conversation {conversation_id} for user {user_id}.")

    return jsonify({'conversation_id': conversation_id}), 200

@app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
@login_required
def delete_conversation(conversation_id):
    user_id = get_current_user_id()
    if not user_id:
        print("User not authenticated.")
        return jsonify({'error': 'User not authenticated'}), 401
    try:
        # Attempt to read the conversation to ensure it exists and belongs to the user
        conversation_item = container.read_item(
            item=conversation_id,
            partition_key=conversation_id
        )
        # Delete the conversation
        container.delete_item(
            item=conversation_id,
            partition_key=user_id
        )
        print(f"Conversation {conversation_id} deleted successfully.")
        return jsonify({'message': 'Conversation deleted successfully'}), 200
    except CosmosResourceNotFoundError:
        print(f"Conversation {conversation_id} not found.")
        return jsonify({'error': 'Conversation not found'}), 404
    except Exception as e:
        app.logger.error(f"Error deleting conversation: {str(e)}", exc_info=True)
        print(f"Error deleting conversation: {str(e)}")
        return jsonify({'error': 'An error occurred while deleting the conversation'}), 500

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    settings = get_settings()
    user_id = get_current_user_id()
    if not user_id:
        print("User not authenticated.")
        return jsonify({'error': 'User not authenticated'}), 401

    if 'file' not in request.files:
        print("No file uploaded.")
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    conversation_id = request.form.get('conversation_id')

    if not file.filename:
        print("No selected file.")
        return jsonify({'error': 'No selected file'}), 400

    # Retrieve or create the conversation
    if not conversation_id or conversation_id.strip() == '':
        # Start a new conversation if no conversation_id is provided
        conversation_id = str(uuid.uuid4())
        conversation_item = {
            'id': conversation_id,
            'user_id': user_id,
            'messages': [],
            'last_updated': datetime.utcnow().isoformat()
        }
        print(f"Started new conversation {conversation_id}.")
    else:
        # Retrieve existing conversation
        try:
            conversation_item = container.read_item(
                item=conversation_id,
                partition_key=conversation_id
            )
            print(f"Retrieved conversation {conversation_id}.")
        except Exception:
            # Start a new conversation if not found
            conversation_id = str(uuid.uuid4())
            conversation_item = {
                'id': conversation_id,
                'user_id': user_id,
                'messages': [],
                'last_updated': datetime.utcnow().isoformat()
            }
            print(f"Conversation {conversation_id} not found. Started new conversation.")

    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    max_file_size_bytes = settings.get('max_file_size_mb', 16) * 1024 * 1024
    if file_length > max_file_size_bytes:
        print("File size exceeds maximum allowed size.")
        return jsonify({'error': 'File size exceeds maximum allowed size'}), 400
    file.seek(0)

    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1].lower()

    # Save the uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        file.save(tmp_file.name)
        temp_file_path = tmp_file.name
        print(f"File {filename} saved temporarily at {temp_file_path}.")

    extracted_text = ''
    try:
        if file_ext in ['.pdf', '.docx', '.xlsx', '.pptx', '.html', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.heif']:
            extracted_text = extract_content_with_azure_di(temp_file_path)
        elif file_ext == '.txt':
            extracted_text = extract_text_file(temp_file_path)
        elif file_ext == '.md':
            extracted_text = extract_markdown_file(temp_file_path)
        elif file_ext == '.json':
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                parsed_json = json.load(f)
                extracted_text = json.dumps(parsed_json, indent=2)
        else:
            print("Unsupported file type.")
            return jsonify({'error': 'Unsupported file type'}), 400

    except Exception as e:
        # Log the error
        app.logger.error(f"Error processing file: {str(e)}", exc_info=True)
        print(f"Error processing file: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    finally:
        os.remove(temp_file_path)
        print(f"Temporary file {temp_file_path} deleted.")

    # Add a message to the conversation indicating the file upload
    try:
        file_message = {
            'role': 'file',
            'filename': filename,
            'file_id': str(uuid.uuid4()),  # Unique ID for the file content
            'timestamp': datetime.utcnow().isoformat(),
            # Store the extracted text (file content)
            'file_content': extracted_text
        }

        conversation_item['messages'].append(file_message)
        conversation_item['last_updated'] = datetime.utcnow().isoformat()

        # Upsert the conversation item in Cosmos DB
        container.upsert_item(conversation_item)
        print(f"File {filename} added to conversation {conversation_id} successfully.")

    except Exception as e:
        print(f"Error adding file to conversation: {str(e)}")
        return jsonify({'error': f'Error adding file to conversation: {str(e)}'}), 500

    response_data = {
        'message': 'File added to the conversation successfully',
        'conversation_id': conversation_id
    }

    return jsonify(response_data), 200

@app.route('/api/get_file_content', methods=['POST'])
@login_required
def get_file_content():
    data = request.get_json()
    user_id = get_current_user_id()
    conversation_id = data.get('conversation_id')
    file_id = data.get('file_id')

    if not user_id:
        print("User not authenticated.")
        return jsonify({'error': 'User not authenticated'}), 401

    if not conversation_id or not file_id:
        print("Missing conversation_id or file_id.")
        return jsonify({'error': 'Missing conversation_id or file_id'}), 400

    try:
        conversation_item = container.read_item(
            item=conversation_id,
            partition_key=conversation_id
        )
        messages = conversation_item.get('messages', [])
        # Find the message with the given file_id
        for message in messages:
            if message.get('role') == 'file' and message.get('file_id') == file_id:
                file_content = message.get('file_content')
                filename = message.get('filename')
                if file_content:
                    print(f"File content retrieved for file_id {file_id}.")
                    return jsonify({'file_content': file_content, 'filename': filename}), 200
                else:
                    print("File content not found.")
                    return jsonify({'error': 'File content not found'}), 404
        print("File not found in conversation.")
        return jsonify({'error': 'File not found in conversation'}), 404

    except Exception as e:
        app.logger.error(f"Error retrieving file content: {str(e)}", exc_info=True)
        print(f"Error retrieving file content: {str(e)}")
        return jsonify({'error': 'Error retrieving file content'}), 500

@app.route('/conversations')
@login_required
def conversations():
    user_id = get_current_user_id()
    if not user_id:
        print("User not authenticated.")
        return redirect(url_for('login'))
    query = f"SELECT c.id, c.last_updated FROM c WHERE c.user_id = '{user_id}' ORDER BY c.last_updated DESC"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    print(f"Retrieved {len(items)} conversations for user {user_id}.")
    return render_template('conversations.html', conversations=items)

@app.route('/conversation/<conversation_id>')
@login_required
def view_conversation(conversation_id):
    user_id = get_current_user_id()
    if not user_id:
        print("User not authenticated.")
        return redirect(url_for('login'))
    try:
        conversation_item = container.read_item(
            item=conversation_id,
            partition_key=conversation_id
        )
        messages = conversation_item['messages']
        print(f"Viewing conversation {conversation_id}.")
        return render_template('chat.html', conversation_id=conversation_id, messages=messages)
    except Exception:
        print(f"Conversation {conversation_id} not found.")
        return "Conversation not found", 404

@app.route('/conversation/<conversation_id>/messages', methods=['GET'])
@login_required
def get_conversation_messages(conversation_id):
    user_id = get_current_user_id()
    if not user_id:
        print("User not authenticated.")
        return jsonify({'error': 'User not authenticated'}), 401
    try:
        conversation_item = container.read_item(
            item=conversation_id,
            partition_key=conversation_id
        )
        messages = conversation_item.get('messages', [])
        # Remove 'file_content' from messages before sending
        for message in messages:
            if message.get('role') == 'file' and 'file_content' in message:
                del message['file_content']
        print(f"Retrieved messages for conversation {conversation_id}.")
        return jsonify({'messages': messages})
    except CosmosResourceNotFoundError:
        # Conversation does not exist yet; return empty messages
        print(f"Conversation {conversation_id} not found.")
        return jsonify({'messages': []})
    except Exception:
        print(f"Error retrieving conversation {conversation_id}.")
        return jsonify({'error': 'Conversation not found'}), 404

# ------------------- Document Processing Routes -------------------

@app.route('/documents', methods=['GET'])
@login_required
def documents():
    user_id = get_current_user_id()
    if not user_id:
        print("User not authenticated.")
        return redirect(url_for('login'))
    return render_template('documents.html')

@app.route('/api/documents/upload', methods=['POST'])
@login_required
def upload_document():
    settings = get_settings()
    user_id = get_current_user_id()
    if not user_id:
        print("User not authenticated.")
        return jsonify({'error': 'User not authenticated'}), 401

    if 'file' not in request.files:
        print("No file uploaded.")
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if not file.filename:
        print("No selected file.")
        return jsonify({'error': 'No selected file'}), 400

    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    max_file_size_bytes = settings.get('max_file_size_mb', 16) * 1024 * 1024
    if file_length > max_file_size_bytes:
        print("File size exceeds maximum allowed size.")
        return jsonify({'error': 'File size exceeds maximum allowed size'}), 400
    file.seek(0)
    
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1].lower()

    # Save the uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        file.save(tmp_file.name)
        temp_file_path = tmp_file.name
        print(f"File {filename} saved temporarily at {temp_file_path}.")

    extracted_text = ''
    try:
        if file_ext in ['.pdf', '.docx', '.xlsx', '.pptx', '.html', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.heif']:
            extracted_text = extract_content_with_azure_di(temp_file_path)
        elif file_ext == '.txt':
            extracted_text = extract_text_file(temp_file_path)
        elif file_ext == '.md':
            extracted_text = extract_markdown_file(temp_file_path)
        elif file_ext == '.json':
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                extracted_text = json.dumps(json.load(f))
        else:
            print("Unsupported file type.")
            return jsonify({'error': 'Unsupported file type'}), 400

    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    finally:
        os.remove(temp_file_path)
        print(f"Temporary file {temp_file_path} deleted.")

    # Process document and store chunks
    try:
        process_document_and_store_chunks(extracted_text, filename, user_id)
        print(f"Document {filename} processed and chunks stored successfully.")
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        return jsonify({'error': f'Error processing document: {str(e)}'}), 500

    return jsonify({'message': 'Document uploaded and processed successfully'}), 200

@app.route('/api/documents', methods=['GET'])
@login_required
def api_get_user_documents():
    user_id = get_current_user_id()
    if not user_id:
        print("User not authenticated.")
        return jsonify({'error': 'User not authenticated'}), 401
    return get_user_documents(user_id)

@app.route('/api/documents/<document_id>', methods=['GET'])
@login_required
def api_get_user_document(document_id):
    user_id = get_current_user_id()
    if not user_id:
        print("User not authenticated.")
        return jsonify({'error': 'User not authenticated'}), 401
    return get_user_document(user_id, document_id)

@app.route('/api/documents/<document_id>', methods=['DELETE'])
@login_required
def api_delete_user_document(document_id):
    user_id = get_current_user_id()
    if not user_id:
        print("User not authenticated.")
        return jsonify({'error': 'User not authenticated'}), 401
    try:
        delete_user_document(user_id, document_id)
        delete_user_document_chunks(document_id)
        print(f"Document {document_id} and its chunks deleted successfully.")
        return jsonify({'message': 'Document deleted successfully'}), 200
    except Exception as e:
        print(f"Error deleting document: {str(e)}")
        return jsonify({'error': f'Error deleting document: {str(e)}'}), 500

from azure.core.exceptions import AzureError

@app.route('/api/get_citation', methods=['POST'])
@login_required
def get_citation():
    data = request.get_json()
    user_id = get_current_user_id()
    citation_id = data.get('citation_id')

    if not user_id:
        print("User not authenticated.")
        return jsonify({'error': 'User not authenticated'}), 401

    if not citation_id:
        print("Missing citation_id.")
        return jsonify({'error': 'Missing citation_id'}), 400

    try:
        # Retrieve the chunk from Azure Cognitive Search by its key (id)
        result = search_client_user.get_document(key=citation_id)

        if not result:
            print("Citation not found.")
            return jsonify({'error': 'Citation not found'}), 404

        chunk = result
        # Verify that the chunk belongs to the user
        if chunk.get('user_id') != user_id:
            print("Unauthorized access to citation.")
            return jsonify({'error': 'Unauthorized access to citation'}), 403

        cited_text = chunk.get('chunk_text')
        file_name = chunk.get('file_name')
        page_number = chunk.get('chunk_sequence')  # Assuming chunk_sequence corresponds to page number

        if not cited_text:
            print("Cited text not found.")
            return jsonify({'error': 'Cited text not found'}), 404

        print(f"Citation {citation_id} retrieved successfully.")
        return jsonify({
            'cited_text': cited_text,
            'file_name': file_name,
            'page_number': page_number
        }), 200

    except AzureError as e:
        app.logger.error(f"Error retrieving citation from Azure Cognitive Search: {str(e)}", exc_info=True)
        print(f"Error retrieving citation from Azure Cognitive Search: {str(e)}")
        return jsonify({'error': 'Error retrieving citation'}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    app.run(debug=True)
