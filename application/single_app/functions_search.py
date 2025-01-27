# functions_search.py

from config import *
from functions_content import *
from functions_documents import *

def hybrid_search(query, user_id, document_id=None, top_n=3):
    """
    Hybrid search that queries the user doc index or the group doc index
    depending on doc type.
    If document_id is None, we just search the user index for the user's docs
    OR you could unify that logic further (maybe search both).
    """
    query_embedding = generate_embedding(query)
    if query_embedding is None:
        return None

    vector_query = VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=top_n,
        fields="embedding"
    )

    if not document_id:
        # If no doc selected, let's default to user docs with a filter user_id = ...
        results = search_client_user.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=f"user_id eq '{user_id}'",
            select=["id", "chunk_text", "chunk_id", "file_name", "user_id", "version", "chunk_sequence", "upload_date"]
        )
    else:
        # We need to detect doc type
        doc_type = detect_doc_type(document_id, user_id=user_id)

        if doc_type == "user":
            # search user docs index
            results = search_client_user.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=f"user_id eq '{user_id}' and document_id eq '{document_id}'",
                select=["id", "chunk_text", "chunk_id", "file_name", "user_id", "version", "chunk_sequence", "upload_date"]
            )
        elif doc_type == "group":
            # search group docs index
            # We might not strictly need group_id, 
            # but if you want to ensure the user can only search the group 
            # they're in, you'd need to check that in your chat logic or the detect code.
            results = search_client_group.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=f"document_id eq '{document_id}'",  # or also "group_id eq X"
                select=["id", "chunk_text", "chunk_id", "file_name", "group_id", "version", "chunk_sequence", "upload_date"]
            )
        else:
            # doc not found or mismatch user
            return None

    # Now collect top_n results
    final_results = []
    for i, r in enumerate(results):
        if i >= top_n:
            break
        final_results.append(r)
    return final_results