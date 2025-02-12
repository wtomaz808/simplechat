# route_frontend_safety.py

from config import *
from functions_authentication import *
from functions_settings import *

def register_route_frontend_safety(app):
    @app.route('/admin/safety_violations', methods=['GET'])
    @login_required
    @admin_required
    def admin_safety_violations():
        settings = get_settings()

        if not settings.get("enable_content_safety"):
            return jsonify({"error": "Safety violations are disabled."}), 400
        
        return render_template('admin_safety_violations.html')