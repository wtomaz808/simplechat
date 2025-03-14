# functions_documents.py

from config import *
from functions_content import *
from functions_settings import *
from functions_search import *

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
    

def add_file_task_to_file_processing_log(document_id, user_id, content):
    settings = get_settings()
    enable_file_processing_log = settings.get('enable_file_processing_log', True)

    if enable_file_processing_log:
        try:
            id_value = str(uuid.uuid4())
            log_item = {
                "id": id_value,
                "document_id": document_id,
                "user_id": user_id,
                "log": content,
                "timestamp": datetime.utcnow().isoformat()
            }
            file_processing_container.create_item(log_item)
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
            "document_classification": "TBD",
            "type": "document_metadata"
        }
        documents_container.upsert_item(document_metadata)

        add_file_task_to_file_processing_log(
            document_id, 
            user_id, 
            f"Document {file_name} created."
        )

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
    document_id             = kwargs.get('document_id')
    user_id                 = kwargs.get('user_id')
    status                  = kwargs.get('status')
    authors                 = kwargs.get('authors')
    abstract                = kwargs.get('abstract')
    keywords                = kwargs.get('keywords')
    number_of_pages         = kwargs.get('number_of_pages')
    num_chunks              = kwargs.get('num_chunks')
    version                 = kwargs.get('version')
    number_of_file_chunks   = kwargs.get('number_of_file_chunks')
    file_name               = kwargs.get('file_name')
    title                   = kwargs.get('title')
    publication_date        = kwargs.get('publication_date')
    percentage_complete     = kwargs.get('percentage_complete')
    current_page            = kwargs.get('current_page')
    current_file_chunk      = kwargs.get('current_file_chunk')
    organization            = kwargs.get('organization')
    enhanced_citations      = kwargs.get('enhanced_citations')
    document_classification = kwargs.get('document_classification')

    current_time = datetime.now(timezone.utc)
    formatted_time = current_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    add_file_task_to_file_processing_log(
        document_id, 
        user_id, 
        f"Updating document {document_id} for user {user_id} with all fields: {kwargs}"
    )

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
            for chunk in get_all_chunks(document_id, user_id):
                update_chunk_metadata(chunk['id'], user_id, document_id, title=title)

        if authors:
            existing_document['authors'] = authors
            for chunk in get_all_chunks(document_id, user_id):
                update_chunk_metadata(chunk['id'], user_id, document_id, author=authors)

        if abstract:
            existing_document['abstract'] = abstract

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
            for chunk in get_all_chunks(document_id, user_id):
                update_chunk_metadata(chunk['id'], user_id, document_id, file_name=file_name)

        if percentage_complete:
            existing_document['percentage_complete'] = percentage_complete

        if publication_date:
            existing_document['publication_date'] = publication_date

        if number_of_file_chunks:
            existing_document['number_of_file_chunks'] = number_of_file_chunks

        if current_page:
            existing_document['current_page'] = current_page

        if current_file_chunk:
            existing_document['current_file_chunk'] = current_file_chunk

        if enhanced_citations:
            existing_document['enhanced_citations'] = enhanced_citations

        if organization:
            existing_document['organization'] = organization
        
        add_file_task_to_file_processing_log(
            document_id, 
            user_id, 
            f"Attempting to update document {document_id} with document_classification: {document_classification}"
        )

        if document_classification:
            add_file_task_to_file_processing_log(
                document_id, 
                user_id, 
                f"Updating document classification for document {document_id} to {document_classification}"
            )
            existing_document['document_classification'] = document_classification
            for chunk in get_all_chunks(document_id, user_id):
                update_chunk_metadata(chunk['id'], user_id, document_id, document_classification=document_classification)


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
            "document_classification": "TBD",
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

def get_all_chunks(document_id, user_id):
    try:
        search_client_user = CLIENTS["search_client_user"]
        results = search_client_user.search(
            search_text="*",
            filter=f"document_id eq '{document_id}' and user_id eq '{user_id}'",
            select=["id", "chunk_text", "chunk_id", "file_name", "user_id", "version", "chunk_sequence", "upload_date"]
        )
        return results
    except Exception as e:
        print(f"Error retrieving chunks for document {document_id}: {e}")
        raise

def update_chunk_metadata(chunk_id, user_id, document_id, **kwargs):
    try:
        search_client_user = CLIENTS["search_client_user"]
        chunk_item = search_client_user.get_document(chunk_id)

        if not chunk_item:
            raise Exception("Chunk not found")
        
        if chunk_item['user_id'] != user_id:
            raise Exception("Unauthorized access to chunk")
        
        if chunk_item['document_id'] != document_id:
            raise Exception("Chunk does not belong to document")
        
        if 'chunk_keywords' in kwargs:
            chunk_item['chunk_keywords'] = kwargs['chunk_keywords']

        if 'chunk_summary' in kwargs:
            chunk_item['chunk_summary'] = kwargs['chunk_summary']

        if 'author' in kwargs:
            chunk_item['author'] = kwargs['author']

        if 'title' in kwargs:
            chunk_item['title'] = kwargs['title']

        if 'document_classification' in kwargs:
            chunk_item['document_classification'] = kwargs['document_classification']

        search_client_user.upload_documents(documents=[chunk_item])
    except Exception as e:
        print(f"Error updating chunk metadata for chunk {chunk_id}: {e}")
        raise

def get_pdf_page_count(pdf_path: str) -> int:
    """
    Returns the total number of pages in the given PDF using PyMuPDF.
    """
    try:
        with fitz.open(pdf_path) as doc:
            return doc.page_count
    except Exception as e:
        print(f"Error reading PDF page count: {e}")
        return 0

def chunk_pdf(input_pdf_path: str, max_pages: int = 500) -> list:
    """
    Splits a PDF into multiple PDFs, each with up to `max_pages` pages,
    using PyMuPDF. Returns a list of file paths for the newly created chunks.
    """
    chunks = []
    try:
        with fitz.open(input_pdf_path) as doc:
            total_pages = doc.page_count
            current_page = 0
            chunk_index = 1
            
            base_name, ext = os.path.splitext(input_pdf_path)
            
            # Loop through the PDF in increments of `max_pages`
            while current_page < total_pages:
                end_page = min(current_page + max_pages, total_pages)
                
                # Create a new, empty document for this chunk
                chunk_doc = fitz.open()
                
                # Insert the range of pages in one go
                chunk_doc.insert_pdf(doc, from_page=current_page, to_page=end_page - 1)
                
                chunk_pdf_path = f"{base_name}_chunk_{chunk_index}{ext}"
                chunk_doc.save(chunk_pdf_path)
                chunk_doc.close()
                
                chunks.append(chunk_pdf_path)
                
                current_page = end_page
                chunk_index += 1

    except Exception as e:
        print(f"Error chunking PDF: {e}")

    return chunks

def get_user_documents(user_id):
    try:
        query = """
            SELECT *
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

def delete_user_document(user_id, document_id):
    """
    Delete a document from the user's documents in Cosmos DB
    and remove any associated blobs in storage whose metadata
    matches the user_id and document_id.
    """
    try:
        # 1. Verify the document is owned by this user
        document_item = documents_container.read_item(
            item=document_id,
            partition_key=document_id
        )
        if document_item.get('user_id') != user_id:
            raise Exception("Unauthorized access to document")

        # 2. Delete from Cosmos DB
        documents_container.delete_item(
            item=document_id,
            partition_key=document_id
        )

        # 3. Delete matching blobs from Azure Storage
        blob_service_client = CLIENTS.get("office_docs_client")
        container_client = blob_service_client.get_container_client(
            user_documents_container_name
        )

        # List only blobs in "user_id/" prefix:
        prefix = f"{user_id}/"
        blob_list = container_client.list_blobs(name_starts_with=prefix)

        for blob_item in blob_list:
            # We need to retrieve the blob’s metadata to check document_id
            blob_client = container_client.get_blob_client(blob_item.name)
            properties = blob_client.get_blob_properties()
            blob_metadata = properties.metadata or {}

            # Compare metadata for user_id and document_id
            if (
                blob_metadata.get('user_id') == str(user_id)
                and blob_metadata.get('document_id') == str(document_id)
            ):
                # This blob belongs to the same doc & user => Delete
                container_client.delete_blob(blob_item.name)

        return {"message": "Document and associated blobs deleted successfully."}

    except CosmosResourceNotFoundError:
        raise Exception("Document not found")
    except Exception as e:
        # You can raise or return a custom JSON error
        raise Exception(f"Error during delete: {str(e)}")



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
            return "personal", doc_item['user_id']
    except:
        pass

    try:
        group_doc_item = group_documents_container.read_item(document_id, partition_key=document_id)
        return "group", group_doc_item['group_id']
    except:
        pass

    return None

def extract_document_metadata(document_id, user_id):

    settings = get_settings()
    enable_gpt_apim = settings.get('enable_gpt_apim', False)
    enable_user_workspace = settings.get('enable_user_workspace', False)
    enable_group_workspaces = settings.get('enable_group_workspaces', False)

    add_file_task_to_file_processing_log(
        document_id, 
        user_id, 
        f"Querying metadata for document {document_id} and user {user_id}"
    )
    
    # Example structure for reference
    meta_data_example = {
        "title": "Title here",
        "authors": ["Author 1", "Author 2"],
        "organization": "Organization or Unknown",
        "publication_date": "MM/YYYY or N/A",
        "keywords": ["keyword1", "keyword2"],
        "abstract": "two sentence abstract"
    }
    
    # Pre-initialize metadata dictionary
    meta_data = {
        "title": "",
        "authors": [],
        "organization": "",
        "publication_date": "",
        "keywords": [],
        "abstract": ""
    }

    # --- Step 1: Retrieve document from Cosmos ---
    try:
        query = """
            SELECT *
            FROM c
            WHERE c.id = @document_id AND c.user_id = @user_id
        """
        parameters = [
            {"name": "@document_id", "value": document_id},
            {"name": "@user_id", "value": user_id}
        ]
        document_items = list(documents_container.query_items(
            query=query, 
            parameters=parameters, 
            enable_cross_partition_query=True
        ))

        add_file_task_to_file_processing_log(
            document_id, 
            user_id, 
            f"Retrieved document items for document {document_id}: {document_items}"
        )
    
    except Exception as e:
        add_file_task_to_file_processing_log(
            document_id, 
            user_id, 
            f"Error querying document items for document {document_id}: {e}"
        )
        print(f"Error querying document items for document {document_id}: {e}")

    if not document_items:
        return None

    document_metadata = document_items[0]
    
    # --- Step 2: Populate meta_data from DB ---
    if "title" in document_metadata:
        meta_data["title"] = document_metadata["title"]
    if "authors" in document_metadata:
        meta_data["authors"] = document_metadata["authors"]
    if "organization" in document_metadata:
        meta_data["organization"] = document_metadata["organization"]
    if "publication_date" in document_metadata:
        meta_data["publication_date"] = document_metadata["publication_date"]
    if "keywords" in document_metadata:
        meta_data["keywords"] = document_metadata["keywords"]
    if "abstract" in document_metadata:
        meta_data["abstract"] = document_metadata["abstract"]

    add_file_task_to_file_processing_log(
        document_id, 
        user_id, 
        f"Extracted metadata for document {document_id}, metadata: {meta_data}"
    )

    # --- Step 3: Content Safety Check (if enabled) ---
    if settings.get('enable_content_safety') and "content_safety_client" in CLIENTS:
        content_safety_client = CLIENTS["content_safety_client"]
        blocked = False
        block_reasons = []
        triggered_categories = []
        blocklist_matches = []

        try:
            # For demonstration, we only check 'title'. 
            # Consider checking more fields if needed.
            request_obj = AnalyzeTextOptions(text=json.dumps(meta_data))
            cs_response = content_safety_client.analyze_text(request_obj)

            max_severity = 0
            for cat_result in cs_response.categories_analysis:
                triggered_categories.append({
                    "category": cat_result.category,
                    "severity": cat_result.severity
                })
                if cat_result.severity > max_severity:
                    max_severity = cat_result.severity

            if cs_response.blocklists_match:
                for match in cs_response.blocklists_match:
                    blocklist_matches.append({
                        "blocklistName": match.blocklist_name,
                        "blocklistItemId": match.blocklist_item_id,
                        "blocklistItemText": match.blocklist_item_text
                    })

            if max_severity >= 4:
                blocked = True
                block_reasons.append("Max severity >= 4")
            if blocklist_matches:
                blocked = True
                block_reasons.append("Blocklist match")
            
            if blocked:
                add_file_task_to_file_processing_log(
                    document_id, 
                    user_id, 
                    f"Blocked document metadata: {document_metadata}, reasons: {block_reasons}"
                )
                # Log or handle blocked content
                print(f"Blocked document metadata: {document_metadata}\nReasons: {block_reasons}")
                return None

        except Exception as e:
            add_file_task_to_file_processing_log(
                document_id, 
                user_id, 
                f"Error checking content safety for document metadata: {e}"
            )
            print(f"Error checking content safety for document metadata: {e}")

    # --- Step 4: Optional Bing Search ---
    try:
        if enable_user_workspace or enable_group_workspaces:
            add_file_task_to_file_processing_log(
                document_id, 
                user_id, 
                f"Processing Hybrid search for document {document_id} using json dump of metadata {json.dumps(meta_data)}"
            )

            document_scope, id = detect_doc_type(document_id, user_id)
            if document_scope == "personal":
                search_results = hybrid_search(json.dumps(meta_data), user_id, document_id=document_id, top_n=10, doc_scope=document_scope)
            elif document_scope == "group":
                search_results = hybrid_search(json.dumps(meta_data), user_id, document_id=document_id, top_n=10, doc_scope=document_scope, active_group_id=id)
            add_file_task_to_file_processing_log(
                document_id, 
                user_id, 
                f"Hybrid search results for document {document_id}: {search_results}"
            )
        else:
            search_results = "No Hybrid results"
    except Exception as e:
        add_file_task_to_file_processing_log(
            document_id, 
            user_id, 
            f"Error processing Bing search for document {document_id}: {e}"
        )
        print(f"Error processing Bing search for document {document_id}: {e}")
        bing_results = "No Bing results"

    # --- Step 5: Prepare GPT Client ---
    if enable_gpt_apim:
        # Apim-based GPT client
        gpt_model = settings.get('azure_apim_gpt_deployment')
        gpt_client = AzureOpenAI(
            api_version=settings.get('azure_apim_gpt_api_version'),
            azure_endpoint=settings.get('azure_apim_gpt_endpoint'),
            api_key=settings.get('azure_apim_gpt_subscription_key')
        )
    else:
        # Standard Azure OpenAI approach
        if settings.get('azure_openai_gpt_authentication_type') == 'managed_identity':
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), 
                "https://cognitiveservices.azure.com/.default"
            )
            gpt_client = AzureOpenAI(
                api_version=settings.get('azure_openai_gpt_api_version'),
                azure_endpoint=settings.get('azure_openai_gpt_endpoint'),
                azure_ad_token_provider=token_provider
            )
        else:
            gpt_client = AzureOpenAI(
                api_version=settings.get('azure_openai_gpt_api_version'),
                azure_endpoint=settings.get('azure_openai_gpt_endpoint'),
                api_key=settings.get('azure_openai_gpt_key')
            )

        # Retrieve the selected deployment name if provided
        gpt_model_obj = settings.get('gpt_model', {})
        if gpt_model_obj and gpt_model_obj.get('selected'):
            selected_gpt_model = gpt_model_obj['selected'][0]
            gpt_model = selected_gpt_model['deploymentName']


    # --- Step 6: GPT Prompt and JSON Parsing ---
    # Construct messages in the recommended chat format
    try:
        add_file_task_to_file_processing_log(
            document_id, 
            user_id,
            f"Processing GPT request for document {document_id}"
        )
        messages = [
            {"role": "system", "content": "You are an AI assistant that extracts metadata. Return valid JSON."},
            {
                "role": "user", 
                "content": (
                f"Search results from AI search index:\n{search_results}\n\n"
                f"Current known metadata:\n{json.dumps(meta_data, indent=2)}\n\n"
                f"Desired metadata structure:\n{json.dumps(meta_data_example, indent=2)}\n\n"
                "Please fill in any missing values. Return only JSON."
                )
            }
        ]

        response = gpt_client.chat.completions.create(model=gpt_model, messages=messages)
        
    except Exception as e:
        add_file_task_to_file_processing_log(
            document_id, 
            user_id, 
            f"Error processing GPT request for document {document_id}: {e}"
        )
        print(f"Error processing GPT request for document {document_id}: {e}")
        return meta_data
    
    if not response:
        return meta_data  # or None, depending on your logic

    response_content = response.choices[0].message.content
    add_file_task_to_file_processing_log(
        document_id, 
        user_id, 
        f"GPT response for document {document_id}: {response_content}"
    )
    try:
        add_file_task_to_file_processing_log(
            document_id, 
            user_id,
            f"Decoding JSON from response for document {document_id}"
        )
        cleaned_output = clean_json_codeFence(response_content)
        response_json = json.loads(cleaned_output)  
    except json.JSONDecodeError as e:
        add_file_task_to_file_processing_log(
            document_id, 
            user_id,   
            f"Error decoding JSON from response for document {document_id}: {e}"
        )
        print(f"Error decoding JSON from response: {e}")
        return meta_data  # or None

    # --- Step 7: Merge GPT Output with Existing Metadata ---
    meta_data["title"] = meta_data["title"] or response_json.get("title", "Unknown")
    meta_data["authors"] = meta_data["authors"] or response_json.get("authors", []) or [meta_data["organization"]] or ["Unknown"]
    meta_data["organization"] = meta_data["organization"] or response_json.get("organization", "Unknown")
    meta_data["publication_date"] = meta_data["publication_date"] or response_json.get("publication_date", "Unknown")
    meta_data["keywords"] = meta_data["keywords"] or response_json.get("keywords", [])
    meta_data["abstract"] = meta_data["abstract"] or response_json.get("abstract", "")

    add_file_task_to_file_processing_log(
        document_id, 
        user_id, 
        f"Final metadata for document {document_id}: {meta_data}"
    )

    return meta_data

def clean_json_codeFence(response_content: str) -> str:
    """
    Removes leading and trailing triple-backticks or code fences from a string 
    so that it can be parsed as JSON.
    """
    # This regex looks for ``` or ```json followed by optional whitespace/newlines, 
    # and removes them, as well as trailing ``` on its own line.
    cleaned = re.sub(r"^```(?:json)?\s*", "", response_content.strip(), flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE)
    return cleaned.strip()

def process_document_upload_background(document_id, user_id, temp_file_path, original_filename):
    """
    Runs in a background thread via Flask-Executor.
    Chunk the file, call Azure DI, upsert each page into Search, update doc status in Cosmos, etc.
    """
    settings = get_settings()
    enable_enhanced_citations = settings.get('enable_enhanced_citations')
    enable_extract_meta_data = settings.get('enable_extract_meta_data')
    max_file_size_bytes = settings.get('max_file_size_mb', 16) * 1024 * 1024
    di_limit_bytes = 500 * 1024 * 1024
    di_page_limit = 2000

    file_ext = os.path.splitext(original_filename)[-1].lower()

    # We'll read metadata from the temp file (for PDF, docx, etc.)
    doc_title = ''
    doc_author = ''
    doc_subject = None
    doc_keywords = None

    try:
        # Attempt to get some metadata if it's one of our known doc types
        if file_ext in [
            '.pdf', '.docx', '.doc', '.xlsx', '.pptx',
            '.html', '.jpg', '.jpeg', '.png', '.bmp',
            '.tiff', '.tif', '.heif'
        ]:
            # extract metadata
            if file_ext == '.pdf':
                doc_title, doc_author, doc_subject, doc_keywords = extract_pdf_metadata(temp_file_path)
                doc_authors_list = parse_authors(doc_author)

            elif file_ext in ('.docx', '.doc'):
                doc_title, doc_author = extract_docx_metadata(temp_file_path)
                doc_authors_list = parse_authors(doc_author)

            # Retrieve file size, (optionally) page count
            page_count = 0
            file_size = os.path.getsize(temp_file_path)
            if file_ext == '.pdf':
                page_count = get_pdf_page_count(temp_file_path)

            # Update cosmos doc with known metadata
            if doc_title:
                update_document(
                    document_id=document_id,
                    user_id=user_id,
                    title=doc_title
                )
            if doc_author:
                update_document(
                    document_id=document_id,
                    user_id=user_id,
                    authors=doc_author
                )
            if doc_subject:
                update_document(
                    document_id=document_id,
                    user_id=user_id,
                    abstract=doc_subject
                )
            if doc_keywords:
                update_document(
                    document_id=document_id,
                    user_id=user_id,
                    keywords=doc_keywords
                )

            # ---------------------------
            # Check Enhanced Citations?
            # ---------------------------
            if not enable_enhanced_citations:
                # Non-enhanced mode: must be <= 500MB, <= 2000 pages, and <= max_file_size_bytes
                if (file_size > di_limit_bytes or 
                    page_count > di_page_limit or 
                    file_size > max_file_size_bytes):
                    # Not supported in non-enhanced mode
                    update_document(
                        document_id=document_id,
                        user_id=user_id,
                        status="Error: File exceeds non-enhanced citations limits."
                    )
                    # Cleanup temp file
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    return jsonify({
                        'error': (
                            f'File exceeds non-enhanced citations limits '
                            f'(max {di_limit_bytes} bytes / {di_page_limit} pages / {max_file_size_bytes} bytes).'
                        )
                    }), 400

                # No chunking for non-enhanced mode
                file_paths_to_process = [temp_file_path]

            else:
                # Enhanced citations
                update_document(
                    document_id=document_id,
                    user_id=user_id,
                    enhanced_citations=True
                )

                # Still reject if file is bigger than your max or the pages are too high
                if file_size > max_file_size_bytes:
                    update_document(
                        document_id=document_id,
                        user_id=user_id,
                        status="Error: File exceeds maximum size in enhanced mode."
                    )
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    return jsonify({
                        'error': f'File exceeds maximum size of {max_file_size_bytes} bytes in enhanced mode.'
                    }), 400

                # If the file is <= 500MB and <= 2000 pages => no chunk
                if file_size <= di_limit_bytes and page_count <= di_page_limit:
                    file_paths_to_process = [temp_file_path]
                else:
                    # If bigger than 500MB or more than 2000 pages => chunk it (PDF only)
                    if file_ext == '.pdf':
                        file_paths_to_process = chunk_pdf(temp_file_path, max_pages=500)
                        # Clean up the original big PDF if chunking was successful
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                    else:
                        update_document(
                            document_id=document_id,
                            user_id=user_id,
                            status="Error: Only PDF chunking is supported."
                        )
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                        return jsonify({
                            'error': 'Only PDF chunking is supported in this scenario.'
                        }), 400

            # Update doc with chunk count
            num_file_chunks = len(file_paths_to_process)
            update_document(
                document_id=document_id,
                user_id=user_id,
                num_file_chunks=num_file_chunks,
                status=f"Processing {original_filename} with {num_file_chunks} chunk(s)"
            )

            # -----------------------------------
            # Process each chunk (or single file)
            # -----------------------------------
            for idx, chunk_path in enumerate(file_paths_to_process, start=1):
                update_document(
                    document_id=document_id,
                    user_id=user_id,
                    status=f"Processing file chunk {idx} of {num_file_chunks}"
                )

                # Build chunk-based doc ID if multiple chunks
                if num_file_chunks > 1:
                    chunk_document_id = f"{document_id}-chunk-{idx}"
                else:
                    chunk_document_id = document_id

                # Decide a chunk filename that includes original name + index
                base_name, ext = os.path.splitext(original_filename)
                if num_file_chunks > 1:
                    # e.g. "mydoc_chunk_1.pdf"
                    chunk_filename = f"{base_name}_chunk_{idx}{ext}"
                else:
                    chunk_filename = original_filename

                # -------------------------------------------------
                # If enhanced_citations, we also upload to Blob
                # -------------------------------------------------
                if enable_enhanced_citations:
                    try:
                        blob_path = f"{user_id}/{chunk_filename}"
                        blob_service_client = CLIENTS.get("office_docs_client")
                        blob_client = blob_service_client.get_blob_client(
                            container=user_documents_container_name,
                            blob=blob_path
                        )
                        # Add metadata fields for user_id and document_id
                        blob_metadata = {
                            "user_id": str(user_id),
                            "document_id": str(document_id)
                        }
                        with open(chunk_path, "rb") as f:
                            blob_client.upload_blob(f, overwrite=True, metadata=blob_metadata)
                    except Exception as e:
                        update_document(
                            document_id=document_id,
                            user_id=user_id,
                            status=(
                                f"Error uploading {chunk_filename} to Blob Storage: {str(e)}"
                            )
                        )
                        if os.path.exists(chunk_path):
                            os.remove(chunk_path)
                        return jsonify({
                            'error': f'Error uploading chunk {chunk_filename} to Blob Storage: {str(e)}'
                        }), 500

                # ----------------------
                # Send chunk to Azure DI
                # ----------------------
                update_document(
                    document_id=document_id,
                    user_id=user_id,
                    status=f"Sending {chunk_filename} (chunk {idx} of {num_file_chunks}) to Azure Document Intelligence"
                )

                try:
                    pages = extract_content_with_azure_di(chunk_path)
                    update_document(
                        document_id=document_id,
                        user_id=user_id,
                        number_of_pages=len(pages),
                        status=f"Extracted content from {chunk_filename}."
                    )
                except Exception as e:
                    update_document(
                        document_id=document_id,
                        user_id=user_id,
                        status=f"Error extracting content from {chunk_filename}: {str(e)}"
                    )
                    if os.path.exists(chunk_path):
                        os.remove(chunk_path)
                    return jsonify({'error': f'Error extracting file: {str(e)}'}), 500

                # ---------------------------------------------
                # Save each page’s text content as a “chunk”
                # ---------------------------------------------
                try:
                    for page_data in pages:
                        page_number = page_data["page_number"]
                        page_content = page_data["content"]
                        update_document(
                            document_id=document_id,
                            user_id=user_id,
                            status=f"Saving page {page_number} of {chunk_filename}..."
                        )

                        save_chunks(
                            page_text_content=page_content,
                            page_number=page_number,
                            file_name=chunk_filename,
                            user_id=user_id,
                            document_id=chunk_document_id
                        )

                    update_document(
                        document_id=document_id,
                        user_id=user_id,
                        status=f"Saved extracted content from {chunk_filename}."
                    )
                except Exception as e:
                    update_document(
                        document_id=document_id,
                        user_id=user_id,
                        status=f"Error saving extracted content from {chunk_filename}: {str(e)}"
                    )
                    if os.path.exists(chunk_path):
                        os.remove(chunk_path)
                    return jsonify({'error': f'Error saving extracted content: {str(e)}'}), 500

                # Clean up local chunk file if not the same as original temp_file
                if chunk_path != temp_file_path and os.path.exists(chunk_path):
                    os.remove(chunk_path)

            # If metadata extraction is enabled
            if enable_extract_meta_data:
                try:
                    update_document(
                        document_id=document_id,
                        user_id=user_id,
                        status="Extracting final metadata..."
                    )
                    document_metadata = extract_document_metadata(document_id, user_id)

                    update_document(
                        document_id=document_id,
                        user_id=user_id,
                        title=document_metadata.get('title'),
                        authors=document_metadata.get('authors'),
                        abstract=document_metadata.get('abstract'),
                        keywords=document_metadata.get('keywords'),
                        publication_date=document_metadata.get('publication_date'),
                        organization=document_metadata.get('organization'),
                    )
                except Exception as e:
                    update_document(
                        document_id=document_id,
                        user_id=user_id,
                        status=f"Error extracting metadata: {str(e)}"
                    )
                    # Not critical enough to return error necessarily, do as you prefer.

            # Mark the entire doc as complete
            update_document(
                document_id=document_id,
                user_id=user_id,
                status="Processing complete",
                percentage_complete=100
            )

            # Finally, remove the original temp file if it still exists
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

            return jsonify({'message': 'Document uploaded and processed successfully'}), 200

        # -------------------------------------------------------
        # If it’s a .txt, .md, or .json, handle them differently
        # -------------------------------------------------------
        elif file_ext == '.txt':
            extracted_content = extract_text_file(temp_file_path)
            save_chunks(extracted_content, original_filename, user_id, document_id=document_id)
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return jsonify({'message': 'TXT file processed successfully'}), 200

        elif file_ext == '.md':
            extracted_content = extract_markdown_file(temp_file_path)
            save_chunks(extracted_content, original_filename, user_id, document_id=document_id)
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return jsonify({'message': 'MD file processed successfully'}), 200

        elif file_ext == '.json':
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                extracted_content = json.dumps(json.load(f))
            save_chunks(extracted_content, original_filename, user_id, document_id=document_id)
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return jsonify({'message': 'JSON file processed successfully'}), 200

        else:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            return jsonify({'error': 'Unsupported file type'}), 400

    except Exception as e:
        # In case of any unexpected error
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        update_document(
            document_id=document_id,
            user_id=user_id,
            status=f"Processing failed: {str(e)}"
        )
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

