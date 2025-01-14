from config import *
from functions_documents import *
from functions_authentication import *
from functions_settings import *

def register_route_frontend_admin_settings(app):
    @app.route('/admin/settings', methods=['GET', 'POST'])
    @login_required
    def admin_settings():
        settings = get_settings()

        if request.method == 'POST':
            app_title = request.form.get('app_title', 'AI Chat Application')
            max_file_size_mb = int(request.form.get('max_file_size_mb', 16))
            conversation_history_limit = int(request.form.get('conversation_history_limit', 10))
            default_system_prompt = request.form.get('default_system_prompt', '')
            use_external_apis = request.form.get('use_external_apis') == 'on'
            external_chunking_api = request.form.get('external_chunking_api', '')
            external_embedding_api = request.form.get('external_embedding_api', '')
            show_logo = request.form.get('show_logo') == 'on'

            # New fields for Azure OpenAI GPT / Embedding / Image Gen
            azure_openai_gpt_endpoint = request.form.get('azure_openai_gpt_endpoint', '')
            azure_openai_gpt_api_version = request.form.get('azure_openai_gpt_api_version', '')
            azure_openai_gpt_authentication_type = request.form.get('azure_openai_gpt_authentication_type', 'key')
            azure_openai_gpt_key = request.form.get('azure_openai_gpt_key', '')

            gpt_model = request.form.get('gpt_model', 'gpt-4o')
            azure_openai_embedding_endpoint = request.form.get('azure_openai_embedding_endpoint', '')
            azure_openai_embedding_api_version = request.form.get('azure_openai_embedding_api_version', '')
            azure_openai_embedding_authentication_type = request.form.get('azure_openai_embedding_authentication_type', 'key')
            azure_openai_embedding_key = request.form.get('azure_openai_embedding_key', '')

            embedding_model = request.form.get('embedding_model', 'text-embedding-ada-002')
            enable_image_generation = request.form.get('enable_image_generation') == 'on'
            azure_openai_image_gen_endpoint = request.form.get('azure_openai_image_gen_endpoint', '')
            azure_openai_image_gen_api_version = request.form.get('azure_openai_image_gen_api_version', '')
            azure_openai_image_gen_authentication_type = request.form.get('azure_openai_image_gen_authentication_type', 'key')
            azure_openai_image_gen_key = request.form.get('azure_openai_image_gen_key', '')

            image_gen_model = request.form.get('image_gen_model', 'dall-e-2')

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
                'azure_openai_gpt_endpoint': azure_openai_gpt_endpoint,
                'azure_openai_gpt_api_version': azure_openai_gpt_api_version,
                'azure_openai_gpt_authentication_type': azure_openai_gpt_authentication_type,
                'azure_openai_gpt_key': azure_openai_gpt_key,
                'gpt_model': gpt_model,
                'azure_openai_embedding_endpoint': azure_openai_embedding_endpoint,
                'azure_openai_embedding_api_version': azure_openai_embedding_api_version,
                'azure_openai_embedding_authentication_type': azure_openai_embedding_authentication_type,
                'azure_openai_embedding_key': azure_openai_embedding_key,
                'embedding_model': embedding_model,
                'enable_image_generation': enable_image_generation,
                'azure_openai_image_gen_endpoint': azure_openai_image_gen_endpoint,
                'azure_openai_image_gen_api_version': azure_openai_image_gen_api_version,
                'azure_openai_image_gen_authentication_type': azure_openai_image_gen_authentication_type,
                'azure_openai_image_gen_key': azure_openai_image_gen_key,
                'image_gen_model': image_gen_model,
                'use_external_apis': use_external_apis,
                'external_chunking_api': external_chunking_api,
                'external_embedding_api': external_embedding_api,
                'logo_path': logo_path_relative,
                'show_logo': show_logo
            }
            update_settings(new_settings)
            settings.update(new_settings)

            print("Admin settings updated successfully.")

            return redirect(url_for('admin_settings'))

        return render_template('admin_settings.html', settings=settings)