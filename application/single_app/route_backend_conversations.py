# route_backend_conversations.py

from config import *
from functions_authentication import *

def register_route_backend_conversations(app):

    @app.route('/api/get_messages', methods=['GET'])
    @login_required
    @user_required
    def api_get_messages():
        conversation_id = request.args.get('conversation_id')
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        if not conversation_id:
            return jsonify({'error': 'No conversation_id provided'}), 400
        try:
            conversation_item = container.read_item(
                item=conversation_id,
                partition_key=conversation_id
            )
            messages = conversation_item.get('messages', [])
            return jsonify({'messages': messages})
        except CosmosResourceNotFoundError:
            return jsonify({'messages': []})
        except Exception:
            return jsonify({'error': 'Conversation not found'}), 404
        
    @app.route('/api/get_conversations', methods=['GET'])
    @login_required
    @user_required
    def get_conversations():
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        query = f"SELECT c.id, c.title, c.last_updated FROM c WHERE c.user_id = '{user_id}' ORDER BY c.last_updated DESC"
        items = list(container.query_items(query=query, enable_cross_partition_query=True))
        return jsonify({'conversations': items})


    @app.route('/api/create_conversation', methods=['POST'])
    @login_required
    @user_required
    def create_conversation():
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401

        conversation_id = str(uuid.uuid4())
        conversation_item = {
            'id': conversation_id,
            'user_id': user_id,
            'messages': [],
            'last_updated': datetime.utcnow().isoformat(),
            'title': 'New Conversation'
        }
        container.upsert_item(conversation_item)

        return jsonify({'conversation_id': conversation_id}), 200
    
    @app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
    @login_required
    @user_required
    def delete_conversation(conversation_id):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        try:
            conversation_item = container.read_item(
                item=conversation_id,
                partition_key=conversation_id
            )
            container.delete_item(
                item=conversation_id,
                partition_key=conversation_id
            )

            return jsonify({'message': 'Conversation deleted successfully'}), 200
        except CosmosResourceNotFoundError:
            return jsonify({'error': 'Conversation not found'}), 404
        except Exception as e:
            return jsonify({'error': 'An error occurred while deleting the conversation'}), 500