# route_backend_prompts.py

from config import *
from functions_authentication import *
from functions_settings import *
from functions_prompts import *

def register_route_backend_prompts(app):
    @app.route('/api/prompts', methods=['GET'])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def get_prompts():
        user_id = get_current_user_id()
        page, page_size = get_pagination_params(request.args)
        search_term = request.args.get('search', None)

        # Base query
        query = f"SELECT * FROM c WHERE c.user_id = @user_id AND c.type = 'user_prompt'"
        parameters = [ {"name": "@user_id", "value": user_id} ]

        # Count query (without pagination limits but with filters)
        count_query = f"SELECT VALUE COUNT(1) FROM c WHERE c.user_id = @user_id AND c.type = 'user_prompt'"

        # Add search filter if provided
        if search_term:
            # Make sure search term isn't excessively long
            safe_search_term = search_term[:100] # Limit length
            query += " AND CONTAINS(c.name, @search_term, true)" # Case-insensitive search
            count_query += " AND CONTAINS(c.name, @search_term, true)"
            parameters.append({"name": "@search_term", "value": safe_search_term})

        # Order results (optional, but good for consistency)
        query += " ORDER BY c.updated_at DESC" # Or c.name ASC

        # Calculate offset for pagination
        offset = (page - 1) * page_size
        query += f" OFFSET {offset} LIMIT {page_size}"

        try:
            # Execute count query
            count_results = list(prompts_container.query_items(query=count_query, parameters=parameters, enable_cross_partition_query=True))
            total_count = count_results[0] if count_results else 0

            # Execute main query for the page
            items = list(prompts_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))

            return jsonify({
                "prompts": items,
                "page": page,
                "page_size": page_size,
                "total_count": total_count
            }), 200

        except Exception as e:
            app.logger.error(f"Unexpected error fetching prompts: {e}")
            return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

    @app.route('/api/prompts', methods=['POST'])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def create_prompt():
        user_id = get_current_user_id()
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Invalid JSON payload"}), 400

            name = data.get("name")
            content = data.get("content")

            if not name or not isinstance(name, str) or len(name.strip()) == 0:
                return jsonify({"error": "Missing or invalid 'name'"}), 400
            if not content or not isinstance(content, str) or len(content.strip()) == 0:
                 # Allow potentially empty content? Decide based on requirements.
                 # If empty content is invalid:
                 return jsonify({"error": "Missing or invalid 'content'"}), 400

            new_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

            prompt_doc = {
                "id": new_id,
                "user_id": user_id,
                "name": name.strip(), # Trim whitespace
                "content": content, # Don't strip content usually
                "type": "user_prompt",
                "created_at": now,
                "updated_at": now
            }

            created_item = prompts_container.create_item(body=prompt_doc)
            # Return only essential fields or the full created item
            return jsonify({
                 "id": created_item['id'],
                 "name": created_item['name'],
                 "updated_at": created_item['updated_at']
             }), 201 # Use 201 Created status code

        except Exception as e:
            app.logger.error(f"Unexpected error creating prompt: {e}")
            return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

    @app.route('/api/prompts/<prompt_id>', methods=['GET'])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def get_prompt(prompt_id):
        user_id = get_current_user_id()
        try:
            # Attempt direct read first if partition key is id
            try:
                item = prompts_container.read_item(item=prompt_id, partition_key=prompt_id)
                # Verify user_id and type if read was successful
                if item.get('user_id') == user_id and item.get('type') == 'user_prompt':
                    return jsonify(item), 200
                else:
                    # Item found but doesn't belong to user or isn't a prompt
                     return jsonify({"error": "Prompt not found or access denied"}), 404
            except:
                # If direct read fails (e.g., partition key isn't ID), fall back to query
                query = "SELECT * FROM c WHERE c.id = @prompt_id AND c.user_id = @user_id AND c.type='user_prompt'"
                parameters = [
                    {"name": "@prompt_id", "value": prompt_id},
                    {"name": "@user_id", "value": user_id}
                ]
                items = list(prompts_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
                if not items:
                    return jsonify({"error": "Prompt not found"}), 404
                return jsonify(items[0]), 200

        except Exception as e:
            app.logger.error(f"Unexpected error getting prompt {prompt_id}: {e}")
            return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

    @app.route('/api/prompts/<prompt_id>', methods=['PATCH'])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def update_prompt(prompt_id):
        user_id = get_current_user_id()
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Invalid JSON payload"}), 400

            # Validate incoming data - only update allowed fields
            updates = {}
            if "name" in data:
                name = data["name"]
                if not name or not isinstance(name, str) or len(name.strip()) == 0:
                     return jsonify({"error": "Invalid 'name' provided"}), 400
                updates["name"] = name.strip()
            if "content" in data:
                content = data["content"]
                # Allow empty content? Assume yes for now. Check type.
                if content is None or not isinstance(content, str): # Check if it's null or not a string
                     return jsonify({"error": "Invalid 'content' provided"}), 400
                updates["content"] = content # Don't strip content

            if not updates:
                 return jsonify({"error": "No fields provided for update"}), 400

            # Fetch existing doc to ensure it belongs to the user
            try:
                item = prompts_container.read_item(item=prompt_id, partition_key=prompt_id)
                if item.get('user_id') != user_id or item.get('type') != 'user_prompt':
                     return jsonify({"error": "Prompt not found or access denied"}), 404
            except:
                 # Query as fallback if direct read fails
                 query = "SELECT * FROM c WHERE c.id = @prompt_id AND c.user_id = @user_id AND c.type='user_prompt'"
                 parameters = [{"name": "@prompt_id", "value": prompt_id}, {"name": "@user_id", "value": user_id}]
                 items = list(prompts_container.query_items(query=query, parameters=parameters, enable_cross_partition_query=True))
                 if not items:
                     return jsonify({"error": "Prompt not found"}), 404
                 item = items[0] # Get the item if found via query

            # Apply updates
            for key, value in updates.items():
                item[key] = value
            item["updated_at"] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

            # Use replace_item for updates, passing the etag for optimistic concurrency
            updated_item = prompts_container.replace_item(item=item['id'], body=item) # ETag handled automatically by SDK if present in 'item'

            # Return minimal confirmation or updated fields
            return jsonify({
                 "id": updated_item['id'],
                 "name": updated_item['name'],
                 "updated_at": updated_item['updated_at']
             }), 200

        except Exception as e:
            app.logger.error(f"Unexpected error updating prompt {prompt_id}: {e}")
            return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

    @app.route('/api/prompts/<prompt_id>', methods=['DELETE'])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def delete_prompt(prompt_id):
        user_id = get_current_user_id()
        try:
            # Need partition key for deletion. Assuming it's the 'id' field based on other operations.
            # First, verify ownership before deleting
            try:
                 item = prompts_container.read_item(item=prompt_id, partition_key=prompt_id)
                 if item.get('user_id') != user_id or item.get('type') != 'user_prompt':
                      return jsonify({"error": "Prompt not found or access denied"}), 404
                 # If ownership verified, proceed to delete
                 prompts_container.delete_item(item=prompt_id, partition_key=prompt_id)
                 return jsonify({"message": "Prompt deleted successfully"}), 200 # 200 OK or 204 No Content
            except:
                 # Item doesn't exist
                 return jsonify({"error": "Prompt not found"}), 404

        except Exception as e:
            app.logger.error(f"Unexpected error deleting prompt {prompt_id}: {e}")
            return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500