# route_frontend_chats.py

from config import *
from functions_authentication import *
from functions_content import *
from functions_settings import *
from functions_documents import *

def register_route_frontend_chats(app):
    @app.route('/chats', methods=['GET'])
    @login_required
    @user_required
    def chats():
        user_id = get_current_user_id()
        settings = get_settings()
        user_settings = get_user_settings(user_id)
        public_settings = sanitize_settings_for_user(settings)
        enable_user_feedback = public_settings.get("enable_user_feedback", False)
        enable_enhanced_citations = public_settings.get("enable_enhanced_citations", False)
        active_group_id = user_settings["settings"].get("activeGroupOid", "")
        if not user_id:
            return redirect(url_for('login'))
        return render_template('chats.html', settings=public_settings, enable_user_feedback=enable_user_feedback, active_group_id=active_group_id, enable_enhanced_citations=enable_enhanced_citations)
    
    @app.route('/upload', methods=['POST'])
    @login_required
    @user_required
    def upload_file():
        settings = get_settings()
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401

        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        conversation_id = request.form.get('conversation_id')

        if not file.filename:
            return jsonify({'error': 'No selected file'}), 400

        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            conversation_item = {
                'id': conversation_id,
                'user_id': user_id,
                'last_updated': datetime.utcnow().isoformat(),
                'title': 'New Conversation'
            }
            container.upsert_item(conversation_item)
        else:
            try:
                conversation_item = container.read_item(
                    item=conversation_id,
                    partition_key=conversation_id
                )
            except CosmosResourceNotFoundError:
                conversation_id = str(uuid.uuid4())
                conversation_item = {
                    'id': conversation_id,
                    'user_id': user_id,
                    'last_updated': datetime.utcnow().isoformat(),
                    'title': 'New Conversation'
                }
                container.upsert_item(conversation_item)
            except Exception as e:
                return jsonify({'error': f'Error reading conversation: {str(e)}'}), 500
        
        file.seek(0, os.SEEK_END)
        file_length = file.tell()
        max_file_size_bytes = settings.get('max_file_size_mb') * 1024 * 1024
        if file_length > max_file_size_bytes:
            return jsonify({'error': 'File size exceeds maximum allowed size'}), 400
        file.seek(0)

        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            file.save(tmp_file.name)
            temp_file_path = tmp_file.name

        extracted_content  = ''
        is_table = False 

        try:
            if file_ext in ['.pdf', '.docx', '.xlsx', '.pptx', '.html', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.heif']:
                extracted_content  = extract_content_with_azure_di(temp_file_path)
            elif file_ext == '.txt':
                extracted_content  = extract_text_file(temp_file_path)
            elif file_ext == '.md':
                extracted_content  = extract_markdown_file(temp_file_path)
            elif file_ext == '.json':
                with open(temp_file_path, 'r', encoding='utf-8') as f:
                    parsed_json = json.load(f)
                    extracted_content  = json.dumps(parsed_json, indent=2)
            elif file_ext in ['.csv', '.xls', '.xlsx']:
                extracted_content = extract_table_file(temp_file_path, file_ext)
                is_table = True
            else:
                return jsonify({'error': 'Unsupported file type'}), 400

        except Exception as e:
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
        finally:
            os.remove(temp_file_path)

        try:
            file_message_id = f"{conversation_id}_file_{int(time.time())}_{random.randint(1000,9999)}"
            file_message = {
                'id': file_message_id,
                'conversation_id': conversation_id,
                'role': 'file',
                'filename': filename,
                'file_content': extracted_content,
                'is_table': is_table,
                'timestamp': datetime.utcnow().isoformat(),
                'model_deployment_name': None
            }

            messages_container.upsert_item(file_message)

            conversation_item['last_updated'] = datetime.utcnow().isoformat()
            container.upsert_item(conversation_item)

        except Exception as e:
            return jsonify({
                'error': f'Error adding file to conversation: {str(e)}'
            }), 500

        return jsonify({
            'message': 'File added to the conversation successfully',
            'conversation_id': conversation_id
        }), 200
    
    @app.route("/view_pdf", methods=["GET"])
    @login_required
    @user_required
    @enabled_required("enable_user_workspace")
    def view_pdf():
        """
        1) Grab 'doc_id' and 'page' from query params.
        2) Validate user and doc_id ownership.
        3) Generate SAS URL for the PDF in Azure Blob Storage.
        4) Download the file to a temp location or memory.
        5) (Optional) Use PyMuPDF to do further operations (like extracting a single page).
        6) Return the PDF file via send_file.
        """

        # 1) Get query params
        doc_id = request.args.get("doc_id")
        page_number = request.args.get("page", default=1, type=int)

        user_id = get_current_user_id()
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401

        # 2) Validate doc_id -> get the blob name
        #    For example, doc_id references the DB row that includes user_id & file_name
        doc_response, status_code = get_user_document(user_id, doc_id)
        if status_code != 200:
            return doc_response, status_code

        raw_doc = doc_response.get_json()
        blob_name = f"{raw_doc['user_id']}/{raw_doc['file_name']}"

        # 3) Generate the SAS URL (short-lived, read-only)
        settings = get_settings()
        blob_service_client = CLIENTS.get("office_docs_client")
        container_client = blob_service_client.get_container_client(user_documents_container_name)

        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=container_client.container_name,
            blob_name=blob_name,
            account_key=settings.get("office_docs_key"),
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(minutes=60)  # 60-minute expiry
        )

        signed_url = (
            f"https://{blob_service_client.account_name}.blob.core.windows.net"
            f"/{container_client.container_name}/{blob_name}?{sas_token}"
        )

        if AZURE_ENVIRONMENT == "usgovernment":
            signed_url = (
                f"https://{blob_service_client.account_name}.blob.core.usgovcloudapi.net"
                f"/{container_client.container_name}/{blob_name}?{sas_token}"
            )

        # 4) Download the PDF from Azure to a temp file (or you can use in-memory BytesIO)
        random_uuid = str(uuid.uuid4())
        temp_pdf_path = f"temp_file_{random_uuid}.pdf"

        try:
            # Download PDF
            response = requests.get(signed_url, timeout=30)
            response.raise_for_status()
            with open(temp_pdf_path, "wb") as f:
                f.write(response.content)

            # 4) Extract the relevant pages
            pdf_document = fitz.open(temp_pdf_path)
            total_pages = pdf_document.page_count

            # Convert 1-based page_number to 0-based index
            current_idx = page_number - 1  
            if current_idx < 0 or current_idx >= total_pages:
                pdf_document.close()
                os.remove(temp_pdf_path)
                return jsonify({"error": "Requested page is out of range"}), 400

            # Default to extracting ONLY the current page
            start_idx = current_idx
            end_idx = current_idx

            # If there's a page before, include it
            if current_idx > 0:
                start_idx = current_idx - 1

            # If there's a page after, include it
            if current_idx < total_pages - 1:
                end_idx = current_idx + 1

            # Create a new PDF with the subset of pages
            extracted_pdf = fitz.open()
            extracted_pdf.insert_pdf(pdf_document, from_page=start_idx, to_page=end_idx)

            # Overwrite the temp file with the smaller PDF
            extracted_pdf.save(temp_pdf_path, garbage=4, deflate=True)
            extracted_pdf.close()
            pdf_document.close()

            # 5) Return the trimmed PDF
            # The front-end can point to: /view_pdf?doc_id=XXX&page=2#page=2
            return send_file(temp_pdf_path, as_attachment=False)

        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
            return jsonify({"error": str(e)}), 500
        finally:
            # Clean up the temp file after the request finishes
            # (You can also do this in an after_request or teardown block.)
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)