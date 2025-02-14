# route_frontend_group_documents.py

from config import *
from functions_authentication import *
from functions_settings import *

def register_route_frontend_group_documents(app):
    @app.route('/group_documents', methods=['GET'])
    @login_required
    @user_required
    @enabled_required("enable_group_documents")
    def group_documents():
        """Render the Group Documents page for the current active group."""
        user_id = get_current_user_id()
        
        if not user_id:
            return redirect(url_for('login'))

        return render_template('group_documents.html')
