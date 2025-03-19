# route_backend_documents.py

from config import *
from functions_authentication import *
from functions_documents import *
from functions_settings import *

def register_route_backend_documents(app):
    @app.route('/api/get_file_content', methods=['POST'])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def get_file_content():
        data = request.get_json()
        user_id = get_current_user_id()
        conversation_id = data.get('conversation_id')
        file_id = data.get('file_id')

        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401

        if not conversation_id or not file_id:
            return jsonify({'error': 'Missing conversation_id or id'}), 400

        try:
            _ = container.read_item(
                item=conversation_id,
                partition_key=conversation_id
            )
        except CosmosResourceNotFoundError:
            return jsonify({'error': 'Conversation not found'}), 404
        except Exception as e:
            return jsonify({'error': f'Error reading conversation: {str(e)}'}), 500

        try:
            query_str = """
                SELECT * FROM c
                WHERE c.conversation_id = @conversation_id
                AND c.id = @file_id
            """
            items = list(messages_container.query_items(
                query=query_str,
                parameters=[
                    {'name': '@conversation_id', 'value': conversation_id},
                    {'name': '@file_id', 'value': file_id}
                ],
                partition_key=conversation_id
            ))

            if not items:
                return jsonify({'error': 'File not found in conversation'}), 404

            items_sorted = sorted(items, key=lambda x: x.get('chunk_index', 0))

            filename = items_sorted[0].get('filename', 'Untitled')
            is_table = items_sorted[0].get('is_table', False)

            combined_parts = []
            for it in items_sorted:
                combined_parts.append(it.get('file_content', ''))
            combined_content = ''.join(combined_parts)

            if not combined_content:
                return jsonify({'error': 'File content not found'}), 404

            return jsonify({
                'file_content': combined_content,
                'filename': filename,
                'is_table': is_table
            }), 200

        except Exception as e:
            return jsonify({'error': f'Error retrieving file content: {str(e)}'}), 500
    
    @app.route('/api/documents/upload', methods=['POST'])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def upload_document():
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401

        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if not file.filename:
            return jsonify({'error': 'No selected file'}), 400

        # 1) Save the file temporarily
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()

        parent_document_id = str(uuid.uuid4())
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            file.save(tmp_file.name)
            temp_file_path = tmp_file.name

        # 2) Create the Cosmos metadata with status=“queued”
        create_document(
            file_name=filename,
            user_id=user_id,
            document_id=parent_document_id,
            num_file_chunks=0,
            status="Queued for processing"  # or "Starting..."
        )

        # (Optional) set initial percentage
        update_document(
            document_id=parent_document_id,
            user_id=user_id,
            percentage_complete=0
        )

        # 3) Now run heavy-lifting in a background thread
        # Pass in user_id, doc_id, and the path to the saved file
        future = executor.submit(
            process_document_upload_background,
            parent_document_id,
            user_id,
            temp_file_path,
            filename
        )
        # If you want to store the future in memory by name, you can do:
        executor.submit_stored(parent_document_id, process_document_upload_background, ...)

        # 4) Return immediately to the user with doc ID
        return jsonify({
            'message': 'File accepted for processing. Check status periodically.',
            'document_id': parent_document_id
        }), 200


    @app.route('/api/documents', methods=['GET'])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def api_get_user_documents():
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
                
        return get_user_documents(user_id)

    @app.route('/api/documents/<document_id>', methods=['GET'])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def api_get_user_document(document_id):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        return get_user_document(user_id, document_id)

    @app.route('/api/documents/<document_id>', methods=['PATCH'])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def api_patch_user_document(document_id):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401

        data = request.get_json()  # new metadata values from the client

        # Update allowed fields
        # You can decide which fields can be updated from the client
        if 'title' in data:
            update_document(
                document_id=document_id,
                user_id=user_id,
                title=data['title']
            )
        if 'abstract' in data:
            update_document(
                document_id=document_id,
                user_id=user_id,
                abstract=data['abstract']
            )
        if 'keywords' in data:
            # Expect a list or a comma-delimited string
            if isinstance(data['keywords'], list):
                update_document(
                    document_id=document_id,
                    user_id=user_id,
                    keywords=data['keywords']
                )
            else:
                # if client sends a comma-separated string of keywords
                update_document(
                    document_id=document_id,
                    user_id=user_id,
                    keywords=[kw.strip() for kw in data['keywords'].split(',')]
                )
        if 'publication_date' in data:
            update_document(
                document_id=document_id,
                user_id=user_id,
                publication_date=data['publication_date']
            )
        if 'document_classification' in data:
            update_document(
                document_id=document_id,
                user_id=user_id,
                document_classification=data['document_classification']
            )
        # Add authors if you want to allow editing that
        if 'authors' in data:
            # if you want a list, or just store a string
            # here is one approach:
            if isinstance(data['authors'], list):
                update_document(
                    document_id=document_id,
                    user_id=user_id,
                    authors=data['authors']
                )
            else:
                update_document(
                    document_id=document_id,
                    user_id=user_id,
                    authors=[data['authors']]
                )

        # Save updates back to Cosmos
        try:
            return jsonify({'message': 'Document metadata updated successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500


    @app.route('/api/documents/<document_id>', methods=['DELETE'])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def api_delete_user_document(document_id):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        try:
            delete_user_document(user_id, document_id)
            delete_user_document_chunks(document_id)
            return jsonify({'message': 'Document deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': f'Error deleting document: {str(e)}'}), 500
        
    @app.route("/api/get_citation", methods=["POST"])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def get_citation():
        data = request.get_json()
        user_id = get_current_user_id()
        citation_id = data.get("citation_id")

        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
                
        if not citation_id:
            return jsonify({"error": "Missing citation_id"}), 400

        try:
            search_client_user = CLIENTS['search_client_user']
            chunk = search_client_user.get_document(key=citation_id)
            if chunk.get("user_id") != user_id:
                return jsonify({"error": "Unauthorized access to citation"}), 403

            return jsonify({
                "cited_text": chunk.get("chunk_text", ""),
                "file_name": chunk.get("file_name", ""),
                "page_number": chunk.get("chunk_sequence", 0)
            }), 200

        except ResourceNotFoundError:
            pass

        try:
            search_client_group = CLIENTS['search_client_group']
            group_chunk = search_client_group.get_document(key=citation_id)

            return jsonify({
                "cited_text": group_chunk.get("chunk_text", ""),
                "file_name": group_chunk.get("file_name", ""),
                "page_number": group_chunk.get("chunk_sequence", 0)
            }), 200

        except ResourceNotFoundError:
            return jsonify({"error": "Citation not found in user or group docs"}), 404

        except Exception as e:
            return jsonify({"error": f"Unexpected error: {str(e)}"}), 500