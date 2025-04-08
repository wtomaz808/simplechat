# route_backend_feedback.py

from config import *
from functions_authentication import *
from functions_settings import *   

def register_route_backend_feedback(app):

    @app.route("/feedback/submit", methods=["POST"])
    @login_required
    @user_required
    @enabled_required("enable_user_feedback")
    def feedback_submit():
        """
        Endpoint to store user feedback:
          POST /feedback/submit
          JSON body: { messageId, conversationId, feedbackType, reason }
        """
        data = request.get_json()
        messageId = data.get("messageId")
        conversationId = data.get("conversationId")
        feedbackType = data.get("feedbackType")
        reason = data.get("reason", "")
        user_id = None
        if "user" in session:
            user_id = session["user"].get("oid") or session["user"].get("sub")

        if not messageId or not conversationId or not feedbackType:
            return jsonify({"error": "Missing required fields"}), 400

        try:
            conversation_doc = container.read_item(
                item=conversationId, partition_key=conversationId
            )
        except:
            return jsonify({"error": "Conversation not found"}), 404

        ai_message_text = None
        user_prompt_text = None

        all_messages = conversation_doc.get("messages", [])
        # Find the AI message corresponding to the messageId
        ai_msg_index = -1
        for i, msg in enumerate(all_messages):
            if msg["role"] == "assistant" and msg.get("message_id") == messageId:
                ai_message_text = msg["content"]
                ai_msg_index = i
                break

        # Find the user message immediately preceding the AI message
        if ai_msg_index > 0:
            for i in range(ai_msg_index - 1, -1, -1):
                 if all_messages[i]["role"] == "user":
                     user_prompt_text = all_messages[i]["content"]
                     break # Found the closest preceding user prompt

        if not ai_message_text:
            ai_message_text = "[AI response text not found]"

        if not user_prompt_text:
            # Fallback: Try finding the *last* user message if direct preceding one isn't found
            # (This logic might need refinement based on exact conversation structure needs)
            reversed_messages = list(reversed(all_messages))
            for msg in reversed_messages:
                if msg["role"] == "user":
                    user_prompt_text = msg["content"]
                    break
            if not user_prompt_text:
                user_prompt_text = "[User prompt not found]"


        feedback_id = str(uuid.uuid4())
        item = {
            "id": feedback_id,
            "partitionKey": feedback_id, # Explicitly set partition key if it's the ID
            "userId": user_id,
            "prompt": user_prompt_text,
            "aiResponse": ai_message_text,
            "feedbackType": feedbackType,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "adminReview": {
                "acknowledged": False,
                "analyzedBy": None,
                "analysisNotes": None,
                "responseToUser": None,
                "actionTaken": None,
                "reviewTimestamp": None
            }
        }

        feedback_container.upsert_item(item)

        return jsonify({"success": True, "feedbackId": feedback_id})
    

    @app.route("/feedback/review", methods=["GET"])
    @login_required
    @admin_required
    @enabled_required("enable_user_feedback")
    def feedback_review_get():
        """
        Return feedback for admin review with pagination and filtering.
        """
        try:
            # --- Pagination Parameters ---
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('page_size', 10, type=int)
            if page < 1: page = 1
            if page_size not in [10, 20, 50]: page_size = 10 # Enforce allowed sizes
            offset = (page - 1) * page_size

            # --- Filter Parameters ---
            filter_type = request.args.get('type', None, type=str)
            filter_ack_str = request.args.get('ack', None, type=str) # Keep as string first

            # --- Build Query ---
            base_query = "SELECT * FROM c"
            count_query = "SELECT VALUE COUNT(1) FROM c"
            where_clauses = []
            parameters = []

            # Filter by Feedback Type
            if filter_type and filter_type in ["Positive", "Negative", "Neutral"]:
                where_clauses.append("c.feedbackType = @type")
                parameters.append({"name": "@type", "value": filter_type})

            # Filter by Acknowledged Status
            filter_ack_bool = None
            if filter_ack_str == 'true':
                filter_ack_bool = True
            elif filter_ack_str == 'false':
                filter_ack_bool = False

            if filter_ack_bool is not None:
                # Querying nested properties requires dot notation
                where_clauses.append("c.adminReview.acknowledged = @ack")
                parameters.append({"name": "@ack", "value": filter_ack_bool})

            # --- Construct Full Queries ---
            if where_clauses:
                query_suffix = " WHERE " + " AND ".join(where_clauses)
                base_query += query_suffix
                count_query += query_suffix

            # Add Ordering (e.g., by timestamp descending) - adjust field if needed
            base_query += " ORDER BY c.timestamp DESC" # Important for consistent pagination

            # Add Pagination
            base_query += " OFFSET @offset LIMIT @limit"
            parameters.extend([
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": page_size}
            ])

            # --- Execute Queries ---
            # Count Query (first, to know total pages)
            total_count_result = list(feedback_container.query_items(
                query=count_query,
                parameters=parameters[:-2], # Exclude offset/limit params for count
                enable_cross_partition_query=True
            ))
            total_count = total_count_result[0] if total_count_result else 0

            # Data Query
            items = list(feedback_container.query_items(
                query=base_query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            # --- Format Results ---
            results = []
            for f in items:
                results.append({
                    "id": f["id"],
                    "userId": f.get("userId"),
                    "prompt": f.get("prompt"),
                    "aiResponse": f.get("aiResponse"),
                    "feedbackType": f.get("feedbackType"),
                    "reason": f.get("reason"),
                    "timestamp": f.get("timestamp"),
                    "adminReview": f.get("adminReview", {})
                })

            # --- Return JSON Response ---
            return jsonify({
                "feedback": results,
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": math.ceil(total_count / page_size)
            })

        except Exception as e:
             print(f"Error fetching feedback for review: {e}")
             # Log the full exception traceback if possible
             import traceback
             traceback.print_exc()
             return jsonify({"error": f"Failed to retrieve feedback: {str(e)}"}), 500

    @app.route("/feedback/review/<feedbackId>", methods=["GET"])
    @login_required
    @admin_required
    @enabled_required("enable_user_feedback")
    def feedback_review_get_single(feedbackId):
        """
        Fetch a single feedback item by its ID.
        Needed for the edit modal after switching to pagination.
        """
        try:
            # Assuming feedbackId is the partition key as well
            feedback_doc = feedback_container.read_item(
                item=feedbackId, partition_key=feedbackId
            )

            result = {
                "id": feedback_doc["id"],
                "userId": feedback_doc.get("userId"),
                "prompt": feedback_doc.get("prompt"),
                "aiResponse": feedback_doc.get("aiResponse"),
                "feedbackType": feedback_doc.get("feedbackType"),
                "reason": feedback_doc.get("reason"),
                "timestamp": feedback_doc.get("timestamp"),
                "adminReview": feedback_doc.get("adminReview", {})
            }
            return jsonify(result)

        except CosmosResourceNotFoundError: # Import this if not already done
             return jsonify({"error": "Feedback item not found"}), 404
        except Exception as e:
             print(f"Error fetching single feedback item {feedbackId}: {e}")
             import traceback
             traceback.print_exc()
             return jsonify({"error": f"Failed to retrieve feedback item: {str(e)}"}), 500
        
    @app.route("/feedback/review/<feedbackId>", methods=["PATCH"])
    @login_required
    @admin_required
    @enabled_required("enable_user_feedback")
    def feedback_review_update(feedbackId):
        """
        Patch admin fields: acknowledged, analysisNotes, responseToUser, actionTaken
        """
        data = request.get_json()

        try:
             # Assume feedbackId is the partition key
            feedback_doc = feedback_container.read_item(
                item=feedbackId, partition_key=feedbackId
            )
        except CosmosResourceNotFoundError:
            return jsonify({"error": "Feedback not found"}), 404
        except Exception as e:
            print(f"Error reading feedback item {feedbackId} for update: {e}")
            return jsonify({"error": "Failed to read feedback item"}), 500


        admin_review_data = feedback_doc.get("adminReview", {}) # Get current or default dict

        # Update fields based on request data
        admin_review_data["acknowledged"] = data.get("acknowledged", admin_review_data.get("acknowledged", False))
        admin_review_data["analysisNotes"] = data.get("analysisNotes", admin_review_data.get("analysisNotes"))
        admin_review_data["responseToUser"] = data.get("responseToUser", admin_review_data.get("responseToUser"))
        admin_review_data["actionTaken"] = data.get("actionTaken", admin_review_data.get("actionTaken"))
        admin_review_data["reviewTimestamp"] = datetime.utcnow().isoformat()
        # Optionally add analyzedBy from session user
        # if 'user' in session:
        #     admin_review_data["analyzedBy"] = session['user'].get('oid') or session['user'].get('sub')

        feedback_doc["adminReview"] = admin_review_data # Assign updated dict back

        try:
             feedback_container.upsert_item(feedback_doc)
             return jsonify({"success": True})
        except Exception as e:
             print(f"Error updating feedback item {feedbackId}: {e}")
             return jsonify({"error": "Failed to save changes"}), 500


    @app.route("/feedback/retest/<feedbackId>", methods=["POST"])
    @login_required
    @admin_required
    @enabled_required("enable_user_feedback")
    def feedback_retest(feedbackId):
        """
        Admin retests the prompt. We basically re-run the prompt
        against the current AI chain to see if it's improved.
        """
        data = request.get_json()
        prompt = data.get("prompt")
        if not prompt:
            return jsonify({"error": "Missing prompt"}), 400

        try:
            retestResponse = run_prompt_against_gpt(prompt)
            return jsonify({"retestResponse": retestResponse})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    @app.route("/feedback/my", methods=["GET"])
    @login_required
    @user_required
    @enabled_required("enable_user_feedback")
    def feedback_my():
        """
        Returns the current user's feedback items with server-side pagination and filtering.
        Query Parameters:
            page (int): Page number (default: 1).
            page_size (int): Items per page (default: 10).
            type (str): Filter by feedbackType (Positive, Negative, Neutral).
            ack (str): Filter by acknowledged status ('true', 'false').
        """
        user_id = None
        if "user" in session:
            user_id = session["user"].get("oid") or session["user"].get("sub")
        if not user_id:
            return jsonify({"error": "No user ID found in session"}), 403

        try:
            # --- Pagination Parameters ---
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('page_size', 10))
            if page < 1: page = 1
            if page_size < 1: page_size = 10
            offset = (page - 1) * page_size

            # --- Filtering Parameters ---
            filter_type = request.args.get('type', None)
            filter_ack_str = request.args.get('ack', None) # 'true' or 'false'

            # --- Build Query ---
            query_conditions = ["c.userId = @userId"]
            parameters = [{"name": "@userId", "value": user_id}]

            if filter_type:
                query_conditions.append("c.feedbackType = @type")
                parameters.append({"name": "@type", "value": filter_type})

            if filter_ack_str is not None:
                filter_ack_bool = filter_ack_str.lower() == 'true'
                # Query Cosmos DB boolean. Assumes adminReview.acknowledged is stored as boolean
                # Adjust the path if 'adminReview' might not exist (use IS_DEFINED or check existence)
                # For simplicity, assuming adminReview object exists if filtering by ack status
                query_conditions.append("c.adminReview.acknowledged = @ackStatus")
                parameters.append({"name": "@ackStatus", "value": filter_ack_bool})
                # More robust: query_conditions.append("(IS_DEFINED(c.adminReview) ? c.adminReview.acknowledged : false) = @ackStatus") if false should be default

            # Base query structure
            where_clause = " WHERE " + " AND ".join(query_conditions)
            query = f"SELECT * FROM c {where_clause} ORDER BY c.timestamp DESC"
            count_query = f"SELECT VALUE COUNT(1) FROM c {where_clause}"

            # --- Execute Queries ---
            # 1. Get total count
            count_results = list(feedback_container.query_items(
                query=count_query,
                parameters=parameters,
                enable_cross_partition_query=True # Adjust based on partition key
            ))
            total_count = count_results[0] if count_results else 0

            # 2. Get paginated items
            all_matching_items = list(feedback_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            # Apply pagination slicing
            paginated_items = all_matching_items[offset : offset + page_size]

            # Format results (as done previously)
            results = []
            for f in paginated_items:
                results.append({
                    "id": f["id"],
                    "userId": f.get("userId"),
                    "prompt": f.get("prompt"),
                    "aiResponse": f.get("aiResponse"),
                    "feedbackType": f.get("feedbackType"),
                    "reason": f.get("reason"),
                    "timestamp": f.get("timestamp"),
                    "adminReview": f.get("adminReview", {}) # Ensure adminReview is an empty dict if missing
                })

            return jsonify({
                "feedback": results,
                "page": page,
                "page_size": page_size,
                "total_count": total_count
            }), 200

        except Exception as e:
            print(f"Error in feedback_my: {str(e)}")
            return jsonify({"error": f"An error occurred while fetching your feedback: {str(e)}"}), 500


def run_prompt_against_gpt(prompt):
    # To do -  Replace with the real logic of your chat pipeline
    # Example: Access your LLM client and run the prompt
    # from your_llm_module import llm_client
    # response = llm_client.invoke(prompt)
    # return response.content
    print(f"Retesting prompt (stub): {prompt}")
    return f"[Retested with current model config] Mock AI response for: '{prompt}'"