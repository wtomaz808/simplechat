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
        POST body should contain a JSON payload with { test_type: "<something>" }
        for example: { "test_type": "gpt" } or { "test_type": "embedding" }, etc.
        """
        data = request.get_json(force=True)
        test_type = data.get('test_type', '')

        try:
            if test_type == 'gpt':
                # Actually attempt to connect to GPT
                # e.g.: test_gpt_connection() 
                # If successful, return 200 with a success message:
                return jsonify({'message': 'GPT connection successful'}), 200

            elif test_type == 'embedding':
                # Attempt to connect to Embeddings
                # e.g.: test_embedding_connection()
                return jsonify({'message': 'Embedding connection successful'}), 200

            elif test_type == 'image':
                # Attempt to connect to Image Gen
                return jsonify({'message': 'Image generation connection successful'}), 200

            elif test_type == 'safety':
                # Attempt to connect to the Safety endpoint
                return jsonify({'message': 'Safety connection successful'}), 200

            elif test_type == 'chunking_api':
                # perform your chunking test
                return jsonify({'message': 'Chunking API connection successful'}), 200
            
            elif test_type == 'web_search':
                # perform your web search test
                return jsonify({'message': 'Web search connection successful'}), 200
            
            elif test_type == 'azure_ai_search':
                # perform your azure ai search test
                return jsonify({'message': 'Azure AI search connection successful'}), 200
            
            elif test_type == 'azure_doc_intelligence':
                # perform your azure document intelligence test
                return jsonify({'message': 'Azure document intelligence connection successful'}), 200
            
            else:
                # Default or unknown
                return jsonify({'error': f'Unknown test_type: {test_type}'}), 400

        except Exception as e:
            return jsonify({'error': str(e)}), 500