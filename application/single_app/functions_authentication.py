from config import *

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            #print("User not logged in. Redirecting to login page.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_id():
    user = session.get('user')
    if user:
        return user.get('oid')
    return None