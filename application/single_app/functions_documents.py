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
        #print(f"System message added to conversation {conversation_id} successfully.")

    except Exception as e:
        #print(f"Error adding system message to conversation: {str(e)}")
        raise e
    
def process_document_and_store_chunks(extracted_content , file_name, user_id):
    settings = get_settings()
    use_external_apis = settings.get('use_external_apis')
    external_chunking_api = settings.get('external_chunking_api')
    external_embedding_api = settings.get('external_embedding_api')

    if use_external_apis:
        response = requests.post(f"{external_chunking_api}/chunk", json={'text': extracted_content })
        chunks = response.json().get('chunks', [])
    else:
        chunks = chunk_text(extracted_content )

    #print("Function process_document_and_store_chunks called")
    document_id = str(uuid.uuid4())
    #print(f"Generated document ID: {document_id}")
    
    chunks = chunk_text(extracted_content )
    #print(f"Total chunks created: {len(chunks)}")

    num_chunks = len(chunks)

    existing_document_query = """
        SELECT c.version 
        FROM c 
        WHERE c.file_name = @file_name AND c.user_id = @user_id
    """
    parameters = [{"name": "@file_name", "value": file_name}, {"name": "@user_id", "value": user_id}]
    #print(f"Querying existing document with parameters: {parameters}")
    
    existing_document = list(documents_container.query_items(query=existing_document_query, parameters=parameters, enable_cross_partition_query=True))
    #print(f"Existing document found: {existing_document}")

    if existing_document:
        version = existing_document[0]['version'] + 1
        #print(f"New version determined: {version} (existing document found)")
    else:
        version = 1
        #print(f"New version determined: {version} (no existing document)")

    current_time = datetime.now(timezone.utc)

    formatted_time = current_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    document_metadata = {
        "id": document_id,
        "num_chunks": num_chunks,
        "file_name": file_name,
        "user_id": user_id,
        "upload_date": formatted_time,
        "version": version,
        "type": "document_metadata"
    }
    #print(f"Document metadata to be upserted: {document_metadata}")
    documents_container.upsert_item(document_metadata)
    #print("Document metadata upserted successfully.")

    chunk_documents = []

    for idx, chunk_text_content in enumerate(chunks):
        chunk_id = f"{document_id}_{idx}"
        #print(f"Processing chunk {idx} with ID: {chunk_id}")

        if use_external_apis:
            response = requests.post(f"{external_embedding_api}/embed", json={'text': chunk_text_content})
            embedding = response.json().get('embedding')
        else:
            embedding = generate_embedding(chunk_text_content)
        #print(f"Generated embedding for chunk {idx}")

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
        #print(f"Chunk document created for chunk {idx}: {chunk_document}")
        chunk_documents.append(chunk_document)

    #print(f"Uploading {len(chunk_documents)} chunk documents to Azure Cognitive Search")
    search_client_user.upload_documents(documents=chunk_documents)
    #print("Chunks uploaded successfully")

def get_user_documents(user_id):
    try:
        query = """
            SELECT c.file_name, c.id, c.upload_date, c.user_id, c.num_chunks ,c.version
            FROM c
            WHERE c.user_id = @user_id
        """
        parameters = [{"name": "@user_id", "value": user_id}]
        
        documents = list(documents_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        #print(f"Retrieved {len(documents)} documents for user {user_id}.")

        latest_documents = {}

        for doc in documents:
            file_name = doc['file_name']
            if file_name not in latest_documents or doc['version'] > latest_documents[file_name]['version']:
                latest_documents[file_name] = doc
                
        #print("Successfully processed user documents.")
        return jsonify({"documents": list(latest_documents.values())}), 200
    except Exception as e:
        #print(f"Error retrieving documents: {str(e)}")
        return jsonify({'error': f'Error retrieving documents: {str(e)}'}), 500

def get_user_document(user_id, document_id):
    #print(f"Function get_user_document called for user_id: {user_id}, document_id: {document_id}")

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
        #print(f"Query parameters: {parameters}")

        document_results = list(documents_container.query_items(
            query=latest_version_query, 
            parameters=parameters, 
            enable_cross_partition_query=True
        ))

        #print(f"Query executed, document_results: {document_results}")

        if not document_results:
            #print("Document not found or access denied")
            return jsonify({'error': 'Document not found or access denied'}), 404

        #print(f"Returning latest version of document: {document_results[0]}")
        return jsonify(document_results[0]), 200  # Return the latest version of the document

    except Exception as e:
        #print(f"Error retrieving document: {str(e)}")
        return jsonify({'error': f'Error retrieving document: {str(e)}'}), 500

def get_latest_version(document_id, user_id):
    #print(f"Function get_latest_version called for document_id: {document_id}, user_id: {user_id}")

    query = """
        SELECT c.version
        FROM c 
        WHERE c.id = @document_id AND c.user_id = @user_id
    """
    parameters = [
        {"name": "@document_id", "value": document_id},
        {"name": "@user_id", "value": user_id}
    ]
    #print(f"Query parameters: {parameters}")

    try:
        results = list(documents_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
        #print(f"Query results: {results}")

        if results:
            max_version = max(item['version'] for item in results)
            #print(f"Latest version found: {max_version}")
            return max_version
        else:
            #print("No version found for the document.")
            return None

    except Exception as e:
        #print(f"Error retrieving latest version: {str(e)}")
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
            #print("Document version not found.")
            return jsonify({'error': 'Document version not found'}), 404

        #print(f"Returning document version: {version}")
        return jsonify(document_results[0]), 200  # Return the specific version of the document

    except Exception as e:
        #print(f"Error retrieving document version: {str(e)}")
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
        #print(f"Document {document_id} deleted successfully.")
    except CosmosResourceNotFoundError:
        #print("Document not found.")
        raise Exception("Document not found")
    except Exception as e:
        #print(f"Error deleting document: {str(e)}")
        raise

def delete_user_document_chunks(document_id):
    """Delete document chunks from Azure Cognitive Search index."""
    try:
        results = search_client_user.search(
            search_text="*",
            filter=f"document_id eq '{document_id}'",
            select=["id"]
        )

        ids_to_delete = [doc['id'] for doc in results]

        if not ids_to_delete:
            #print(f"No chunks found for document_id: {document_id}")
            return

        documents_to_delete = [{"id": doc_id} for doc_id in ids_to_delete]

        batch = IndexDocumentsBatch()

        batch.add_delete_actions(documents_to_delete)

        result = search_client_user.index_documents(batch)
        #print(f"Document chunks for {document_id} deleted successfully.")
    except Exception as e:
        #print(f"Error deleting document chunks: {str(e)}")
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
        #print(f"Deleted document version {version} for document_id {document_id}.")

def delete_user_document_version_chunks(document_id, version):
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
    #print(f"Deleted chunks for document_id {document_id}, version {version}.")

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
            #print("No versions found for the document.")
            return []
        #print(f"Retrieved {len(versions_results)} versions for document {document_id}.")
        return versions_results

    except Exception as e:
        #print(f'Error retrieving document versions: {str(e)}')
        return []
    
def detect_doc_type(document_id, user_id=None):
    """
    Check Cosmos to see if this doc belongs to the user's docs (has user_id)
    or the group's docs (has group_id).
    Returns one of: "user", "group", or None if not found.
    Optionally checks if user_id matches (for user docs).
    """

    # 1) Try user docs container
    try:
        # For user docs, the container is "documents_container"
        doc_item = documents_container.read_item(document_id, partition_key=document_id)
        # If found, confirm it belongs to this user_id if given
        if user_id and doc_item.get('user_id') != user_id:
            # doesn't match the user -> not a user doc for this user
            pass
        else:
            return "user"
    except:
        pass  # Not found in user docs

    # 2) Try group docs container
    try:
        group_doc_item = group_documents_container.read_item(document_id, partition_key=document_id)
        # If found, it must be a group doc
        return "group"
    except:
        pass

    # If not found in either container
    return None