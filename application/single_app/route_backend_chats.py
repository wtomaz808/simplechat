from config import *
from functions_authentication import *
from functions_search import *
from functions_bing_search import *
from functions_settings import *

def register_route_backend_chats(app):
    @app.route('/api/chat', methods=['POST'])
    @login_required
    def chat_api():
        settings = get_settings()
        data = request.get_json()
        user_id = get_current_user_id()
        if not user_id:
            #print("User not authenticated.")
            return jsonify({'error': 'User not authenticated'}), 401

        user_message = data['message']
        conversation_id = data.get('conversation_id')
        hybrid_search_enabled = data.get('hybrid_search')
        selected_document_id = data.get('selected_document_id')
        bing_search_enabled = data.get('bing_search')
        image_gen_enabled = data.get('image_generation')


        gpt_client = AzureOpenAI(
            api_version=settings.get('azure_openai_gpt_api_version'),
            azure_endpoint=settings.get('azure_openai_gpt_endpoint'),
            api_key=settings.get('azure_openai_gpt_key')
        )


        gpt_model = settings.get('gpt_model')


        image_gen_client = AzureOpenAI(
            api_version=settings.get('azure_openai_image_gen_api_version'),
            azure_endpoint=settings.get('azure_openai_image_gen_endpoint'),
            api_key=settings.get('azure_openai_image_gen_key')
        )


        image_gen_model = settings.get('image_gen_model')

        # Convert hybrid_search_enabled to boolean if necessary
        if isinstance(hybrid_search_enabled, str):
            hybrid_search_enabled = hybrid_search_enabled.lower() == 'true'

        # Convert bing_search_enabled to boolean if necessary
        if isinstance(bing_search_enabled, str):
            bing_search_enabled = bing_search_enabled.lower() == 'true'

        # Retrieve or create the conversation
        if not conversation_id:
            # Generate a new conversation ID
            conversation_id = str(uuid.uuid4())
            conversation_item = {
                'id': conversation_id,
                'user_id': user_id,
                'messages': [],
                'last_updated': datetime.utcnow().isoformat(),
                'title': 'New Conversation'
            }
            #print(f"Started new conversation {conversation_id}.")
        else:
            # Retrieve existing conversation
            try:
                conversation_item = container.read_item(
                    item=conversation_id,
                    partition_key=conversation_id
                )
                #print(f"Retrieved conversation {conversation_id}.")
            except CosmosResourceNotFoundError:
                # Start a new conversation if not found
                conversation_id = str(uuid.uuid4())
                conversation_item = {
                    'id': conversation_id,
                    'user_id': user_id,
                    'messages': [],
                    'last_updated': datetime.utcnow().isoformat(),
                    'title': 'New Conversation'
                }
                #print(f"Conversation {conversation_id} not found. Started new conversation.")
            except Exception as e:
                #print(f"Error retrieving conversation {conversation_id}: {str(e)}", exc_info=True)
                return jsonify({'error': 'An error occurred'}), 500

        # Append the new user message
        conversation_item['messages'].append({'role': 'user', 'content': user_message})

        # If first user message, set conversation title
        if conversation_item.get('title', 'New Conversation') == 'New Conversation':
            new_title = (user_message[:30] + '...') if len(user_message) > 30 else user_message
            conversation_item['title'] = new_title

        # Optionally, if we want a default system prompt at the start
        if len(conversation_item['messages']) == 1 and settings.get('default_system_prompt'):
            conversation_item['messages'].insert(
                0, {'role': 'system', 'content': settings.get('default_system_prompt')}
            )

        # If hybrid search is enabled, perform it and include the results
        if hybrid_search_enabled:
            if selected_document_id:
                search_results = hybrid_search(user_message, user_id, top_n=10, document_id=selected_document_id)
            else:
                search_results = hybrid_search(user_message, user_id, top_n=10)
            if search_results:
                retrieved_texts = []
                for doc in search_results:
                    chunk_text = doc['chunk_text']
                    file_name = doc['file_name']
                    version = doc['version']
                    chunk_sequence = doc['chunk_sequence']
                    page_number = doc.get('page_number') or chunk_sequence
                    citation_id = doc['id'] 
                    citation = f"(Source: {file_name}, Page: {page_number}) [#{citation_id}]"
                    retrieved_texts.append(f"{chunk_text}\n{citation}")
                
                retrieved_content = "\n\n".join(retrieved_texts)
                system_prompt = (
                    "You are an AI assistant provided with the following document excerpts and their sources.\n"
                    "When you answer the user's question, please cite the sources by including the citations provided after each excerpt.\n"
                    "Use the format (Source: filename, Page: page number) [#ID] for citations, where ID is the unique identifier provided.\n"
                    "Ensure your response is informative and includes citations using this format.\n\n"
                    "For example:\n"
                    "User: What is the policy on double dipping?\n"
                    "Assistant: The policy prohibits entities from using federal funds received through one program to apply for additional \n"
                    "funds through another program, commonly known as 'double dipping' (Source: PolicyDocument.pdf, Page: 12) [#123abc].\n\n"
                    f"{retrieved_content}"
                )
                conversation_item['messages'].append({
                    'role': 'system', 
                    'content': system_prompt
                })
                #print("System prompt with hybrid search results added to conversation.")

                container.upsert_item(body=conversation_item)

        # If Bing search is enabled, perform it and include the results
        if bing_search_enabled:
            bing_results = process_query_with_bing_and_llm(user_message)

            if bing_results:
                retrieved_texts = []
                for r in bing_results:
                    title = r["name"]
                    snippet = r["snippet"]
                    url = r["url"]
                    citation = f"(Source: {title}) [{url}]"
                    retrieved_texts.append(f"{snippet}\n{citation}")
                
                retrieved_content = "\n\n".join(retrieved_texts)
                system_prompt = (
                    "You are an AI assistant provided with the following web search results.\n"
                    "When you answer the user's question, cite the sources by including the citations:\n"
                    "Use the format (Source: page_title) [url].\n\n"
                    "For example:\n"
                    "User: What is the capital of France?\n"
                    "Assistant: The capital of France is Paris (Source: OfficialFrancePage) [https://url.com].\n\n"
                    f"{retrieved_content}"
                )
                conversation_item['messages'].append({
                    'role': 'system',
                    'content': system_prompt
                })
                container.upsert_item(body=conversation_item)

        if image_gen_enabled:
            try:
                image_response = image_gen_client.images.generate(
                    prompt=user_message,
                    n=1,
                    model=image_gen_model
                )
                generated_image_url = json.loads(image_response.model_dump_json())['data'][0]['url']

                # Append a special "image" message to the conversation
                conversation_item['messages'].append({
                    'role': 'image',  # Custom role
                    'content': generated_image_url,
                    'prompt': user_message,
                    'created_at': datetime.utcnow().isoformat(),
                })

                conversation_item['last_updated'] = datetime.utcnow().isoformat()
                container.upsert_item(body=conversation_item)

                return jsonify({
                    'reply': f"Here's your generated image: {generated_image_url}",
                    'image_url': generated_image_url,
                    'conversation_id': conversation_id,
                    'conversation_title': conversation_item['title']
                }), 200

            except Exception as e:
                return jsonify({'error': f'Image generation failed: {str(e)}'}), 500
            
        conversation_history_limit = settings.get('conversation_history_limit', 10)
        conversation_history = conversation_item['messages'][-conversation_history_limit:]

        allowed_roles = ['system', 'assistant', 'user', 'function', 'tool']
        conversation_history_for_api = []
        for msg in conversation_history:
            if msg['role'] in allowed_roles:
                conversation_history_for_api.append(msg)
            elif msg['role'] == 'file':
                # Modify 'file' messages to be 'system' messages
                file_content = msg.get('file_content', '')
                filename = msg.get('filename', 'uploaded_file')
                # Optionally limit the length of file content to avoid exceeding token limits
                max_file_content_length = 50000
                if len(file_content) > max_file_content_length:
                    file_content = file_content[:max_file_content_length] + '...'

                system_message = {
                    'role': 'system',
                    'content': f"The user has uploaded a file named '{filename}' with the following content:\n\n{file_content}\n\nPlease use this information to assist the user."
                }
                conversation_history_for_api.append(system_message)
            else:
                continue

        response = gpt_client.chat.completions.create(
            model=gpt_model,
            messages=conversation_history_for_api
        )

        ai_message = response.choices[0].message.content
        conversation_item['messages'].append({'role': 'assistant', 'content': ai_message})
        conversation_item['last_updated'] = datetime.utcnow().isoformat()

        container.upsert_item(body=conversation_item)
        #print("AI response generated and conversation updated.")

        return jsonify({
            'reply': ai_message,
            'conversation_id': conversation_id,
            'conversation_title': conversation_item['title']
        })