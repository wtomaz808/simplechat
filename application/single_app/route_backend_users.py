# route_backend_users.py

from config import *
from functions_authentication import *
from functions_settings import *

def register_route_backend_users(app):
    """
    This route will expose GET /api/userSearch?query=<searchTerm> which calls
    Microsoft Graph to find users by displayName, mail, userPrincipalName, etc.
    """

    # route_backend_users.py
from functions_authentication import *
from config import *

def register_route_backend_users(app):
    @app.route("/api/userSearch", methods=["GET"])
    @login_required
    @user_required
    def api_user_search():
        query = request.args.get("query", "").strip()
        if not query:
            return jsonify([]), 200  # No query provided

        token = session.get("access_token")
        if not token:
            return jsonify({"error": "No access token in session"}), 401

        user_endpoint = "https://graph.microsoft.com/v1.0/users"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Example filter using startsWith on displayName, mail, or userPrincipalName
        filter_str = (
            f"startswith(displayName, '{query}') "
            f"or startswith(mail, '{query}') "
            f"or startswith(userPrincipalName, '{query}')"
        )
        params = {
            "$filter": filter_str,
            "$top": 10,  # up to 10 matches
            "$select": "id,displayName,mail,userPrincipalName"
        }

        response = requests.get(user_endpoint, headers=headers, params=params)
        if response.status_code != 200:
            return jsonify({
                "error": "Graph API error",
                "status": response.status_code,
                "details": response.text
            }), 500

        user_results = response.json().get("value", [])
        results = []
        for user in user_results:
            # If the user doesn't have 'mail', fallback to userPrincipalName, etc.
            email = user.get("mail") or user.get("userPrincipalName") or ""
            results.append({
                "id": user.get("id"),  # <-- This will be the real Azure AD Object ID (GUID)
                "displayName": user.get("displayName", "(no name)"),
                "email": email
            })

        return jsonify(results), 200
    
    @app.route('/api/user/settings', methods=['GET', 'POST'])
    @login_required
    @user_required
    def user_settings():
        user_id = get_current_user_id()
        
        if request.method == 'POST':
            # Get settings from the form or request JSON
            active_group_oid = request.form.get('activeGroupOid', '') or request.json.get('activeGroupOid', '')
            
            # Construct new settings dictionary
            new_settings = {
                "settings": {
                    "activeGroupOid": active_group_oid
                },
                "lastUpdated": datetime.utcnow().isoformat()
            }
            
            # Update user settings in the database
            update_user_settings(user_id, new_settings)
            return jsonify({"message": "User settings updated successfully"}), 200

        # If GET request, fetch the settings
        user_settings_data = get_user_settings(user_id)
        return jsonify(user_settings_data if user_settings_data else {})




