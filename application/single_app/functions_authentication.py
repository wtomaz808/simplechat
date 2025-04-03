# functions_authentication.py

from config import *
from functions_settings import *

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            is_api_request = (
                request.accept_mimetypes.accept_json and
                not request.accept_mimetypes.accept_html
            ) or request.path.startswith('/api/')

            if is_api_request:
                print(f"API request to {request.path} blocked (401 Unauthorized). No valid session.")
                return jsonify({"error": "Unauthorized", "message": "Authentication required"}), 401
            else:
                print(f"Browser request to {request.path} redirected ta login. No valid session.")
                return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user', {})
        if 'roles' not in user or ('User' not in user['roles'] and 'Admin' not in user['roles']):
             if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html or request.path.startswith('/api/'):
                  return jsonify({"error": "Forbidden", "message": "Insufficient permissions (User/Admin role required)"}), 403
             else:
                  return "Forbidden", 403
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user', {})
        if 'roles' not in user or 'Admin' not in user['roles']:
             if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html or request.path.startswith('/api/'):
                  return jsonify({"error": "Forbidden", "message": "Insufficient permissions (Admin role required)"}), 403
             else:
                  return "Forbidden", 403
        return f(*args, **kwargs)
    return decorated_function

def feedback_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user', {})
        settings = get_settings()
        require_member_of_feedback_admin = settings.get("require_member_of_feedback_admin", False)

        if require_member_of_feedback_admin:
            if 'roles' not in user or 'FeedbackAdmin' not in user['roles']:
                 is_api_request = (request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html) or request.path.startswith('/api/')
                 if is_api_request:
                      return jsonify({"error": "Forbidden", "message": "Insufficient permissions (FeedbackAdmin role required)"}), 403
                 else:
                      return "Forbidden: FeedbackAdmin role required", 403
        return f(*args, **kwargs)
    return decorated_function
    
def safety_violation_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user', {})
        settings = get_settings()
        require_member_of_safety_violation_admin = settings.get("require_member_of_safety_violation_admin", False)

        if require_member_of_safety_violation_admin:
            if 'roles' not in user or 'SafetyViolationAdmin' not in user['roles']:
                is_api_request = (request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html) or request.path.startswith('/api/')
                if is_api_request:
                    return jsonify({"error": "Forbidden", "message": "Insufficient permissions (SafetyViolationAdmin role required)"}), 403
                else:
                    return "Forbidden: SafetyViolationAdmin role required", 403
        return f(*args, **kwargs)
    return decorated_function

def create_group_role_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user', {})
        settings = get_settings()
        require_member_of_create_group = settings.get("require_member_of_create_group", False)

        if require_member_of_create_group:
            if 'roles' not in user or 'CreateGroups' not in user['roles']:
                is_api_request = (request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html) or request.path.startswith('/api/')
                if is_api_request:
                    return jsonify({"error": "Forbidden", "message": "Insufficient permissions (CreateGroups role required)"}), 403
                else:
                    return "Forbidden: CreateGroups role required", 403
        return f(*args, **kwargs)
    return decorated_function
    
def create_public_workspace_role_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user', {})
        settings = get_settings()
        require_member_of_create_public_workspace = settings.get("require_member_of_create_public_workspace", False)

        if require_member_of_create_public_workspace:
            if 'roles' not in user or 'CreatePublicWorkspaces' not in user['roles']:
                is_api_request = (request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html) or request.path.startswith('/api/')
                if is_api_request:
                    return jsonify({"error": "Forbidden", "message": "Insufficient permissions (CreatePublicWorkspaces role required)"}), 403
                else:
                    return "Forbidden: CreatePublicWorkspaces role required", 403
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_id():
    user = session.get('user')
    if user:
        return user.get('oid')
    return None

def get_current_user_info():
    user = session.get("user")
    if not user:
        return None
    return {
        "userId": user.get("oid"), 
        "email": user.get("preferred_username"),
        "displayName": user.get("name")
    }
