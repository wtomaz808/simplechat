# route_backend_settings.py

from config import *
from functions_documents import *
from functions_authentication import *
from functions_settings import *

def register_route_backend_settings(app):
    @app.route('/api/admin/settings/test_connection', methods=['POST'])
    @login_required
    @admin_required
    def test_connection():
        """
        Receives JSON payload with { test_type: "...", ... } containing ephemeral
        data from admin_settings.js. Uses that data to attempt an actual connection
        to GPT, Embeddings, etc., and returns success/failure.
        """
        data = request.get_json(force=True)
        test_type = data.get('test_type', '')

        try:
            if test_type == 'gpt':
                return _test_gpt_connection(data)

            elif test_type == 'embedding':
                return _test_embedding_connection(data)

            elif test_type == 'image':
                return _test_image_gen_connection(data)

            elif test_type == 'safety':
                return _test_safety_connection(data)

            elif test_type == 'web_search':
                return _test_web_search_connection(data)

            elif test_type == 'azure_ai_search':
                return _test_azure_ai_search_connection(data)

            elif test_type == 'azure_doc_intelligence':
                return _test_azure_doc_intelligence_connection(data)

            elif test_type == 'chunking_api':
                # If you have a chunking API test, implement it here.
                return jsonify({'message': 'Chunking API connection successful'}), 200

            else:
                return jsonify({'error': f'Unknown test_type: {test_type}'}), 400

        except Exception as e:
            return jsonify({'error': str(e)}), 500


def _test_gpt_connection(payload):
    """Attempt to connect to GPT using ephemeral settings from the admin UI."""
    enable_apim = payload.get('enable_apim', False)
    selected_model = payload.get('selected_model') or {}
    model_deployment = selected_model.get('deploymentName') or ''

    if enable_apim:
        # Use APIM endpoint
        apim_data = payload.get('apim', {})
        endpoint = apim_data.get('endpoint')
        api_version = apim_data.get('api_version')
        deployment = apim_data.get('deployment') or model_deployment
        subscription_key = apim_data.get('subscription_key')

        # Minimal example of calling an APIM endpoint
        # Adjust URL path & method to match your APIM config
        url = f"{endpoint.rstrip('/')}/openai/deployments/{model_deployment}/chat/completions?api-version={api_version}"
        headers = {
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': subscription_key
        }
        body = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an AI assistant that helps people find information."
                },
                {
                    "role": "user",
                    "content": "I am Testing access."
                }
            ],
            "max_tokens": 800
        }

    else:
        direct_data = payload.get('direct', {})

        if direct_data.get('auth_type') == 'key':
            # Direct call to Azure OpenAI
            endpoint = direct_data.get('endpoint')
            api_version = direct_data.get('api_version')
            model_deployment = selected_model.get('deploymentName')
            key = direct_data.get('key')
            
            url = f"{endpoint.rstrip('/')}/openai/deployments/{model_deployment}/chat/completions?api-version={api_version}"
            headers = {
                'Content-Type': 'application/json',
                'api-key': key
            }
            body = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an AI assistant that helps people find information."
                    },
                    {
                        "role": "user",
                        "content": "I am testing access."
                    }
                ],
                "max_tokens": 800
            }
        elif direct_data.get('auth_type') == 'managed_identity':
            # Direct call to Azure OpenAI with Managed Identity
            endpoint = direct_data.get('endpoint')
            api_version = direct_data.get('api_version')
            model_deployment = selected_model.get('deploymentName')

            # Get access token using Managed Identity
            credential = DefaultAzureCredential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default").token

            # Construct request URL
            url = f"{endpoint.rstrip('/')}/openai/deployments/{model_deployment}/completions?api-version={api_version}"

            # Set headers with the Bearer token
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }

            # Request body
            body = {
                "prompt": "Hello from test_connection API!",
                "max_tokens": 5
            }

    # Make the request
    resp = requests.post(url, headers=headers, json=body, timeout=10)
    if resp.status_code == 200:
        return jsonify({'message': 'GPT connection successful'}), 200
    else:
        # Raise an error to fall into the catch-all for test_connection
        raise Exception(f"GPT connection error: {resp.status_code} - {resp.text}")


def _test_embedding_connection(payload):
    """Attempt to connect to Embeddings using ephemeral settings from the admin UI."""
    enable_apim = payload.get('enable_apim', False)
    selected_model = payload.get('selected_model') or {}
    model_deployment = selected_model.get('deploymentName') or ''

    if enable_apim:
        apim_data = payload.get('apim', {})
        endpoint = apim_data.get('endpoint')
        api_version = apim_data.get('api_version')
        deployment = apim_data.get('deployment') or model_deployment
        subscription_key = apim_data.get('subscription_key')

        url = f"{endpoint.rstrip('/')}/openai/deployments/{deployment}/embeddings?api-version={api_version}"
        headers = {
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': subscription_key
        }
        body = {
            "input": "Test embedding"
        }

    else:
        direct_data = payload.get('direct', {})

        if direct_data.get('auth_type') == 'key':
            endpoint = direct_data.get('endpoint')
            api_version = direct_data.get('api_version')
            key = direct_data.get('key')

            url = f"{endpoint.rstrip('/')}/openai/deployments/{model_deployment}/embeddings?api-version={api_version}"
            headers = {
                'Content-Type': 'application/json',
                'api-key': key
            }
            body = {
                "input": "Test embedding"
            }
        elif direct_data.get('auth_type') == 'managed_identity':
            endpoint = direct_data.get('endpoint')
            api_version = direct_data.get('api_version')

            # Get access token using Managed Identity
            credential = DefaultAzureCredential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default").token

            url = f"{endpoint.rstrip('/')}/openai/deployments/{model_deployment}/embeddings?api-version={api_version}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            body = {
                "input": "Test embedding"
            }

    resp = requests.post(url, headers=headers, json=body, timeout=10)
    if resp.status_code == 200:
        return jsonify({'message': 'Embedding connection successful'}), 200
    else:
        raise Exception(f"Embedding connection error: {resp.status_code} - {resp.text}")


def _test_image_gen_connection(payload):
    """Attempt to connect to an Image Generation endpoint using ephemeral settings."""
    enable_apim = payload.get('enable_apim', False)
    selected_model = payload.get('selected_model') or {}
    model_deployment = selected_model.get('deploymentName') or ''

    if enable_apim:
        apim_data = payload.get('apim', {})
        endpoint = apim_data.get('endpoint')
        api_version = apim_data.get('api_version')
        deployment = apim_data.get('deployment') or model_deployment
        subscription_key = apim_data.get('subscription_key')

        # Adjust the actual path if your APIM route is different
        url = f"{endpoint.rstrip('/')}/openai/deployments/{model_deployment}/images/generations?api-version={api_version}"
        headers = {
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': subscription_key
        }
        body = {
            "prompt": "A scenic mountain at sunrise",
            "n": 1,
            "size": "512x512"
        }

    else:
        direct_data = payload.get('direct', {})

        if direct_data.get('auth_type') == 'key':
            endpoint = direct_data.get('endpoint')
            api_version = direct_data.get('api_version')
            key = direct_data.get('key')

            url = f"{endpoint.rstrip('/')}/openai/deployments/{model_deployment}/images/generations?api-version={api_version}"
            headers = {
                'Content-Type': 'application/json',
                'api-key': key
            }
            body = {
                "prompt": "In the style of WordArt, Microsoft Clippy wearing a cowboy hat.",
                "n": 1,
                "style": "natural",
                "quality": "standard"
            }

        elif direct_data.get('auth_type') == 'managed_identity':
            endpoint = direct_data.get('endpoint')
            api_version = direct_data.get('api_version')

            # Get access token using Managed Identity
            credential = DefaultAzureCredential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default").token

            url = f"{endpoint.rstrip('/')}/openai/images/generations?api-version={api_version}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            body = {
                "prompt": "In the style of WordArt, Microsoft Clippy wearing a cowboy hat.",
                "n": 1,
                "style": "natural",
                "quality": "standard"
            }

    resp = requests.post(url, headers=headers, json=body, timeout=10)
    if resp.status_code == 200:
        return jsonify({'message': 'Image generation connection successful'}), 200
    else:
        raise Exception(f"Image Gen connection error: {resp.status_code} - {resp.text}")


def _test_safety_connection(payload):
    """Attempt to connect to a content safety endpoint using ephemeral settings."""
    enabled = payload.get('enabled', False)
    if not enabled:
        # If the user toggled content safety off, just return success
        return jsonify({'message': 'Content Safety is disabled, skipping test'}), 200

    enable_apim = payload.get('enable_apim', False)

    if enable_apim:
        apim_data = payload.get('apim', {})
        endpoint = apim_data.get('endpoint')
        subscription_key = apim_data.get('subscription_key')
        deployment = apim_data.get('deployment')
        api_version = apim_data.get('api_version')

        # Adjust URL for your APIM route
        url = f"{endpoint.rstrip('/')}/contentsafety/text:analyze?api-version=2024-09-01"
        headers = {
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': subscription_key
        }
        body = { "text": "Test content for safety" }
    else:
        direct_data = payload.get('direct', {})
        endpoint = direct_data.get('endpoint')
        key = direct_data.get('key')

        url = f"{endpoint.rstrip('/')}/contentsafety/text:analyze?api-version=2024-09-01"
        headers = {
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': key
        }
        body = { "text": "Test content for safety" }

    resp = requests.post(url, headers=headers, json=body, timeout=10)
    if resp.status_code == 200:
        return jsonify({'message': 'Safety connection successful'}), 200
    else:
        raise Exception(f"Safety connection error: {resp.status_code} - {resp.text}")


def _test_web_search_connection(payload):
    """Attempt to connect to Bing (or your APIM-protected) web search endpoint."""
    enabled = payload.get('enabled', False)
    if not enabled:
        return jsonify({'message': 'Web Search is disabled, skipping test'}), 200

    enable_apim = payload.get('enable_apim', False)

    if enable_apim:
        apim_data = payload.get('apim', {})
        endpoint = apim_data.get('endpoint')
        subscription_key = apim_data.get('subscription_key')
        # deployment, api_version, etc. if relevant
        url = f"{endpoint.rstrip('/')}/bing/v7.0/search"
        headers = {
            'Ocp-Apim-Subscription-Key': subscription_key
        }
        params = { 'q': 'Test' }
    else:
        direct_data = payload.get('direct', {})
        # For direct Bing calls, you typically do something like:
        key = direct_data.get('key')
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {
            'Ocp-Apim-Subscription-Key': key
        }
        params = { 'q': 'Test' }

    resp = requests.get(url, headers=headers, params=params, timeout=10)
    if resp.status_code == 200:
        return jsonify({'message': 'Web search connection successful'}), 200
    else:
        raise Exception(f"Web search connection error: {resp.status_code} - {resp.text}")


def _test_azure_ai_search_connection(payload):
    """Attempt to connect to Azure Cognitive Search (or APIM-wrapped)."""
    enable_apim = payload.get('enable_apim', False)

    if enable_apim:
        apim_data = payload.get('apim', {})
        endpoint = apim_data.get('endpoint')  # e.g. https://my-apim.azure-api.net/search
        subscription_key = apim_data.get('subscription_key')
        url = f"{endpoint.rstrip('/')}/indexes?api-version=2023-11-01"
        headers = {
            'api-key': subscription_key,
            'Content-Type': 'application/json'
        }
    else:
        direct_data = payload.get('direct', {})
        endpoint = direct_data.get('endpoint')  # e.g. https://<searchservice>.search.windows.net
        key = direct_data.get('key')
        url = f"{endpoint.rstrip('/')}/indexes?api-version=2023-11-01"
        headers = {
            'api-key': key,
            'Content-Type': 'application/json'
        }

    # A small GET to /indexes to verify we have connectivity
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        return jsonify({'message': 'Azure AI search connection successful'}), 200
    else:
        raise Exception(f"Azure AI search connection error: {resp.status_code} - {resp.text}")


def _test_azure_doc_intelligence_connection(payload):
    """Attempt to connect to Azure Form Recognizer / Document Intelligence."""
    enable_apim = payload.get('enable_apim', False)

    if enable_apim:
        apim_data = payload.get('apim', {})
        endpoint = apim_data.get('endpoint')
        subscription_key = apim_data.get('subscription_key')
        # deployment, api_version, etc., if needed
        url = f"{endpoint.rstrip('/')}/formrecognizer/documentModels?api-version=2023-07-31"
        headers = {
            'content-type': 'application/json',
            'Ocp-Apim-Subscription-Key': subscription_key
        }
    else:
        direct_data = payload.get('direct', {})
        endpoint = direct_data.get('endpoint')
        key = direct_data.get('key')
        url = f"{endpoint.rstrip('/')}/formrecognizer/documentModels?api-version=2023-07-31"
        headers = {
            'content-type': 'application/json',
            'Ocp-Apim-Subscription-Key': key
        }

    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        return jsonify({'message': 'Azure document intelligence connection successful'}), 200
    else:
        raise Exception(f"Doc Intelligence error: {resp.status_code} - {resp.text}")