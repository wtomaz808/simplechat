# functions_authentication.py

from config import *
from functions_settings import *

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            #print("User not logged in. Redirecting to login page.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user', {})
        # If 'roles' is not in user or 'User' is not part of role or 'Admin' is not part of role, block access
        if 'roles' not in user or ('User' not in user['roles'] and 'Admin' not in user['roles']):
            return "Unauthorized", 403
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user', {})
        # If 'roles' is not in user or 'Admin' is not part of roles, block access
        if 'roles' not in user or 'Admin' not in user['roles']:
            return "Unauthorized", 403  # or redirect somewhere else if you prefer
        return f(*args, **kwargs)
    return decorated_function

def feedback_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user', {})
        settings = get_settings()
        require_member_of_feedback_admin = settings.get("require_member_of_feedback_admin", False)

        if require_member_of_feedback_admin:
            # If 'roles' is not in user or 'FeedbackAdmin' is not part of roles, block access
            if 'roles' not in user or 'FeedbackAdmin' not in user['roles']:
                return "Unauthorized", 403  # or redirect somewhere else if you prefer
        
        return f(*args, **kwargs)
    
    return decorated_function
    
def safety_violation_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user', {})
        settings = get_settings()
        require_member_of_safety_violation_admin = settings.get("require_member_of_safety_violation_admin", False)

        if require_member_of_safety_violation_admin:
            # If 'roles' is not in user or 'SafetyViolationAdmin' is not part of roles, block access
            if 'roles' not in user or 'SafetyViolationAdmin' not in user['roles']:
                return "Unauthorized", 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def create_group_role_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user', {})
        settings = get_settings()
        require_member_of_create_group = settings.get("require_member_of_create_group", False)

        if require_member_of_create_group:
            # If 'roles' is not in user or 'CreateGroups' is not part of roles, block
            if 'roles' not in user or 'CreateGroups' not in user['roles']:
                return "Unauthorized", 403

        return f(*args, **kwargs)
    
    return decorated_function
    
def create_public_workspace_role_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get('user', {})
        settings = get_settings()
        require_member_of_create_public_workspace = settings.get("require_member_of_create_public_workspace", False)

        if require_member_of_create_public_workspace:
            # If 'roles' is not in user or 'CreatePublicWorkspaces' is not part of roles, block access
            if 'roles' not in user or 'CreatePublicWorkspaces' not in user['roles']:
                return "Unauthorized", 403  # or redirect somewhere else if you prefer
        
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
