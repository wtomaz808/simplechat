# route_frontend_conversations.py

from config import *
from functions_authentication import *

def register_route_frontend_conversations(app):
    @app.route('/conversations')
    @login_required
    def conversations():
        user_id = get_current_user_id()
        if not user_id:
            #print("User not authenticated.")
            return redirect(url_for('login'))
        query = f"SELECT c.id, c.last_updated FROM c WHERE c.user_id = '{user_id}' ORDER BY c.last_updated DESC"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        #print(f"Retrieved {len(items)} conversations for user {user_id}.")
        return render_template('conversations.html', conversations=items)

    @app.route('/conversation/<conversation_id>')
    @login_required
    def view_conversation(conversation_id):
        user_id = get_current_user_id()
        if not user_id:
            #print("User not authenticated.")
            return redirect(url_for('login'))
        try:
            conversation_item = container.read_item(
                item=conversation_id,
                partition_key=conversation_id
            )
            messages = conversation_item['messages']
            #print(f"Viewing conversation {conversation_id}.")
            return render_template('chat.html', conversation_id=conversation_id, messages=messages)
        except Exception:
            #print(f"Conversation {conversation_id} not found.")
            return "Conversation not found", 404

    @app.route('/conversation/<conversation_id>/messages', methods=['GET'])
    @login_required
    def get_conversation_messages(conversation_id):
        user_id = get_current_user_id()
        if not user_id:
            #print("User not authenticated.")
            return jsonify({'error': 'User not authenticated'}), 401
        try:
            conversation_item = container.read_item(
                item=conversation_id,
                partition_key=conversation_id
            )
            messages = conversation_item.get('messages', [])
            for message in messages:
                if message.get('role') == 'file' and 'file_content' in message:
                    del message['file_content']
            #print(f"Retrieved messages for conversation {conversation_id}.")
            return jsonify({'messages': messages})
        except CosmosResourceNotFoundError:
            #print(f"Conversation {conversation_id} not found.")
            return jsonify({'messages': []})
        except Exception:
            #print(f"Error retrieving conversation {conversation_id}.")
            return jsonify({'error': 'Conversation not found'}), 404