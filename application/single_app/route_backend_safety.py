# route_backend_safety.py

from config import *
from functions_authentication import *
from functions_settings import *

def register_route_backend_safety(app):
    @app.route('/api/safety/debug', methods=['GET'])
    def debug_safety():
        settings = get_settings()

        if not settings.get("enable_content_safety"):
            return jsonify({"error": "Safety violations are disabled."}), 400

        query = "SELECT c.id, c.timestamp FROM c"
        items = list(safety_container.query_items(query=query, enable_cross_partition_query=True))
        return jsonify(items)

    @app.route('/api/safety/logs', methods=['GET'])
    @login_required
    @admin_required
    def get_safety_logs():
        settings = get_settings()

        if not settings.get("enable_content_safety"):
            return jsonify({"error": "Safety violations are disabled."}), 400
        
        query = "SELECT * FROM c"
        items = list(safety_container.query_items(query=query, enable_cross_partition_query=True))
        return jsonify({"logs": items}), 200

    @app.route('/api/safety/logs/<string:log_id>', methods=['PATCH'])
    @login_required
    @admin_required
    def update_safety_log(log_id):
        """
        Updates status, action, and notes on a safety log.
        Also sets timestamps (created_at if missing, and last_updated).
        """
        data = request.json
        status = data.get("status")
        action = data.get("action")
        notes = data.get("notes")

        settings = get_settings()

        if not settings.get("enable_content_safety"):
            return jsonify({"error": "Safety violations are disabled."}), 400
        
        try:
            item = safety_container.read_item(item=log_id, partition_key=log_id)

            # If we don't yet have created_at, set it now
            if not item.get("created_at"):
                item["created_at"] = datetime.utcnow().isoformat()

            # Update fields if they are provided
            if status:
                item["status"] = status
            if action:
                item["action"] = action
                # If desired, perform something special for "WarnUser" or "SuspendUser", etc.
                # e.g., if action == "WarnUser": send_warning_email(item["user_id"]) 
                # For now, we do nothing except store the value.

            if notes is not None:
                item["notes"] = notes  # store/overwrite admin notes

            item["last_updated"] = datetime.utcnow().isoformat()

            safety_container.upsert_item(item)

            return jsonify({"message": "Safety log updated successfully."}), 200
        except exceptions.CosmosHttpResponseError as e:
            return jsonify({"error": str(e)}), 404