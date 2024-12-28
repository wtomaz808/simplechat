from config import *
from functions_documents import *
from functions_authentication import *

def register_route_frontend_admin_settings(app):
    @app.route('/admin/settings', methods=['GET', 'POST'])
    @login_required
    def admin_settings():
        settings = get_settings()
        print('---------')
        print(settings)
        print('---------')        
        if request.method == 'POST':
            app_title = request.form.get('app_title', 'AI Chat Application')
            max_file_size_mb = int(request.form.get('max_file_size_mb', 16))
            conversation_history_limit = int(request.form.get('conversation_history_limit', 10))
            default_system_prompt = request.form.get('default_system_prompt', '')
            llm_model = request.form.get('llm_model', 'gpt-3.5-turbo')
            use_external_apis = request.form.get('use_external_apis') == 'on'
            external_chunking_api = request.form.get('external_chunking_api', '')
            external_embedding_api = request.form.get('external_embedding_api', '')
            show_logo = request.form.get('show_logo') == 'on'  # Get the show_logo setting

            logo_file = request.files.get('logo_file')
            if logo_file and allowed_file(logo_file.filename, allowed_extensions={'png', 'jpg', 'jpeg'}):
                filename = secure_filename(logo_file.filename)
                logo_path = os.path.join(app.root_path, 'static', 'images', 'custom_logo.png')
                os.makedirs(os.path.dirname(logo_path), exist_ok=True)
                logo_file.save(logo_path)
                logo_path_relative = 'images/custom_logo.png'
            else:
                logo_path_relative = 'images/logo.svg'

            new_settings = {
                'app_title': app_title,
                'max_file_size_mb': max_file_size_mb,
                'conversation_history_limit': conversation_history_limit,
                'default_system_prompt': default_system_prompt,
                'llm_model': llm_model,
                'use_external_apis': use_external_apis,
                'external_chunking_api': external_chunking_api,
                'external_embedding_api': external_embedding_api,
                'logo_path': logo_path_relative,
                'show_logo': show_logo,  # Include the new setting
                'models': MODELS
            }
            update_settings(new_settings)
            settings.update(new_settings)
            #print("Admin settings updated successfully.")

            return redirect(url_for('admin_settings'))

        return render_template('admin_settings.html', settings=settings)