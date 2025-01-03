from config import *

def get_suggestions(query):
    autosuggest_url = f"{BING_SEARCH_ENDPOINT}/v7.0/suggestions"
    headers = {"Ocp-Apim-Subscription-Key": BING_SEARCH_KEY}
    params = {"q": query}
    response = requests.get(autosuggest_url, headers=headers, params=params)
    response.raise_for_status()
    suggestions = response.json()["suggestionGroups"][0]["searchSuggestions"]
    return [s["displayText"] for s in suggestions]

# Function to call Bing Search API
def get_search_results(query, top_n=5):
    search_url = f"{BING_SEARCH_ENDPOINT}/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": BING_SEARCH_KEY}
    params = {"q": query, "count": top_n}
    response = requests.get(search_url, headers=headers, params=params)
    response.raise_for_status()
    results = response.json().get("webPages", {}).get("value", [])
    return [{"name": r["name"], "url": r["url"], "snippet": r["snippet"]} for r in results]

def query_llm_with_chat(original_query, search_results,tmodel):
    try:
        # Format the search results as a context string
        context = "\n".join([f"- {result['name']}: {result['snippet']} (URL: {result['url']})" for result in search_results])
        
        # Define the messages for the chat
        messages = [
            # {
            #     "role": "system",
            #     "content": (
            #         "You are an assistant that answers factual questions based on provided search results. "
            #         "Ensure you include the source URLs in your response for transparency."
            #     ),
            # },
            {"role": "user", "content": f"User Query: {original_query}"},
            {"role": "assistant", "content": f"Search Results:\n{context}"},
            {
                "role": "user",
                "content": "Based on the search results, answer the user's query and reference the sources in your response. References should following the following syntax/template substituting details for the reference url and page title <a target='_blank' href='reference url' rel='noopener noreferrer'>page title</a>",
            },
        ]
        
        # Send the request to the OpenAI ChatCompletion endpoint
        response = openai.ChatCompletion.create(
            engine=tmodel,  # Replace with the desired model, e.g., "gpt-4" or "gpt-3.5-turbo"
            messages=messages,
        )
        
        # Extract and return the assistant's response
        return response.choices[0].message["content"].strip()
    except openai.error.InvalidRequestError as e:
        print(f"InvalidRequestError: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return "An error occurred while processing your request."


# Main Workflow
def process_query_with_bing_and_llm(user_query,tmodel):
    # Step 1: Use Autosuggest to refine the query
    print(f"Original Query: {user_query}")
    suggestions = get_suggestions(user_query)
    if suggestions:
        refined_query = suggestions[0]  # Use the top suggestion
        print(f"Refined Query (from Autosuggest): {refined_query}")
    else:
        refined_query = user_query
        print("No suggestions available. Using the original query.")

    # Step 2: Use Bing Search API to get top 5 results
    search_results = get_search_results(refined_query, top_n=5)
    print(f"Search Results: {search_results}")

    # Step 3: Pass results and query to LLM
    print(f"about to call LLM")
    llm_response = query_llm_with_chat(user_query, search_results,tmodel)
    print(f"LLM Response: {llm_response}")

    return llm_response