# functions_search.py

from config import *
from functions_content import *
from functions_documents import *

def hybrid_search(query, user_id, document_id=None, top_n=3, doc_scope="all", active_group_id=None):
    """
    Hybrid search that queries the user doc index or the group doc index
    depending on doc type.
    If document_id is None, we just search the user index for the user's docs
    OR you could unify that logic further (maybe search both).
    """
    query_embedding = generate_embedding(query)
    if query_embedding is None:
        return None
    
    search_client_user = CLIENTS['search_client_user']
    search_client_group = CLIENTS['search_client_group']

    vector_query = VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=top_n,
        fields="embedding"
    )

    if doc_scope == "all":
        if document_id:
            # Search user documents
            user_results = search_client_user.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=f"user_id eq '{user_id}' and document_id eq '{document_id}'",
                select=["id", "chunk_text", "chunk_id", "file_name", "user_id", "version", "chunk_sequence", "upload_date"]
            )

            # Search group documents
            group_results = search_client_group.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=f"group_id eq '{active_group_id}' and document_id eq '{document_id}'",
                select=["id", "chunk_text", "chunk_id", "file_name", "group_id", "version", "chunk_sequence", "upload_date"]
            )
        else:
            # Search user documents
            user_results = search_client_user.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=f"user_id eq '{user_id}'",
                select=["id", "chunk_text", "chunk_id", "file_name", "user_id", "version", "chunk_sequence", "upload_date"]
            )

            # Search group documents
            group_results = search_client_group.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=f"group_id eq '{active_group_id}'",
                select=["id", "chunk_text", "chunk_id", "file_name", "group_id", "version", "chunk_sequence", "upload_date"]
            )

        # Combine results from both searches
        user_results_final = extract_search_results(user_results, top_n)
        group_results_final = extract_search_results(group_results, top_n)
        results = user_results_final + group_results_final
    
    elif doc_scope == "personal":
        if document_id:
            # Search user documents
            user_results = search_client_user.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=f"user_id eq '{user_id}' and document_id eq '{document_id}'",
                select=["id", "chunk_text", "chunk_id", "file_name", "user_id", "version", "chunk_sequence", "upload_date"]
            )
            results = extract_search_results(user_results, top_n)
        else:
            # Search user documents
            user_results = search_client_user.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=f"user_id eq '{user_id}'",
                select=["id", "chunk_text", "chunk_id", "file_name", "user_id", "version", "chunk_sequence", "upload_date"]
            )
            results = extract_search_results(user_results, top_n)

    elif doc_scope == "group":
        if document_id:
            # Search group documents
            group_results = search_client_group.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=f"group_id eq '{active_group_id}' and document_id eq '{document_id}'",
                select=["id", "chunk_text", "chunk_id", "file_name", "group_id", "version", "chunk_sequence", "upload_date"]
            )
            results = extract_search_results(group_results, top_n)
        else:
            # Search group documents
            group_results = search_client_group.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=f"group_id eq '{active_group_id}'",
                select=["id", "chunk_text", "chunk_id", "file_name", "group_id", "version", "chunk_sequence", "upload_date"]
            )
            results = extract_search_results(group_results, top_n)
    
    return results 

def extract_search_results(paged_results, top_n):
    extracted = []
    for i, r in enumerate(paged_results):
        if i >= top_n:
            break
        # Convert the raw result to a minimal dict you can serialize.
        extracted.append({
            "id": r["id"],
            "chunk_text": r["chunk_text"],
            "chunk_id": r["chunk_id"],
            "file_name": r["file_name"],
            "group_id": r.get("group_id"),
            "version": r["version"],
            "chunk_sequence": r["chunk_sequence"],
            "upload_date": r["upload_date"],
            "score": r["@search.score"]
        })
    return extracted