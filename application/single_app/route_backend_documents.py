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
        settings = get_settings()
        parent_document_id = str(uuid.uuid4())

        enable_enhanced_citations = settings.get('enable_enhanced_citations')
        max_file_size_bytes = settings.get('max_file_size_mb', 16) * 1024 * 1024
        di_limit_bytes = 500 * 1024 * 1024
        di_page_limit = 2000

        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if not file.filename:
            return jsonify({'error': 'No selected file'}), 400

        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()

        create_document(
            file_name=filename,
            user_id=user_id,
            document_id=parent_document_id,
            num_file_chunks=0,
            status=f"New document uploaded."
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            file.save(tmp_file.name)
            temp_file_path = tmp_file.name
            doc_title = ''
            doc_author = ''

            if file_ext in ['.pdf', '.docx', '.xlsx', '.pptx', '.html', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.heif']:
                if file_ext == '.pdf':
                     doc_title, doc_author = extract_pdf_metadata(temp_file_path)
                     doc_authors_list = parse_authors(doc_author)
                
                if file_ext == '.docx' or file_ext == '.doc':
                     doc_title, doc_author = extract_docx_metadata(temp_file_path)
                     doc_authors_list = parse_authors(doc_author)

                try:
                    # Step 2: If it's PDF (or now a converted PDF), check pages
                    page_count = 0
                    file_size = os.path.getsize(temp_file_path)
                except Exception as e:
                    return jsonify({'error': f'Error checking file size/page count: {str(e)}'}), 500

                try:
                    if file_ext == '.pdf':
                        page_count = get_pdf_page_count(temp_file_path)
                except Exception as e:
                    return jsonify({'error': f'Error checking PDF page count: {str(e)}'}), 500

                # Step 3: Validate the file against "enhanced citations" logic
                #         If false => must be <= 500MB, <= 2000 pages, <= max_file_size_bytes
                if not enable_enhanced_citations:
                    try:
                        if (file_size > di_limit_bytes or 
                            page_count > di_page_limit or 
                            file_size > max_file_size_bytes):
                            # Not supported in non-enhanced mode
                            return jsonify({
                                'error': f'File exceeds non-enhanced citations limits (max 500MB/{di_page_limit} pages/{max_file_size_bytes} bytes).'
                            }), 400
                        
                        # Otherwise, we send the entire file directly to DI
                        # No chunking in this mode
                        file_paths_to_process = [temp_file_path]
                    except Exception as e:
                        return jsonify({'error': f'Error processing file that exceeds non-enhanced limits: {str(e)}'}), 500
                
                else:
                    # Enhanced citations enabled
                    # We can handle large files up to max_file_size_bytes
                    if file_size > max_file_size_bytes:
                        return jsonify({
                            'error': f'File exceeds maximum size of {max_file_size_bytes} bytes in enhanced mode.'
                        }), 400
                    
                    # If the file is <= 500MB and <= 2000 pages, no chunk needed
                    if file_size <= di_limit_bytes and page_count <= di_page_limit:
                        try:
                            file_paths_to_process = [temp_file_path]
                        except Exception as e:
                            return jsonify({'error': f'Error processing file that does not need chunking: {str(e)}'}), 500
                    else:
                        # If it's bigger than 500MB or more than 2000 pages, chunk it in 500-page slices.
                        if file_ext == '.pdf':
                            try:
                                file_paths_to_process = chunk_pdf(temp_file_path, max_pages=500)
                                # Clean up original big PDF if chunking is successful
                                if os.path.exists(temp_file_path):
                                    os.remove(temp_file_path)
                            except Exception as e:
                                return jsonify({'error': f'Error chunking PDF that exceeds 500MB/2000 pages: {str(e)}'}), 500
                        else:
                            # If it's not PDF but somehow we got here—shouldn't happen if we always convert docx -> pdf
                            return jsonify({'error': 'Only PDF chunking is supported.'}), 400
            
                
                # Create or update the "parent" document metadata
                # We'll store total chunk count for front-end to know
                num_file_chunks = len(file_paths_to_process)
                
                update_document(
                    document_id=parent_document_id,
                    user_id=user_id,
                    num_file_chunks=num_file_chunks,
                    status=f"Processing {temp_file_path} with {num_file_chunks} chunk(s)"
                )

                if doc_title:
                    update_document(
                        document_id=parent_document_id,
                        user_id=user_id,
                        title=doc_title
                    )

                if doc_authors_list:
                    update_document(
                        document_id=parent_document_id,
                        user_id=user_id,
                        authors=doc_authors_list
                    )

                # Now loop over each chunk (or single file if no chunking)
                file_chunk_index = 1
                for chunk_path in file_paths_to_process:

                    update_document(
                        document_id=parent_document_id,
                        user_id=user_id,
                        status=f"Processing file chunk {chunk_path}, chunk {file_chunk_index} of {num_file_chunks}"
                    )
                    
                    try:
                        # Build chunked document ID if multiple chunks
                        if num_file_chunks > 1:
                            chunk_document_id = f"{parent_document_id}-chunk-{file_chunk_index}"
                        else:
                            chunk_document_id = parent_document_id

                        chunk_filename = os.path.basename(chunk_path)
                        if num_file_chunks > 1:
                            # rename chunk file for final storage (e.g. filename_chunk_01.pdf)
                            base_name, ext = os.path.splitext(chunk_filename)
                            chunk_filename = f"{base_name}_chunk_{file_chunk_index}{ext}"
                    except Exception as e:
                        return jsonify({'error': f'Error getting chunk filename and id for {chunk_path}, chunk {file_chunk_index} of {num_file_chunks}: {str(e)}'}), 500

                    try:
                        # Upload chunk to Blob Storage
                        blob_path = f"{user_id}/{chunk_filename}"

                        blob_service_client = CLIENTS.get("office_docs_client")
                        blob_client = blob_service_client.get_blob_client(
                            container=user_documents_container_name,
                            blob=blob_path
                        )
                        with open(chunk_path, "rb") as f:
                            blob_client.upload_blob(f, overwrite=True)
                    except Exception as e:
                        return jsonify({'error': f'Error uploading chunk {chunk_path}, chunk {file_chunk_index} of {num_file_chunks} to Blob Storage: {str(e)}'}), 500

                    # Add chunk metadata into Cosmos if you want a separate record
                    # (Some choose to store only the "parent" doc in Cosmos. 
                    #  But to poll chunk statuses individually, you might create child records too.)

                    update_document(
                        document_id=parent_document_id,
                        user_id=user_id,
                        status=f"Sending chunk {file_chunk_index} of {num_file_chunks} to Azure Document Intelligence"
                    )

                    # Step 5: Send chunk to Azure Document Intelligence
                    try:
                        pages = extract_content_with_azure_di(chunk_path)
                        # Possibly update chunk's status in Cosmos: "processed" or "indexed"
                        update_document(
                            document_id=parent_document_id,
                            user_id=user_id,
                            status=f"Extracted content from {chunk_filename}, {file_chunk_index} of {num_file_chunks}."
                        )

                    except Exception as e:
                        # Mark chunk as error, continue or break
                        update_document(
                            document_id=parent_document_id,
                            user_id=user_id,
                            status=f"error: failed to extract {chunk_filename}, {file_chunk_index} of {num_file_chunks}. {str(e)}"
                        )
                        return jsonify({'error': f'Error extracting file: {str(e)}'}), 500
                                        
                    try:
                         # For each page, call save_chunks (which we’ll update to handle just one chunk)
                        for page_data in pages:
                            page_number = page_data["page_number"]
                            page_content = page_data["content"]

                            update_document(
                                document_id=parent_document_id,
                                user_id=user_id,
                                num_chunks=pages,
                                status=f"Saving page {page_number} from {chunk_filename}, {file_chunk_index} of {num_file_chunks}."
                            )
                            
                            # Save each page as one "chunk"
                            save_chunks(
                                page_text_content=page_content,
                                page_number=page_number,
                                file_name=chunk_filename,
                                user_id=user_id,
                                document_id=chunk_document_id
                            )
                    except Exception as e:
                        return jsonify({'error': f'Error saving extracted content: {str(e)}'}), 500
                    finally:
                        update_document(
                            document_id=parent_document_id,
                            user_id=user_id,
                            status=f"Saved extracted content from {chunk_filename}, {file_chunk_index} of {num_file_chunks}."
                        )
                        if chunk_path != temp_file_path and os.path.exists(chunk_path):
                            os.remove(chunk_path)

                    file_chunk_index += 1

                # Optionally update the parent doc status to done
                update_document(
                    document_id=parent_document_id,
                    user_id=user_id,
                    status="Processing complete",
                    percentage_complete=100
                )
                
                return jsonify({'message': 'Document uploaded and processed successfully'}), 200
            
            elif file_ext == '.txt':
                extracted_content  = extract_text_file(temp_file_path)
                save_chunks(extracted_content , filename, user_id, document_id=parent_document_id)
                return jsonify({'message': 'Document uploaded and processed successfully'}), 200
            elif file_ext == '.md':
                extracted_content  = extract_markdown_file(temp_file_path)
                save_chunks(extracted_content , filename, user_id, document_id=parent_document_id)
                return jsonify({'message': 'Document uploaded and processed successfully'}), 200
            elif file_ext == '.json':
                with open(temp_file_path, 'r', encoding='utf-8') as f:
                    extracted_content  = json.dumps(json.load(f))
                    save_chunks(extracted_content , filename, user_id, document_id=parent_document_id)
                    return jsonify({'message': 'Document uploaded and processed successfully'}), 200
            else:
                return jsonify({'error': 'Unsupported file type'}), 400
            

        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


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