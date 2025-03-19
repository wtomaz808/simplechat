# route_frontend_conversations.py

from config import *
from functions_authentication import *

def register_route_frontend_conversations(app):
    @app.route('/conversations')
    @login_required
    @user_required
    def conversations():
        user_id = get_current_user_id()
        if not user_id:
            return redirect(url_for('login'))
        
        query = f"""
            SELECT *
            FROM c
            WHERE c.user_id = '{user_id}'
            ORDER BY c.last_updated DESC
        """
        items = list(container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        return render_template('conversations.html', conversations=items)

    @app.route('/conversation/<conversation_id>', methods=['GET'])
    @login_required
    @user_required
    def view_conversation(conversation_id):
        user_id = get_current_user_id()
        if not user_id:
            return redirect(url_for('login'))
        try:
            conversation_item = container.read_item(
                item=conversation_id,
                partition_key=conversation_id
            )
        except Exception:
            return "Conversation not found", 404

        message_query = f"""
            SELECT * FROM c
            WHERE c.conversation_id = '{conversation_id}'
            ORDER BY c.timestamp ASC
        """
        messages = list(messages_container.query_items(
            query=message_query,
            partition_key=conversation_id
        ))
        return render_template('chat.html', conversation_id=conversation_id, messages=messages)

    @app.route('/api/conversations/<conversation_id>', methods=['PUT'])
    @login_required
    @user_required
    def update_conversation_title(conversation_id):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401

        # Parse the new title from the request body
        data = request.get_json()
        new_title = data.get('title', '').strip()
        if not new_title:
            return jsonify({'error': 'Title is required'}), 400

        try:
            # Retrieve the conversation
            conversation_item = container.read_item(
                item=conversation_id,
                partition_key=conversation_id
            )

            # Ensure that the conversation belongs to the current user
            if conversation_item.get('user_id') != user_id:
                return jsonify({'error': 'Forbidden'}), 403

            # Update the title
            conversation_item['title'] = new_title

            # Optionally update the last_updated time
            from datetime import datetime
            conversation_item['last_updated'] = datetime.utcnow().isoformat()

            # Write back to Cosmos DB
            container.upsert_item(conversation_item)

            return jsonify({'message': 'Conversation updated', 'title': new_title})
        except Exception as e:
            print(e)
            return jsonify({'error': 'Failed to update conversation'}), 500
    
    @app.route('/conversation/<conversation_id>/messages', methods=['GET'])
    @login_required
    @user_required
    def get_conversation_messages(conversation_id):
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        try:
            _ = container.read_item(conversation_id, conversation_id)
        except CosmosResourceNotFoundError:
            return jsonify({'error': 'Conversation not found'}), 404
        
        msg_query = f"""
            SELECT * FROM c
            WHERE c.conversation_id = '{conversation_id}'
            ORDER BY c.timestamp ASC
        """
        messages = list(messages_container.query_items(
            query=msg_query,
            partition_key=conversation_id
        ))

        for m in messages:
            if m.get('role') == 'file' and 'file_content' in m:
                del m['file_content']

        return jsonify({'messages': messages})