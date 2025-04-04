# functions_settings.py

from config import *
from functions_authentication import *

def get_settings():
    try:
        settings_item = settings_container.read_item(
            item="app_settings",
            partition_key="app_settings"
        )
        print("Successfully retrieved settings.")
        return settings_item
    except CosmosResourceNotFoundError:
        default_settings = {
            'id': 'app_settings',

            # General Settings
            'app_title': 'Simple Chat',
            'landing_page_text': 'You can add text here and it supports Markdown. You agree to our [acceptable user policy](acceptable_use_policy.html) by using this service.',
            'show_logo': False,
            'logo_path': 'images/logo.svg',

            # GPT Settings
            'enable_gpt_apim': False,
            'azure_openai_gpt_endpoint': '',
            'azure_openai_gpt_api_version': '2024-05-01-preview',
            'azure_openai_gpt_authentication_type': 'key',
            'azure_openai_gpt_subscription_id': '',
            'azure_openai_gpt_resource_group': '',
            'azure_openai_gpt_key': '',
            'gpt_model': {
                "selected": [],
                "all": []
            },
            'azure_apim_gpt_endpoint': '',
            'azure_apim_gpt_subscription_key': '',
            'azure_apim_gpt_deployment': '',
            'azure_apim_gpt_api_version': '',

            # Embeddings Settings
            'enable_embedding_apim': False,
            'azure_openai_embedding_endpoint': '',
            'azure_openai_embedding_api_version': '2024-05-01-preview',
            'azure_openai_embedding_authentication_type': 'key',
            'azure_openai_embedding_subscription_id': '',
            'azure_openai_embedding_resource_group': '',
            'azure_openai_embedding_key': '',
            'embedding_model': {
                "selected": [],
                "all": []
            },
            'azure_apim_embedding_endpoint': '',
            'azure_apim_embedding_subscription_key': '',
            'azure_apim_embedding_deployment': '',
            'azure_apim_embedding_api_version': '',

            # Image Generation Settings
            'enable_image_generation': False,
            'enable_image_gen_apim': False,
            'azure_openai_image_gen_endpoint': '',
            'azure_openai_image_gen_api_version': '2024-05-01-preview',
            'azure_openai_image_gen_authentication_type': 'key',
            'azure_openai_image_gen_subscription_id': '',
            'azure_openai_image_gen_resource_group': '',
            'azure_openai_image_gen_key': '',
            'image_gen_model': {
                "selected": [],
                "all": []
            },
            'azure_apim_image_gen_endpoint': '',
            'azure_apim_image_gen_subscription_key': '',
            'azure_apim_image_gen_deployment': '',
            'azure_apim_image_gen_api_version': '',

            # Workspaces
            'enable_user_workspace': True,
            'enable_group_workspaces': True,
            'require_member_of_create_group': False,
            'enable_public_workspaces': False,
            'require_member_of_create_public_workspace': False,

            # Multimedia
            'enable_video_file_support': False,
            'enable_audio_file_support': False,

            # Metadata Extraction
            'enable_extract_meta_data': False,
            'enable_summarize_content_history_for_search': False,
            'number_of_historical_messages_to_summarize': 10,
            'enable_summarize_content_history_beyond_conversation_history_limit': False,
            # title, authors, publication date, keywords, summary
            'enable_document_classification': False,
            'document_classification_categories': [
                {
                    "label": "None",
                    "color": "#808080"
                },
                {
                    "label": "N/A",
                    "color": "#808080"
                },
                {
                    "label": "Pending",
                    "color": "#0000FF"
                }
            ],

            # Enhanced Citations
            'enable_enhanced_citations': False,
            'enable_enhanced_citations_mount': False,
            'enhanced_citations_mount': '/view_documents',
            'office_docs_storage_account_url': '',
            'office_docs_authentication_type': 'key',
            'office_docs_key': '',
            'video_files_storage_account_url': '',
            'video_files_authentication_type': 'key',
            'video_files_key': '',
            'audio_files_storage_account_url': '',
            'audio_files_authentication_type': 'key',
            'audio_files_key': '',

            # Safety (Content Safety) Settings
            'enable_content_safety': False,
            'require_member_of_safety_violation_admin': False,
            'content_safety_endpoint': '',
            'content_safety_key': '',
            'content_safety_authentication_type': 'key',
            'enable_content_safety_apim': False,
            'azure_apim_content_safety_endpoint': '',
            'azure_apim_content_safety_subscription_key': '',

            # User Feedback / Conversation Archiving
            'enable_user_feedback': True,
            'require_member_of_feedback_admin': False,
            'enable_conversation_archiving': False,

            # Search and Extract
            'enable_web_search': False,
            'bing_search_key': '',
            'enable_web_search_apim': False,
            'azure_apim_web_search_endpoint': '',
            'azure_apim_web_search_subscription_key': '',

            'azure_ai_search_endpoint': '',
            'azure_ai_search_key': '',
            'azure_ai_search_authentication_type': 'key',
            'enable_ai_search_apim': False,
            'azure_apim_ai_search_endpoint': '',
            'azure_apim_ai_search_subscription_key': '',

            'azure_document_intelligence_endpoint': '',
            'azure_document_intelligence_key': '',
            'azure_document_intelligence_authentication_type': 'key',
            'enable_document_intelligence_apim': False,
            'azure_apim_document_intelligence_endpoint': '',
            'azure_apim_document_intelligence_subscription_key': '',

            # Other Settings
            'max_file_size_mb': 150,
            'conversation_history_limit': 10,
            'default_system_prompt': '',
            'enable_file_processing_logs': True
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

def encrypt_key(key):
    cipher_suite = Fernet(app.config['SECRET_KEY'])
    encrypted_key = cipher_suite.encrypt(key.encode())
    return encrypted_key.decode()

def decrypt_key(encrypted_key):
    cipher_suite = Fernet(app.config['SECRET_KEY'])
    try:
        encrypted_key_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
        decrypted_key = cipher_suite.decrypt(encrypted_key_bytes).decode()
        return decrypted_key
    except InvalidToken:
        print("Decryption failed: Invalid token")
        return None

def get_user_settings(user_id):
    """Fetches the user settings document from Cosmos DB."""
    try:
        doc = user_settings_container.read_item(item=user_id, partition_key=user_id)
        # Ensure the settings key exists for consistency downstream
        if 'settings' not in doc:
            doc['settings'] = {}
        return doc
    except exceptions.CosmosResourceNotFoundError:
        # Return a default structure if the user has no settings saved yet
        return {"id": user_id, "settings": {}}
    except Exception as e:
        print(f"Error in get_user_settings for {user_id}: {e}")
        raise # Re-raise the exception to be handled by the route
    
def update_user_settings(user_id, settings_to_update):
    """
    Updates or creates user settings in Cosmos DB, merging new settings
    into the existing 'settings' sub-dictionary and updating 'lastUpdated'.

    Args:
        user_id (str): The ID of the user.
        settings_to_update (dict): A dictionary containing the specific
                                   settings key/value pairs to update.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    log_prefix = f"User settings update for {user_id}:"


    try:
        # Try to read the existing document
        try:
            doc = user_settings_container.read_item(item=user_id, partition_key=user_id)

            # Ensure the 'settings' key exists and is a dictionary
            if 'settings' not in doc or not isinstance(doc.get('settings'), dict):
                doc['settings'] = {}


        except exceptions.CosmosResourceNotFoundError:

            # Document doesn't exist, create the basic structure
            doc = {
                "id": user_id,
                "settings": {} # Initialize the settings dictionary
                # Add any other default top-level fields if needed
            }

        # --- Merge the new settings into the 'settings' sub-dictionary ---
        doc['settings'].update(settings_to_update)

        # --- Update the timestamp ---
        # Use timezone-aware UTC time
        doc['lastUpdated'] = datetime.now(timezone.utc).isoformat()



        # Upsert the modified document
        user_settings_container.upsert_item(body=doc) # Use body=doc for clarity


        return True

    except exceptions.CosmosHttpResponseError as e:
        print(f"{log_prefix} Cosmos DB HTTP error: {e}")

        return False
    except Exception as e:
        # Catch any other unexpected errors during the update process
        print(f"{log_prefix} Unexpected error during update: {e}")

        return False

def enabled_required(setting_key):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            settings = get_settings()
            if not settings.get(setting_key, False):
                setting_key_as_statement = setting_key.replace("_", " ").title()
                return jsonify({"error": f"{setting_key_as_statement} is disabled."}), 400
            return f(*args, **kwargs)
        return wrapper
    return decorator


def sanitize_settings_for_user(full_settings: dict) -> dict:
    keys_to_exclude = {
        'azure_document_intelligence_key',
        'azure_ai_search_key',
        'azure_openai_gpt_key',
        'azure_openai_embedding_key',
        'azure_openai_image_gen_key',
        'bing_search_key',
        'azure_apim_gpt_subscription_key',
        'azure_apim_embedding_subscription_key',
        'azure_apim_image_gen_subscription_key',
        'azure_apim_web_search_subscription_key',
        'azure_apim_ai_search_subscription_key',
        'azure_apim_document_intelligence_subscription_key',
        'azure_apim_content_safety_subscription_key',
        'content_safety_key',
        'office_docs_key',
        'video_files_key',
        'audio_files_key'
        # any others that are secrets
    }
    return {k:v for k,v in full_settings.items() if k not in keys_to_exclude}