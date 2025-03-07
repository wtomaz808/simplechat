# functions_documents.py

from config import *
from functions_content import *
from functions_settings import *

def allowed_file(filename, allowed_extensions=None):
    if not allowed_extensions:
        allowed_extensions = ALLOWED_EXTENSIONS
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def add_system_message_to_conversation(conversation_id, user_id, content):
    try:
        conversation_item = container.read_item(
            item=conversation_id,
            partition_key=conversation_id
        )

        conversation_item['messages'].append({
            "role": "system",
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        conversation_item['last_updated'] = datetime.utcnow().isoformat()

        container.upsert_item(conversation_item)

    except Exception as e:
        raise e
    
def create_document(file_name, user_id, document_id, num_file_chunks, status):
    current_time = datetime.now(timezone.utc)
    formatted_time = current_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    existing_document_query = """
        SELECT c.version 
        FROM c 
        WHERE c.file_name = @file_name AND c.user_id = @user_id
    """
    parameters = [{"name": "@file_name", "value": file_name}, {"name": "@user_id", "value": user_id}]
    
    try:
        existing_document = list(documents_container.query_items(query=existing_document_query, parameters=parameters, enable_cross_partition_query=True))
    except Exception as e:
        print(f"Error querying existing document: {e}")
        raise

    if existing_document:
        version = existing_document[0]['version'] + 1
    else:
        version = 1

    try:
        document_metadata = {
            "id": document_id,
            "file_name": file_name,
            "user_id": user_id,
            "num_chunks": 0,
            "num_file_chunks": num_file_chunks,
            "upload_date": formatted_time,
            "last_updated": formatted_time,
            "version": version,
            "status": status,
            "percentage_complete": 0,
            "type": "document_metadata"
        }
        documents_container.upsert_item(document_metadata)
    except Exception as e:
        print(f"Error upserting document metadata: {e}")
        raise

def get_document_metadata(document_id, user_id):
    try:
        query = """
            SELECT *
            FROM c
            WHERE c.user_id = @user_id AND c.id = @document_id
        """
        parameters = [
            {"name": "@user_id", "value": user_id},
            {"name": "@document_id", "value": document_id}
        ]
        
        document_items = list(documents_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        
        if not document_items:
            return None
        
        return document_items[0]
    except Exception as e:
        print(f"Error retrieving document metadata: {e}")
        return None
    
def update_document(**kwargs):
    document_id     = kwargs.get('document_id')
    user_id         = kwargs.get('user_id')
    status          = kwargs.get('status')
    author          = kwargs.get('author')
    summary         = kwargs.get('summary')
    keywords        = kwargs.get('keywords')
    number_of_pages = kwargs.get('number_of_pages')
    num_chunks      = kwargs.get('num_chunks')
    version         = kwargs.get('version')
    file_name       = kwargs.get('file_name')
    title           = kwargs.get('title')
    percentage_complete = kwargs.get('percentage_complete')
    current_chunk   = kwargs.get('current_chunk')

    current_time = datetime.now(timezone.utc)
    formatted_time = current_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    try:
        # Retrieve the existing document
        query = """
            SELECT *
            FROM c
            WHERE c.user_id = @user_id AND c.id = @document_id
        """
        parameters = [
            {"name": "@user_id", "value": user_id},
            {"name": "@document_id", "value": document_id}
        ]
        
        existing_documents = list(documents_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        if not existing_documents:
            raise CosmosResourceNotFoundError(f"Document {document_id} not found")

        existing_document = existing_documents[0]

        if status:
            # Update the necessary fields
            existing_document['status'] = status
            existing_document['last_updated'] = formatted_time

            if "Processing Complete" in status.lower():
                existing_document['percentage_complete'] = 100
            elif "failed" in status.lower():
                existing_document['percentage_complete'] = 0
            else:
                if existing_document.get('percentage_complete', 0) >= 90:
                    existing_document['percentage_complete'] = 90
                else:
                    existing_document['percentage_complete'] = existing_document.get('percentage_complete') + 1

        if title:
            existing_document['title'] = title

        if author:
            existing_document['author'] = author

        if summary:
            existing_document['summary'] = summary

        if keywords:
            existing_document['keywords'] = keywords
        
        if number_of_pages:
            existing_document['number_of_pages'] = number_of_pages

        if num_chunks:
            existing_document['num_chunks'] = num_chunks

        if version:
            existing_document['version'] = version

        if file_name:
            existing_document['file_name'] = file_name

        if percentage_complete:
            existing_document['percentage_complete'] = percentage_complete


        # Upsert the updated document
        documents_container.upsert_item(existing_document)

    except CosmosResourceNotFoundError as e:
        print(f"Document {document_id} not found: {e}")
        raise
    except Exception as e:
        print(f"Error updating document status for document {document_id}: {e}")
        raise
    
def save_chunks(page_text_content, page_number, file_name, user_id, document_id):
    """
    Save a single chunk (one page) at a time:
      - Generate embedding
      - Build chunk metadata
      - Upload to Search index
    """
    settings = get_settings()

    current_time = datetime.now(timezone.utc)
    formatted_time = current_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    try:
        # Update document status
        num_chunks = 1  # because we only have one chunk (page) here
        status = f"Processing 1 chunk (page {page_number})"
        update_document(document_id=document_id, user_id=user_id, status=status)

        version = get_document_metadata(document_id, user_id)['version']
        
    except Exception as e:
        print(f"Error updating document status or retrieving metadata for document {document_id}: {e}")
        raise

    # Generate embedding
    try:
        status = f"Generating embedding for page {page_number}"
        update_document(document_id=document_id, user_id=user_id, status=status)
        embedding = generate_embedding(page_text_content)
    except Exception as e:
        print(f"Error generating embedding for page {page_number} of document {document_id}: {e}")
        raise

    # Build chunk document
    try:
        chunk_id = f"{document_id}_{page_number}"
        chunk_keywords = []
        chunk_summary = ""
        author = []
        title = ""

        chunk_document = {
            "id": chunk_id,
            "document_id": document_id,
            "chunk_id": str(page_number),
            "chunk_text": page_text_content,
            "embedding": embedding,
            "file_name": file_name,
            "user_id": user_id,
            "chunk_keywords": chunk_keywords,
            "chunk_summary": chunk_summary,
            "page_number": page_number,
            "author": author,
            "title": title,
            "chunk_sequence": page_number,  # or you can keep an incremental idx
            "upload_date": formatted_time,
            "version": version
        }
    except Exception as e:
        print(f"Error creating chunk document for page {page_number} of document {document_id}: {e}")
        raise

    # Upload chunk document to Search
    try:
        status = f"Uploading page {page_number} of document {document_id} to index."
        update_document(document_id=document_id, user_id=user_id, status=status)

        search_client_user = CLIENTS["search_client_user"]
        # Upload as a single-document list
        search_client_user.upload_documents(documents=[chunk_document])
    except Exception as e:
        print(f"Error uploading chunk document for document {document_id}: {e}")
        raise


def get_pdf_page_count(pdf_path: str) -> int:
    reader = PdfReader(pdf_path)
    return len(reader.pages)

def chunk_pdf(input_pdf_path: str, max_pages: int = 500) -> list:
    """
    Splits a PDF into multiple PDFs, each with up to `max_pages` pages.
    Returns a list of file paths for the newly created chunks.
    """
    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)
    chunks = []
    current_page = 0
    chunk_index = 1

    base_name, ext = os.path.splitext(input_pdf_path)

    while current_page < total_pages:
        writer = PdfWriter()
        end_page = min(current_page + max_pages, total_pages)

        for p in range(current_page, end_page):
            writer.add_page(reader.pages[p])

        chunk_pdf_path = f"{base_name}_chunk_{chunk_index}{ext}"
        with open(chunk_pdf_path, "wb") as f:
            writer.write(f)

        chunks.append(chunk_pdf_path)
        current_page = end_page
        chunk_index += 1

    return chunks

def get_user_documents(user_id):
    try:
        query = """
            SELECT c.file_name, c.id, c.upload_date, c.user_id, c.num_chunks ,c.version
            FROM c
            WHERE c.user_id = @user_id
        """
        parameters = [{"name": "@user_id", "value": user_id}]
        
        documents = list(documents_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        latest_documents = {}

        for doc in documents:
            file_name = doc['file_name']
            if file_name not in latest_documents or doc['version'] > latest_documents[file_name]['version']:
                latest_documents[file_name] = doc
                
        return jsonify({"documents": list(latest_documents.values())}), 200
    except Exception as e:
        return jsonify({'error': f'Error retrieving documents: {str(e)}'}), 500

def get_user_document(user_id, document_id):

    try:
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

        document_results = list(documents_container.query_items(
            query=latest_version_query, 
            parameters=parameters, 
            enable_cross_partition_query=True
        ))

        if not document_results:
            return jsonify({'error': 'Document not found or access denied'}), 404

        return jsonify(document_results[0]), 200

    except Exception as e:
        return jsonify({'error': f'Error retrieving document: {str(e)}'}), 500

def get_latest_version(document_id, user_id):

    query = """
        SELECT c.version
        FROM c 
        WHERE c.id = @document_id AND c.user_id = @user_id
    """
    parameters = [
        {"name": "@document_id", "value": document_id},
        {"name": "@user_id", "value": user_id}
    ]

    try:
        results = list(documents_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

        if results:
            max_version = max(item['version'] for item in results)
            return max_version
        else:
            return None

    except Exception as e:
        return None
    
def get_user_document_version(user_id, document_id, version):
    try:
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
            return jsonify({'error': 'Document version not found'}), 404

        return jsonify(document_results[0]), 200

    except Exception as e:
        return jsonify({'error': f'Error retrieving document version: {str(e)}'}), 500

def delete_user_document(user_id, document_id):
    """Delete a document from the user's documents in Cosmos DB."""
    try:
        document_item = documents_container.read_item(
            item=document_id,
            partition_key=document_id
        )

        if document_item.get('user_id') != user_id:
            raise Exception("Unauthorized access to document")

        documents_container.delete_item(
            item=document_id,
            partition_key=document_id
        )
    except CosmosResourceNotFoundError:
        raise Exception("Document not found")
    except Exception as e:
        raise

def delete_user_document_chunks(document_id):
    """Delete document chunks from Azure Cognitive Search index."""
    try:
        search_client_user = CLIENTS["search_client_user"]
        results = search_client_user.search(
            search_text="*",
            filter=f"document_id eq '{document_id}'",
            select=["id"]
        )

        ids_to_delete = [doc['id'] for doc in results]

        if not ids_to_delete:
            return

        documents_to_delete = [{"id": doc_id} for doc_id in ids_to_delete]
        batch = IndexDocumentsBatch()
        batch.add_delete_actions(documents_to_delete)
        result = search_client_user.index_documents(batch)
    except Exception as e:
        raise

def delete_user_document_version(user_id, document_id, version):
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

    for doc in documents:
        documents_container.delete_item(doc['id'], partition_key=doc['user_id'])

def delete_user_document_version_chunks(document_id, version):
    search_client_user = CLIENTS["search_client_user"]
    search_client_user.delete_documents(
        actions=[
            {"@search.action": "delete", "id": chunk['id']} for chunk in 
            search_client_user.search(
                search_text="*",
                filter=f"document_id eq '{document_id}' and version eq {version}",
                select="id"
            )
        ]
    )

def get_document_versions(user_id, document_id):
    try:
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
            return []
        return versions_results

    except Exception as e:
        return []
    
def detect_doc_type(document_id, user_id=None):
    """
    Check Cosmos to see if this doc belongs to the user's docs (has user_id)
    or the group's docs (has group_id).
    Returns one of: "user", "group", or None if not found.
    Optionally checks if user_id matches (for user docs).
    """

    try:
        doc_item = documents_container.read_item(document_id, partition_key=document_id)
        if user_id and doc_item.get('user_id') != user_id:
            pass
        else:
            return "user"
    except:
        pass

    try:
        group_doc_item = group_documents_container.read_item(document_id, partition_key=document_id)
        return "group"
    except:
        pass

    return None

def process_document_upload_background(document_id, user_id, temp_file_path, original_filename):
    """
    Runs in a background thread via Flask-Executor.
    Chunk the file, call Azure DI, upsert each page into Search, update doc status in Cosmos, etc.
    """
    settings = get_settings()
    enable_enhanced_citations = settings.get('enable_enhanced_citations')
    max_file_size_bytes = settings.get('max_file_size_mb', 16) * 1024 * 1024
    di_limit_bytes = 500 * 1024 * 1024
    di_page_limit = 2000

    file_ext = os.path.splitext(original_filename)[-1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
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
                document_id=document_id,
                user_id=user_id,
                num_file_chunks=num_file_chunks,
                status=f"Processing {temp_file_path} with {num_file_chunks} chunk(s)"
            )

            if doc_title:
                update_document(
                    document_id=document_id,
                    user_id=user_id,
                    title=doc_title
                )

            if doc_authors_list:
                update_document(
                    document_id=document_id,
                    user_id=user_id,
                    authors=doc_authors_list
                )

            # Now loop over each chunk (or single file if no chunking)
            file_chunk_index = 1
            for chunk_path in file_paths_to_process:

                update_document(
                    document_id=document_id,
                    user_id=user_id,
                    status=f"Processing file chunk {chunk_path}, chunk {file_chunk_index} of {num_file_chunks}"
                )
                
                try:
                    # Build chunked document ID if multiple chunks
                    if num_file_chunks > 1:
                        chunk_document_id = f"{document_id}-chunk-{file_chunk_index}"
                    else:
                        chunk_document_id = document_id

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
                    document_id=document_id,
                    user_id=user_id,
                    status=f"Sending chunk {file_chunk_index} of {num_file_chunks} to Azure Document Intelligence"
                )

                # Step 5: Send chunk to Azure Document Intelligence
                try:
                    pages = extract_content_with_azure_di(chunk_path)
                    # Possibly update chunk's status in Cosmos: "processed" or "indexed"
                    update_document(
                        document_id=document_id,
                        user_id=user_id,
                        status=f"Extracted content from {chunk_filename}, {file_chunk_index} of {num_file_chunks}."
                    )

                except Exception as e:
                    # Mark chunk as error, continue or break
                    update_document(
                        document_id=document_id,
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
                            document_id=document_id,
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
                        document_id=document_id,
                        user_id=user_id,
                        status=f"Saved extracted content from {chunk_filename}, {file_chunk_index} of {num_file_chunks}."
                    )
                    if chunk_path != temp_file_path and os.path.exists(chunk_path):
                        os.remove(chunk_path)

                file_chunk_index += 1

            # Optionally update the parent doc status to done
            update_document(
                document_id=document_id,
                user_id=user_id,
                status="Processing complete",
                percentage_complete=100
            )
            
            return jsonify({'message': 'Document uploaded and processed successfully'}), 200
        
        elif file_ext == '.txt':
            extracted_content  = extract_text_file(temp_file_path)
            save_chunks(extracted_content , original_filename, user_id, document_id=document_id)
            return jsonify({'message': 'Document uploaded and processed successfully'}), 200
        elif file_ext == '.md':
            extracted_content  = extract_markdown_file(temp_file_path)
            save_chunks(extracted_content , original_filename, user_id, document_id=document_id)
            return jsonify({'message': 'Document uploaded and processed successfully'}), 200
        elif file_ext == '.json':
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                extracted_content  = json.dumps(json.load(f))
                save_chunks(extracted_content , original_filename, user_id, document_id=document_id)
                return jsonify({'message': 'Document uploaded and processed successfully'}), 200
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        

    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
