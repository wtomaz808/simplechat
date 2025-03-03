# route_backend_conversations.py

from config import *
from functions_authentication import *
from functions_settings import *

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
            # Then query the messages in messages_container
            message_query = f"SELECT * FROM c WHERE c.conversation_id = '{conversation_id}' ORDER BY c.timestamp ASC"
            messages = list(messages_container.query_items(
                query=message_query,
                partition_key=conversation_id
            ))
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
        return jsonify({
            'conversations': items
        }), 200


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

        return jsonify({
            'conversation_id': conversation_id,
            'title': 'New Conversation'
        }), 200
    
    @app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
    @login_required
    @user_required
    def delete_conversation(conversation_id):
        """
        Delete a conversation. If archiving is enabled, copy it to archived_conversations first.
        """
        settings = get_settings()
        archiving_enabled = settings.get('enable_conversation_archiving', False)

        try:
            conversation_item = container.read_item(
                item=conversation_id,
                partition_key=conversation_id
            )
        except CosmosResourceNotFoundError:
            return jsonify({
                "error": f"Conversation {conversation_id} not found."
            }), 404
        except Exception as e:
            return jsonify({
                "error": str(e)
            }), 500

        if archiving_enabled:
            archived_item = dict(conversation_item)
            archived_item["archived_at"] = datetime.utcnow().isoformat()
            archived_conversations_container.upsert_item(archived_item)

        message_query = f"SELECT * FROM c WHERE c.conversation_id = '{conversation_id}'"
        results = list(messages_container.query_items(
            query=message_query,
            partition_key=conversation_id
        ))

        for doc in results:
            if archiving_enabled:
                archived_doc = dict(doc)
                archived_doc["archived_at"] = datetime.utcnow().isoformat()
                archived_messages_container.upsert_item(archived_doc)

            messages_container.delete_item(doc['id'], partition_key=conversation_id)
        
        try:
            container.delete_item(
                item=conversation_id,
                partition_key=conversation_id
            )
        except Exception as e:
            return jsonify({
                "error": str(e)
            }), 500

        return jsonify({
            "success": True
        }), 200