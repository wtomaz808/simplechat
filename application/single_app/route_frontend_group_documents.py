from config import *
from functions_authentication import *

def register_route_frontend_group_documents(app):
    @app.route('/group_documents', methods=['GET'])
    @login_required
    @user_required
    def group_documents():
        """Render the Group Documents page for the current active group."""
        user_id = get_current_user_id()
        if not user_id:
            return redirect(url_for('login'))
        # Just render the template. The front-end JS will call the new APIs.
        return render_template('group_documents.html')
