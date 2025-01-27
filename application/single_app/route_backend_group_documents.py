from config import *
from functions_authentication import *
from functions_settings import get_user_settings
from functions_group import get_user_role_in_group, find_group_by_id
from functions_group_documents import *

def register_route_backend_group_documents(app):
    """
    Provides backend routes for group-level document management:
    - GET /api/group_documents      (list)
    - POST /api/group_documents/upload
    - DELETE /api/group_documents/<doc_id>
    """

    @app.route('/api/group_documents', methods=['GET'])
    @login_required
    def api_get_group_documents():
        """
        Return the list of documents for the user's *active* group.
        """
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401

        # Retrieve the user's active group
        user_settings = get_user_settings(user_id)
        active_group_id = user_settings["settings"].get("activeGroupOid")

        if not active_group_id:
            return jsonify({'error': 'No active group selected'}), 400

        # Check membership in that group
        group_doc = find_group_by_id(active_group_id)
        if not group_doc:
            return jsonify({'error': 'Active group not found'}), 404

        role = get_user_role_in_group(group_doc, user_id)
        if not role:
            return jsonify({'error': 'You are not a member of the active group'}), 403

        # Retrieve documents from group_documents_container
        try:
            docs = get_group_documents(active_group_id)
            return jsonify({'documents': docs}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500


    @app.route('/api/group_documents/upload', methods=['POST'])
    @login_required
    def api_upload_group_document():
        """
        Upload a new document into the active group’s collection, if user role
        is Owner/Admin/Document Manager.
        """
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401

        # Retrieve the user's active group
        user_settings = get_user_settings(user_id)
        active_group_id = user_settings["settings"].get("activeGroupOid")
        if not active_group_id:
            return jsonify({'error': 'No active group selected'}), 400

        group_doc = find_group_by_id(active_group_id)
        if not group_doc:
            return jsonify({'error': 'Active group not found'}), 404

        role = get_user_role_in_group(group_doc, user_id)
        if role not in ["Owner", "Admin", "DocumentManager"]:
            return jsonify({'error': 'You do not have permission to upload documents'}), 403

        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({'error': 'No selected file'}), 400

        try:
            result = process_group_document_upload(file, active_group_id, user_id)
            return jsonify({'message': 'Document uploaded successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500


    @app.route('/api/group_documents/<doc_id>', methods=['DELETE'])
    @login_required
    def api_delete_group_document(doc_id):
        """
        Delete a document from the active group, if user role
        is Owner/Admin/Document Manager.
        """
        user_id = get_current_user_id()
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401

        # Retrieve the user's active group
        user_settings = get_user_settings(user_id)
        active_group_id = user_settings["settings"].get("activeGroupOid")
        if not active_group_id:
            return jsonify({'error': 'No active group selected'}), 400

        group_doc = find_group_by_id(active_group_id)
        if not group_doc:
            return jsonify({'error': 'Active group not found'}), 404

        role = get_user_role_in_group(group_doc, user_id)
        if role not in ["Owner", "Admin", "DocumentManager"]:
            return jsonify({'error': 'You do not have permission to delete documents'}), 403

        try:
            delete_group_document(doc_id, active_group_id)
            return jsonify({'message': 'Document deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
