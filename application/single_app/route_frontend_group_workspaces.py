# route_frontend_group_workspaces.py

from config import *
from functions_authentication import *
from functions_settings import *

def register_route_frontend_group_workspaces(app):
    @app.route('/group_workspaces', methods=['GET'])
    @login_required
    @user_required
    @enabled_required("enable_group_workspaces")
    def group_workspaces():
        """Render the Group workspaces page for the current active group."""
        user_id = get_current_user_id()
        settings = get_settings()
        public_settings = sanitize_settings_for_user(settings)
        enable_document_classification = settings.get('enable_document_classification', False)
        enable_extract_meta_data = settings.get('enable_extract_meta_data', False)
        enable_video_file_support = settings.get('enable_video_file_support', False)
        enable_audio_file_support = settings.get('enable_audio_file_support', False)
        if not user_id:
            print("User not authenticated.")
            return redirect(url_for('login'))
                
        return render_template(
            'group_workspaces.html', 
            settings=public_settings, 
            enable_document_classification=enable_document_classification, 
            enable_extract_meta_data=enable_extract_meta_data,
            enable_video_file_support=enable_video_file_support,
            enable_audio_file_support=enable_audio_file_support,
        )
