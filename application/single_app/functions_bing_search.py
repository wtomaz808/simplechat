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

def query_llm_with_chat(original_query, search_results):
    try:
        # Format the search results as a context string
        context = "\n".join([f"- {result['name']}: {result['snippet']} (URL: {result['url']})" for result in search_results])
        
        # Define the messages for the chat
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an assistant that answers factual questions based on provided search results. "
                    "Ensure you include the source URLs in your response for transparency.  Source URLs should be rendered to open in a new browser window."
                ),
            },
            {"role": "user", "content": f"User Query: {original_query}"},
            {"role": "assistant", "content": f"Search Results:\n{context}"},
            {
                "role": "user",
                "content": "Based on the search results, answer the user's query and reference the sources in your response. Please make sure that links to references open in a new browser window.",
            },
        ]
        
        # Send the request to the OpenAI ChatCompletion endpoint
        response = openai.ChatCompletion.create(
            engine="gpt-4o",  # Replace with the desired model, e.g., "gpt-4" or "gpt-3.5-turbo"
            messages=messages,
        )
        
        # Extract and return the assistant's response
        return response.choices[0].message["content"].strip()
    except openai.error.InvalidRequestError as e:
        print(f"InvalidRequestError: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return "An error occurred while processing your request."

# Function to generate LLM response
def query_llm(original_query, search_results):
    context = "\n".join([f"- {result['name']}: {result['snippet']} (URL: {result['url']})" for result in search_results])
    prompt = (
        f"User Query: {original_query}\n"
        f"Search Results:\n{context}\n\n"
        "Based on the search results, answer the user's query:"
    )
    response = openai.Completion.create(engine="gpt-4o", param='', prompt=prompt, max_tokens=200)
    return response.choices[0].text.strip()

# Main Workflow
def process_query_with_bing_and_llm(user_query):
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
    llm_response = query_llm_with_chat(user_query, search_results)
    print(f"LLM Response: {llm_response}")

    return llm_response