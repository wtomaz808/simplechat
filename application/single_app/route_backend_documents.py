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
        
        add_file_task_to_file_processing_log(document_id=file_id, user_id=user_id, content="Conversation exists, retrieving file content")
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
                add_file_task_to_file_processing_log(document_id=file_id, user_id=user_id, content="File not found in conversation")
                return jsonify({'error': 'File not found in conversation'}), 404

            add_file_task_to_file_processing_log(document_id=file_id, user_id=user_id, content="File found, processing content: " + str(items))
            items_sorted = sorted(items, key=lambda x: x.get('chunk_index', 0))

            filename = items_sorted[0].get('filename', 'Untitled')
            is_table = items_sorted[0].get('is_table', False)

            add_file_task_to_file_processing_log(document_id=file_id, user_id=user_id, content="Combining file content from chunks, filename: " + filename + ", is_table: " + str(is_table))
            combined_parts = []
            for it in items_sorted:
                fc = it.get('file_content', '')

                if isinstance(fc, list):
                    # If file_content is a list of dicts, join their 'content' fields
                    text_chunks = []
                    for chunk in fc:
                        text_chunks.append(chunk.get('content', ''))
                    combined_parts.append("\n".join(text_chunks))
                elif isinstance(fc, str):
                    # If it's already a string, just append
                    combined_parts.append(fc)
                else:
                    # If it's neither a list nor a string, handle as needed (e.g., skip or log)
                    pass

            combined_content = "\n".join(combined_parts)

            if not combined_content:
                add_file_task_to_file_processing_log(document_id=file_id, user_id=user_id, content="Combined file content is empty")
                return jsonify({'error': 'File content not found'}), 404

            return jsonify({
                'file_content': combined_content,
                'filename': filename,
                'is_table': is_table
            }), 200

        except Exception as e:
            add_file_task_to_file_processing_log(document_id=file_id, user_id=user_id, content="Error retrieving file content: " + str(e))
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

        # --- 1) Read pagination and filter parameters ---
        page = request.args.get('page', default=1, type=int)
        page_size = request.args.get('page_size', default=10, type=int)
        search_term = request.args.get('search', default=None, type=str)
        classification_filter = request.args.get('classification', default=None, type=str)
        author_filter = request.args.get('author', default=None, type=str)
        keywords_filter = request.args.get('keywords', default=None, type=str)
        abstract_filter = request.args.get('abstract', default=None, type=str)

        # Ensure page and page_size are positive
        if page < 1: page = 1
        if page_size < 1: page_size = 10
        # Limit page size to prevent abuse? (Optional)
        # page_size = min(page_size, 100)

        # --- 2) Build dynamic WHERE clause and parameters ---
        query_conditions = ["c.user_id = @user_id"]
        query_params = [{"name": "@user_id", "value": user_id}]
        param_count = 0 # To generate unique parameter names

        # General Search (File Name / Title)
        if search_term:
            param_name = f"@search_term_{param_count}"
            # Case-insensitive search using LOWER and CONTAINS
            query_conditions.append(f"(CONTAINS(LOWER(c.file_name ?? ''), LOWER({param_name})) OR CONTAINS(LOWER(c.title ?? ''), LOWER({param_name})))")
            query_params.append({"name": param_name, "value": search_term})
            param_count += 1

        # Classification Filter
        if classification_filter:
            param_name = f"@classification_{param_count}"
            if classification_filter.lower() == 'none':
                # Filter for documents where classification is null, undefined, or empty string
                query_conditions.append(f"(NOT IS_DEFINED(c.document_classification) OR c.document_classification = null OR c.document_classification = '')")
                # No parameter needed for this specific condition
            else:
                query_conditions.append(f"c.document_classification = {param_name}")
                query_params.append({"name": param_name, "value": classification_filter})
                param_count += 1

        # Author Filter (Assuming 'authors' is an array of strings)
        if author_filter:
            param_name = f"@author_{param_count}"
            # Use ARRAY_CONTAINS for searching within the authors array (case-insensitive)
            # Note: This checks if the array *contains* the exact author string.
            # For partial matches *within* author names, CONTAINS(ToString(c.authors)...) might be needed, but less precise.
            query_conditions.append(f"ARRAY_CONTAINS(c.authors, {param_name}, true)") # true enables case-insensitivity
            query_params.append({"name": param_name, "value": author_filter})
            param_count += 1

        # Keywords Filter (Assuming 'keywords' is an array of strings)
        if keywords_filter:
            param_name = f"@keywords_{param_count}"
            # Use ARRAY_CONTAINS for searching within the keywords array (case-insensitive)
            query_conditions.append(f"ARRAY_CONTAINS(c.keywords, {param_name}, true)") # true enables case-insensitivity
            query_params.append({"name": param_name, "value": keywords_filter})
            param_count += 1

        # Abstract Filter
        if abstract_filter:
            param_name = f"@abstract_{param_count}"
            # Case-insensitive search using LOWER and CONTAINS
            query_conditions.append(f"CONTAINS(LOWER(c.abstract ?? ''), LOWER({param_name}))")
            query_params.append({"name": param_name, "value": abstract_filter})
            param_count += 1

        # Combine conditions into the WHERE clause
        where_clause = " AND ".join(query_conditions)

        # --- 3) First query: get total count based on filters ---
        try:
            count_query_str = f"SELECT VALUE COUNT(1) FROM c WHERE {where_clause}"
            # print(f"DEBUG Count Query: {count_query_str}") # Optional Debugging
            # print(f"DEBUG Count Params: {query_params}")    # Optional Debugging
            count_items = list(documents_container.query_items(
                query=count_query_str,
                parameters=query_params,
                enable_cross_partition_query=True # May be needed if user_id is not partition key
            ))
            total_count = count_items[0] if count_items else 0

        except Exception as e:
            print(f"Error executing count query: {e}") # Log the error
            return jsonify({"error": f"Error counting documents: {str(e)}"}), 500


        # --- 4) Second query: fetch the page of data based on filters ---
        try:
            offset = (page - 1) * page_size
            # Note: ORDER BY c._ts DESC to show newest first
            data_query_str = f"""
                SELECT *
                FROM c
                WHERE {where_clause}
                ORDER BY c._ts DESC
                OFFSET {offset} LIMIT {page_size}
            """
            # print(f"DEBUG Data Query: {data_query_str}") # Optional Debugging
            # print(f"DEBUG Data Params: {query_params}")    # Optional Debugging
            docs = list(documents_container.query_items(
                query=data_query_str,
                parameters=query_params,
                enable_cross_partition_query=True # May be needed if user_id is not partition key
            ))
        except Exception as e:
            print(f"Error executing data query: {e}") # Log the error
            return jsonify({"error": f"Error fetching documents: {str(e)}"}), 500

        # --- 5) Return results ---
        return jsonify({
            "documents": docs,
            "page": page,
            "page_size": page_size,
            "total_count": total_count # This now reflects the filtered count
        }), 200


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
    
    @app.route('/api/documents/<document_id>/extract_metadata', methods=['POST'])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def api_extract_metadata(document_id):
        """
        POST /api/documents/<document_id>/extract_metadata
        Queues a background job that calls extract_document_metadata() 
        and updates the document in Cosmos DB with the new metadata.
        """
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401

        settings = get_settings()
        if not settings.get('enable_extract_meta_data'):
            return jsonify({'error': 'Metadata extraction not enabled'}), 403

        # Queue the background task (immediately returns a future)
        future = executor.submit(
            process_metadata_extraction_background,
            document_id,
            user_id
        )

        # Optionally store or track this future:
        executor.submit_stored(f"{document_id}_metadata", process_metadata_extraction_background, document_id, user_id)

        # Return an immediate response to the user
        return jsonify({
            'message': 'Metadata extraction has been queued. Check document status periodically.',
            'document_id': document_id
        }), 200


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