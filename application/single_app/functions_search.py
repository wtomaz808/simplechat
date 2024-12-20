from config import *
from functions_content import *

def hybrid_search(query, user_id, top_n=3):
    try:
        query_embedding = generate_embedding(query)

        if query_embedding is None:
            #print("Failed to generate query embedding.")
            return None

        vector_query = VectorizedQuery(vector=query_embedding, k_nearest_neighbors=top_n, fields="embedding")

        results = search_client_user.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=f"user_id eq '{user_id}'",
            select=["id", "chunk_text", "chunk_id", "file_name", "user_id", "version", "chunk_sequence", "upload_date"]
        )

        limited_results = []
        for i, result in enumerate(results):
            if i >= top_n:
                break
            limited_results.append(result)

        documents = [doc for doc in limited_results]
        #print(f"Hybrid search completed successfully with {len(documents)} results.")
        return documents

    except Exception as e:
        #print(f"Error during hybrid search: {str(e)}")
        return None