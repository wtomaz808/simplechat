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
            'app_title': 'AI Chat Application',
            'show_logo': False,
            'logo_path': 'images/logo.svg',
            'max_file_size_mb': 150,
            'conversation_history_limit': 10,
            'default_system_prompt': '',
            'use_external_apis': False,
            'external_chunking_api': '',
            'external_embedding_api': '',
            'enable_user_documents': True,
            'enable_group_documents': True,
            'azure_openai_gpt_endpoint': '',
            'azure_openai_gpt_api_version': '',
            'azure_openai_gpt_authentication_type': 'key',
            'azure_openai_gpt_subscription_id': '',
            'azure_openai_gpt_resource_group': '',
            'azure_openai_gpt_key': '',
            'gpt_model': {
                "selected": [],
                "all": [] 
            },
            'azure_openai_embedding_endpoint': '',
            'azure_openai_embedding_api_version': '',
            'azure_openai_embedding_authentication_type': 'key',
            'azure_openai_embedding_subscription_id': '',
            'azure_openai_embedding_resource_group': '',
            'azure_openai_embedding_key': '',
            'embedding_model': {
                "selected": [],
                "all": []
            },
            'enable_image_generation': False,
            'azure_openai_image_gen_endpoint': '',
            'azure_openai_image_gen_api_version': '',
            'azure_openai_image_gen_authentication_type': 'key',
            'azure_openai_image_gen_subscription_id': '',
            'azure_openai_image_gen_resource_group': '',
            'azure_openai_image_gen_key': '',
            'image_gen_model': {
                "selected": [],
                "all": []
            },
            'enable_web_search': False,
            'bing_search_key': '',
            'landing_page_text': 'Click the button below to start chatting with the AI assistant.',
            'enable_gpt_apim': False,
            'enable_image_gen_apim': False,
            'enable_embedding_apim': False,
            'azure_apim_gpt_endpoint': '',
            'azure_apim_gpt_subscription_key': '',
            'azure_apim_gpt_deployment': '',
            'azure_apim_gpt_api_version': '',
            'azure_apim_embedding_endpoint': '',
            'azure_apim_embedding_subscription_key': '',
            'azure_apim_embedding_deployment': '',
            'azure_apim_embedding_api_version': '',
            'azure_apim_image_gen_endpoint': '',
            'azure_apim_image_gen_subscription_key': '',
            'azure_apim_image_gen_deployment': '',
            'azure_apim_image_gen_api_version': ''          
            
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
    doc_id = str(user_id)
    try:
        return user_settings_container.read_item(item=doc_id, partition_key=doc_id)
    except exceptions.CosmosResourceNotFoundError:
        return {
            "id": user_id,
            "settings": {
                "activeGroupOid": ""
            },
            "lastUpdated": None
        }
    
def update_user_settings(user_id, new_settings):
    doc_id = str(user_id)
    try:
        doc = user_settings_container.read_item(item=doc_id, partition_key=doc_id)
        doc.update(new_settings)
        user_settings_container.upsert_item(doc)
    except exceptions.CosmosResourceNotFoundError:
        doc = {
            "id": doc_id,
            **new_settings
        }
        user_settings_container.upsert_item(doc)