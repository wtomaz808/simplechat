<!-- BEGIN RELEASE_NOTES.MD BLOCK -->

# Feature Release
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