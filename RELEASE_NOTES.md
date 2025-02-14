<!-- BEGIN RELEASE_NOTES.MD BLOCK -->

# Feature Release
## (V0.199.3)

We introduced a robust user feedback system, expanded content-safety features for both admins and end users, added new Cosmos DB containers, and refined route-level permission toggles. These changes help administrators collect feedback on AI responses, manage content safety more seamlessly, and give end users clearer ways to manage their documents, groups, and personal logs. Enjoy the new functionality, and let us know if you have any questions or issues!

1. **New “User Feedback” System**
   - **Thumbs Up / Thumbs Down**: Users can now provide feedback on individual AI responses (when enabled in App Settings)
   - **Frontend Feedback Pages**:
     - **/my_feedback** page shows each user’s submitted feedback.
     - **/admin/feedback_review** page allows admins to review, filter, and manage all feedback.
2. **Extended Content Safety Features**
   - **New “Safety Violations” Page**: Admins can manage safety violations.
   - **New “My Safety Violations” Page**: Users can view their violations and add personal notes to each violation.
3. **New or Updated Database Containers**
   - feedback_container for user feedback.
   - archived_conversations_container / archived_feedback_container / archived_safety_container for long-term archival.
4. **Route-Level Feature Toggles**
   - **enabled_required(setting_key) Decorator**:
     - Dynamically block or allow routes based on an admin setting (e.g., enable_user_documents or enable_group_documents).
     - Reduces scattered if checks; you simply annotate the route.
5. **Conversation & Messaging Improvements**
   - **Unique message_id for Each Chat Message**:
     - Every user, assistant, safety, or image message now includes a message_id.
     - Makes it easier to tie user feedback or safety logs to a specific message.
   - **Public vs. Secret Settings**:
     - Frontend references a public_settings = sanitize_settings_for_user(settings) to avoid the potential to expose secrets on the client side.
6. **UI/UX Tweaks**
   - **Chat Layout Updates**:
     - “Start typing to create a new conversation…” message if none selected.
     - Automatic creation of new conversation when user tries to send a message with no active conversation.
   - **Navigation Bar Adjustments**:
     - Consolidated admin links into a dropdown.
     - “My Account” dropdown for quick access to “My Groups,” “My Feedback,” etc., if enabled.

## (v0.196.9)

1. **Content Safety Integration**
   - **New Safety Tab in Admin Settings**: A dedicated “Safety” section now appears under Admin Settings, allowing you to enable Azure Content Safety, configure its endpoint and key, and test connectivity.
   - **Real-Time Message Scanning**: If Content Safety is enabled, user prompts are scanned for potentially disallowed content. Blocked messages are flagged and a “safety” message is added to the conversation log in place of a normal AI reply.
   - **Admin Safety Logs**: Site admins (with “Admin” role) can view a new “Safety Violations” page (at /admin/safety_violations) showing blocked or flagged messages. Admins can update the status, action taken, or notes on each violation.
2. **Expanded APIM Support for GPT, Embeddings, and Image Generation**
   - **Fine-Grained APIM Toggles**: You can now enable or disable APIM usage independently for GPT, embeddings, and image generation. Each service has its own APIM endpoint, version, and subscription key fields in Admin Settings.
   - **UI-Driven Switching**: Check/uncheck “Enable APIM” to toggle between native Azure OpenAI endpoints or APIM-managed endpoints, all without redeploying the app.
3. **Workspaces & Documents Configuration**
   - **User Documents and Group Documents**: A new “Workspaces” tab in Admin Settings (replacing the old “Web Search” tab) lets you enable or disable user-specific documents and group-based documents.
   - **Group Documents Page**: The front-end for Group Documents now checks whether “Enable My Groups” is turned on. If enabled, members can manage shared group files and see group-level search results.
   - **My Groups & Group Management**: Navigation includes “My Groups” (if group features are enabled). This leads to a new set of pages for viewing groups, managing memberships, transferring ownership, and more.
4. **Search & Extract Tab**
   - **Azure AI Search & Document Intelligence**: Moved Bing Web Search, Azure AI Search, and Azure Document Intelligence settings into a new “Search and Extract” tab (replacing the older “Web Search” tab).
   - **Bing Search Toggle**: If you enable web search, the user can optionally include Bing results in chat queries.
   - **Azure Document Intelligence**: Configure endpoints and keys for file ingestion (OCR, form analysis, etc.) in a more structured place within Admin Settings.
5. **Updated UI & Navigation**
   - **Admin Dropdown**: Admin-specific features (App Settings, Safety Violations, etc.) are grouped in an “Admin” dropdown on the main navbar.
   - **Safety**: For Content Safety (as noted above).
   - **Search & Extract**: For Bing Search, Azure AI Search, and Document Intelligence.
   - **External APIs**: Simplified chunking/embedding form under one collapsible panel.
   - **Minor Styling Adjustments**: Updated top navbar to show/hide “Groups” or “Documents” links based on new toggles (Enable Your Documents, Enable My Groups).

## (v0.191.0)

1. **Azure API Management (APIM) Support**  
   - **New APIM Toggles**: In the Admin Settings, you can now enable or disable APIM usage separately for GPT, embeddings, and image generation.  
   - **APIM Endpoints & Subscription Keys**: For each AI service (GPT, Embeddings, Image Generation), you can specify an APIM endpoint, version, deployment, and subscription key—allowing a unified API gateway approach (e.g., rate limiting, authentication) without changing your core service code.  
   - **Seamless Switching**: A single checkbox (`Enable APIM`) within each tab (GPT, Embeddings, Image Generation) instantly switches the app between native Azure endpoints and APIM-protected endpoints, with no redeployment required.

2. **Enhanced Admin Settings UI**  
   - **Advanced Fields**: Collapsible “Show Advanced” sections for GPT, Embeddings, and Image Generation let you configure API versions or other fine-tuning details only when needed.  
   - **Test Connectivity**: Each service tab (GPT, Embeddings, Image Gen) now has a dedicated “Test Connection” button, providing immediate feedback on whether your settings and credentials are valid.  
   - **Improved UX for Keys**: Updated show/hide password toggles for all key fields (including APIM subscription keys), making it easier to confirm you’ve entered credentials correctly.

3. **External APIs Refreshed**  
   - **New Form Layout**: The “External APIs” tab has been refined for chunking or embedding endpoints outside of Azure OpenAI, aligning the UI design with the rest of the Admin Settings.  
   - **Connection Testing**: A dedicated “Test Connection” button has been added to verify external chunking or embedding services before saving changes.

4. **Miscellaneous Improvements**  
   - **UI Polishing**: Minor styling updates and improved tooltips in Admin Settings to guide first-time users.  
   - **Performance Tweaks**: Reduced initial load time for the Admin Settings page when large model lists are returned from the OpenAI endpoints.  
   - **Logging & Error Handling**: More descriptive error messages and client-side alerts for failed fetches (e.g., if the user tries to fetch GPT models but hasn’t set the endpoint properly).

## v0.191.0

1. **Azure API Management (APIM) Support**  
   - **New APIM Toggles**: In the Admin Settings, you can now enable or disable APIM usage separately for GPT, embeddings, and image generation.  
   - **APIM Endpoints & Subscription Keys**: For each AI service (GPT, Embeddings, Image Generation), you can specify an APIM endpoint, version, deployment, and subscription key—allowing a unified API gateway approach (e.g., rate limiting, authentication) without changing your core service code.  
   - **Seamless Switching**: A single checkbox (`Enable APIM`) within each tab (GPT, Embeddings, Image Generation) instantly switches the app between native Azure endpoints and APIM-protected endpoints, with no redeployment required.

2. **Enhanced Admin Settings UI**  
   - **Advanced Fields**: Collapsible “Show Advanced” sections for GPT, Embeddings, and Image Generation let you configure API versions or other fine-tuning details only when needed.  
   - **Test Connectivity**: Each service tab (GPT, Embeddings, Image Gen) now has a dedicated “Test Connection” button, providing immediate feedback on whether your settings and credentials are valid.  
   - **Improved UX for Keys**: Updated show/hide password toggles for all key fields (including APIM subscription keys), making it easier to confirm you’ve entered credentials correctly.

3. **External APIs Refreshed**  
   - **New Form Layout**: The “External APIs” tab has been refined for chunking or embedding endpoints outside of Azure OpenAI, aligning the UI design with the rest of the Admin Settings.  
   - **Connection Testing**: A dedicated “Test Connection” button has been added to verify external chunking or embedding services before saving changes.

4. **Miscellaneous Improvements**  
   - **UI Polishing**: Minor styling updates and improved tooltips in Admin Settings to guide first-time users.  
   - **Performance Tweaks**: Reduced initial load time for the Admin Settings page when large model lists are returned from the OpenAI endpoints.  
   - **Logging & Error Handling**: More descriptive error messages and client-side alerts for failed fetches (e.g., if the user tries to fetch GPT models but hasn’t set the endpoint properly).

## v0.190.1

1. **Admin Settings UI**  
   - Configure Azure OpenAI GPT, Embeddings, Image Generation, and Bing Search settings directly through an in-app interface (rather than `.env`).  
   - Choose between **key-based** or **managed identity** authentication for GPT, Embeddings, and Image Generation.  
   - Dynamically switch models/deployments without redeploying the app.

2. **Multiple Roles & Group Permissions**  
   - Roles include `Owner`, `Admin`, `DocumentManager`, and `User`.  
   - Group Owners/Admins can invite or remove members, manage documents, and set “active workspace” for group-based search.

3. **One-Click Switching of Active Group**  
   - Users in multiple groups can quickly switch their active group to see group-specific documents and chat references.

4. **Ephemeral Document Upload**  
   - Upload a file for a single conversation. The file is not saved in Azure Cognitive Search; instead, it is only used for the session’s RAG context.

5. **Inline File Previews in Chat**  
   - Files attached to a conversation can be previewed directly from the chat, with text or data displayed in a pop-up.

6. **Optional Bing Web Search**  
   - Administrators can enable or disable web search. When enabled, the user can toggle “Search the Web” while chatting to incorporate Bing results.

7. **Optional Image Generation**  
   - Users can toggle an “Image” button to create images via Azure OpenAI (e.g., DALL·E) when configured in Admin Settings.

8. **App Roles & Enterprise Application**  
   - Provides a robust way to control user access at scale.  
   - Admins can assign roles to new users or entire Azure AD groups.