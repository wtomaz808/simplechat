# Simple Chat Application

## Overview

The **Simple Chat Application** is designed to enable users to interact with a generative AI model via a web-based chat interface. It supports **Retrieval-Augmented Generation (RAG)**, allowing users to enhance the AI’s responses with custom data by uploading documents. The application uses **inline temporary file storage** for short-term processing and **Azure AI Search** for long-term document retrieval and storage, enabling efficient hybrid searches. The application is built to run on **Azure App Service** both in **Azure Commercial** and **Azure Government**.

https://github.com/user-attachments/assets/a1045817-e2e4-4336-8a18-d4f83a6a02af

**Important Change**:  

- **Azure OpenAI** and **Bing Search** configuration is now done via the **Admin Settings** page within the application, rather than being stored directly in environment variables (`.env` file). This allows for easier updates and toggling of features like GPT, embeddings, web search (Bing), and image generation at runtime.

![Screenshot: Chat UI](./images/chat.png)

## Features

- **Chat with AI**: Interact with an AI model based on OpenAI's GPT.
- **RAG with Hybrid Search**: Upload documents and perform hybrid searches, retrieving relevant information from your files.
- **Document Management**: Upload, store, and manage multiple versions of documents (personal or group-level).
- **Group Management**: Create and join groups to share access to group-specific documents (RBAC).
- **Ephemeral (Single-Convo) Documents**: Upload temporary documents available only during the current chat session.
- **Azure Cosmos DB**: Stores conversations, documents, and metadata.
- **Azure Cognitive Search**: Facilitates efficient search and retrieval of document data.
- **Azure Document Intelligence**: Extracts data from various document formats, including PDFs, Word documents, and images.
- **Optional Bing Web Search**: Toggle web-search-based augmentation from the Admin Settings.  
- **Optional Image Generation**: Toggle image generation with Azure OpenAI from the Admin Settings.
- **Authentication & RBAC**: Secured via Azure Active Directory (AAD) integration, using MSAL (Microsoft Authentication Library), plus group-based access control and app roles.

![Architecture Diagram](./images/architecture.png)

## Latest Features 
### (v0.191.0)

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

### (v0.190.1)

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

## Technology Stack

- **Flask (Python)**: Web framework for handling requests and rendering web pages.
- **Azure OpenAI**: Used for generating AI responses and creating document embeddings for RAG.
- **Azure Cosmos DB**: For storing conversations, documents, and metadata.
- **Azure Cognitive Search**: Enables document retrieval based on AI-embedded vectors.
- **Azure Document Intelligence**: Extracts text from uploaded documents in various formats.
- **MSAL**: Handles authentication with Azure Active Directory (AAD).

## Demos

### Upload Document

![Upload Document Demo](./images/UploadDocumentDemo.gif)

### Chat with Searching your Documents

![Chat with Searching your Documents Demo](./images/ChatwithSearchingYourDocsDemo.gif)

### Chat with temporary documents in a single conversation

![Chat with Temp Docs](./images/ChatwithTempDocs.gif)

## Setup Instructions

### Initializing Indexes in Azure AI Search

The **Simple Chat Application** uses Azure AI Search to store user (personal) and group documents. You’ll create **two** indexes:

1. **User Index**  
2. **Group Index**  

Both schemas are found in the `artifacts/` folder (`user-index.json` and `group-index.json`).

```
     📁 SimpleChat
     └── 📁 artifacts
         └── user-index.json
         └── group-index.json
```

#### Steps to Initialize the Indexes in the Azure Portal

1. **Access the Azure Portal**  
   - Go to the [Azure Portal](https://portal.azure.com/).  
   - In the search bar, search for **"Azure Cognitive Search"** and select your Azure AI Search resource.

2. **Navigate to Indexes**  
   - In the left-hand menu, select **Indexes** under **Search Management**.
   - Click on **+ Add Index from JSON** to create a new index.

3. **Create Index from JSON**  
   - Open `user-index.json` in your local editor. Copy its JSON and paste into the Azure portal’s **Add Index from JSON** screen.  
   - Do the same for `group-index.json`.

4. **Verify Index Creation**  
   - After creation, you should see `simplechat-user-index` and `simplechat-group-index` listed under Indexes.

### Setting Up Authentication for the Simple Chat Application

The application secures access using **Azure Active Directory**. Users log in with their organizational credentials. Access is further refined with roles (`Owner`, `Admin`, `DocumentManager`, `User`) assigned in your tenant’s **Enterprise Applications**.

1. **Enable App Service Authentication**  
   - In the **App Service** → **Authentication** blade, add **Microsoft** as an identity provider, linking to your Azure AD app registration.  
   - Require authentication so only logged-in users can access the app.

2. **App Registration**  
   - In **Azure AD** → **App Registrations**, find your registration (e.g., `my-webapp-simplechat`).  
   - Configure Redirect URIs (e.g., `https://my-webapp.azurewebsites.net/getAToken`) and permissions.  
   - Grant admin consent if needed (e.g., `User.Read`, `User.ReadBasic.All`, etc.).

3. **Assign Users in Enterprise Applications**  
   - Under **Enterprise Applications** → **Users and groups**, assign users or groups to the app, specifying the appropriate role.

### Configured Permissions

Your application is authorized to call APIs when granted permissions by users or administrators. Below are the currently configured permissions for **Microsoft Graph** in this application.

| API / Permission Name  | Type      | Description                                         |
| ---------------------- | --------- | --------------------------------------------------- |
| **email**              | Delegated | View users' email address                           |
| **offline_access**     | Delegated | Maintain access to data you have given it access to |
| **openid**             | Delegated | Sign users in                                       |
| **People.Read.All**    | Delegated | Read all users' relevant people lists               |
| **profile**            | Delegated | View users' basic profile                           |
| **User.Read**          | Delegated | Sign in and read user profile                       |
| **User.ReadBasic.All** | Delegated | Read all users' basic profiles                      |

### Granting Admin Consent

For the permissions that require **admin consent**, ensure that an administrator grants consent by:

1. Navigating to **Azure Portal > Azure Active Directory**.
2. Selecting **App registrations** and locating your registered application.
3. Clicking on **API permissions**.
4. Selecting **Grant admin consent for [your tenant]**.
5. Confirming the operation.

### Adding Additional Permissions

If your application requires further permissions:

1. Click **+ Add a permission**.
2. Select **Microsoft Graph** or another API.
3. Choose either **Delegated permissions** (acting on behalf of the user) or **Application permissions** (acting as a service).
4. Select the required permissions and **Add** them.
5. If admin consent is required, follow the **Granting Admin Consent** steps above.

By ensuring the correct permissions and admin consent, your application can securely interact with Microsoft Graph APIs while respecting user and security policies.
### App Roles

**Description**: App roles are custom roles to assign permissions to users or apps. The application defines and publishes these app roles, which are then interpreted as permissions during authorization.

| Display Name | Description            | Allowed Member Types | Value | State   |
| ------------ | ---------------------- | -------------------- | ----- | ------- |
| **Admins**   | Manage the application | Users/Groups         | Admin | Enabled |
| **Users**    | Normal user            | Users/Groups         | User  | Enabled |

### Adding Users to the Application

To allow users to sign in to your application and automatically be assigned the correct role (Admin or User), you must add these users in the **Enterprise application** that is associated with your **Registered app** in Azure Active Directory:

1. **Go to Azure Active Directory**  
   - In the [Azure Portal](https://portal.azure.com), go to **Azure Active Directory** from the main menu.

2. **Select ‘Enterprise applications’**  
   - Under the **Manage** section in Azure AD, choose **Enterprise applications**.

3. **Locate Your Application**  
   - Find and select the Enterprise application that was automatically created when you registered your app (the name should match or be closely related to the registered app’s name).

4. **Go to ‘Users and groups’**  
   - Under **Manage** for that Enterprise application, select **Users and groups** to manage role assignments.

5. **Click on ‘Add user/group’**  
   - Here, you can choose to add either **individual users** or entire **Azure AD groups** to the application.

6. **Assign the Appropriate Role**  
   - When adding users or groups, you will see the available app roles (e.g., **Admins**, **Users**).  
   - Select the relevant role to ensure the user or group is granted the correct permissions.

7. **Save Your Changes**  
   - Confirm your assignments and click **Assign** (or **Save**) to finalize.

8. **Verification**  
   - Once a user is assigned, they can sign in and be granted the permissions associated with their role in your application.

### Configuring Environment Variables and `.env` File

While **Azure OpenAI** (GPT, Embeddings, Image Gen) and **Bing Search** are now configured via the in-app **Admin Settings**, you still need some basic environment variables for the rest of the services. These are typically set in the Azure Portal under **Configuration** or uploaded via a `.env` file.

1. **Modify `example.env`**  
   - Rename `example.env` to `.env`.  
   - Update placeholders for **Azure Cosmos DB**, **Azure Cognitive Search**, **Azure Document Intelligence**, and **AAD** values.  
   - **Omit** any direct references to Azure OpenAI or Bing Search here, since these are now set in the admin UI.

2. **Upload `.env` to Azure App Service**  
   - In VS Code, use **"Azure App Service: Upload Local Settings"** or manually copy the env keys into **App Service → Configuration**.

> **Note**: Keep secrets out of source control. Use Azure Key Vault or the App Service Settings blade to store any credentials for production scenarios.

#### Alternate Method: Upload Environment Variables Using JSON Configuration

If you prefer, you can update your environment variables directly in the Azure Portal using the **Advanced Edit** feature. This method allows you to paste a JSON configuration, which can be especially useful for bulk updates or when setting up a new environment.

#### Steps:

1. Navigate to your **App Service** in the [Azure Portal](https://portal.azure.com/).
2. Go to **Settings** > **Configuration**.
3. Click on the **Application settings** tab.
4. Click **Advanced edit**.
5. Copy and paste the JSON configuration below into the **Advanced Edit** window.
6. Click **OK**, then **Save** to apply the changes.

#### JSON Configuration:

> [!NOTE]
>
> Replace the placeholder values (e.g., `MICROSOFT_PROVIDER_AUTHENTICATION_SECRET`, `FLASK_KEY`, etc.) with your actual configuration values.

```json
[
    { "name": "MICROSOFT_PROVIDER_AUTHENTICATION_SECRET", "value": "<your-authentication-secret>", "slotSetting": true },
    { "name": "WEBSITE_AUTH_AAD_ALLOWED_TENANTS", "value": "<your-allowed-tenant-id>", "slotSetting": false },
    { "name": "SCM_DO_BUILD_DURING_DEPLOYMENT", "value": "true", "slotSetting": false },
    { "name": "WEBSITE_HTTPLOGGING_RETENTION_DAYS", "value": "7", "slotSetting": false },
    { "name": "APPINSIGHTS_INSTRUMENTATIONKEY", "value": "<your-instrumentation-key>", "slotSetting": false },
    { "name": "APPLICATIONINSIGHTS_CONNECTION_STRING", "value": "InstrumentationKey=<your-instrumentation-key>;IngestionEndpoint=<your-ingestion-endpoint>;LiveEndpoint=<your-live-endpoint>;ApplicationId=<your-application-id>", "slotSetting": false },
    { "name": "ApplicationInsightsAgent_EXTENSION_VERSION", "value": "~3", "slotSetting": false },
    { "name": "APPLICATIONINSIGHTSAGENT_EXTENSION_ENABLED", "value": "true", "slotSetting": false },
    { "name": "XDT_MicrosoftApplicationInsights_Mode", "value": "default", "slotSetting": false },
    { "name": "APPINSIGHTS_PROFILERFEATURE_VERSION", "value": "1.0.0", "slotSetting": false },
    { "name": "APPINSIGHTS_SNAPSHOTFEATURE_VERSION", "value": "1.0.0", "slotSetting": false },
    { "name": "SnapshotDebugger_EXTENSION_VERSION", "value": "disabled", "slotSetting": false },
    { "name": "InstrumentationEngine_EXTENSION_VERSION", "value": "disabled", "slotSetting": false },
    { "name": "XDT_MicrosoftApplicationInsights_BaseExtensions", "value": "disabled", "slotSetting": false },
    { "name": "XDT_MicrosoftApplicationInsights_PreemptSdk", "value": "disabled", "slotSetting": false },
    { "name": "AZURE_COSMOS_ENDPOINT", "value": "<your-cosmosdb-endpoint>", "slotSetting": false },
    { "name": "AZURE_COSMOS_KEY", "value": "<your-cosmosdb-key>", "slotSetting": false },
    { "name": "AZURE_COSMOS_DB_NAME", "value": "SimpleChat", "slotSetting": false },
    { "name": "AZURE_COSMOS_DOCUMENTS_CONTAINER_NAME", "value": "documents", "slotSetting": false },
    { "name": "AZURE_COSMOS_CONVERSATIONS_CONTAINER_NAME", "value": "conversations", "slotSetting": false },
    { "name": "AZURE_COSMOS_LOGS_CONTAINER_NAME", "value": "logs", "slotSetting": false },
    { "name": "AZURE_AI_SEARCH_ENDPOINT", "value": "<your-ai-search-endpoint>", "slotSetting": false },
    { "name": "AZURE_AI_SEARCH_KEY", "value": "<your-ai-search-key>", "slotSetting": false },
    { "name": "AZURE_AI_SEARCH_USER_INDEX", "value": "simplechat-user-index", "slotSetting": false },
    { "name": "AZURE_AI_SEARCH_GROUP_INDEX", "value": "simplechat-group-index", "slotSetting": false },
    { "name": "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "value": "<your-document-intelligence-endpoint>", "slotSetting": false },
    { "name": "AZURE_DOCUMENT_INTELLIGENCE_KEY", "value": "<your-document-intelligence-key>", "slotSetting": false },
    { "name": "BING_SEARCH_ENDPOINT", "value": "https://api.bing.microsoft.com/", "slotSetting": false },
    { "name": "CLIENT_ID", "value": "<your-client-id>", "slotSetting": false },
    { "name": "TENANT_ID", "value": "<your-tenant-id>", "slotSetting": false },
    { "name": "SECRET_KEY", "value": "<your-32-character-secret>", "slotSetting": false }
]

```

#### Notes:

- The `slotSetting` flag is set to `true` for sensitive or environment-specific variables (e.g., secrets). This ensures that these variables are not affected by swapping deployment slots (e.g., staging and production).

By using the **Advanced Edit** function and pasting this JSON, you can easily manage and update your environment variables in a single step.

![Advanced Edit](./images/advanced_edit_env.png)

### Installing and Deploying

1. **Clone the Repo**  
   
   ```bash
   git clone https://github.com/your-repo/SimpleChat.git
   cd SimpleChat

2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

3. **Deploy to Azure App Service**
    You can use **Azure CLI** or **VS Code** deployment.

#### Deploying via VS Code

1. Install the **Azure Tools** VS Code Extension.
2. Sign in to your Azure account in VS Code.
3. Right-click your project folder → **Deploy to Web App**.
4. Select or create an **Azure App Service**.
5. Wait for deployment to complete.
6. Upload your `.env` or configure application settings in the Azure Portal.

### Running the Application

- **Locally** (for testing):

  ```bash
  flask run
  ```

  Then open [http://localhost:5000](http://localhost:5000/) in your browser.

- **Azure**: Once deployed, open your `https://<app_name>.azurewebsites.net`.

### Admin Settings Configuration

After deployment and login (with a role of Admin or Owner), navigate to `Admin Settings` in the navigation bar:

1. **General**: Set application title, toggle show/hide logo, customize the landing page text.
2. **GPT**: Provide the Azure OpenAI GPT endpoint, choose between “Key” or “Managed Identity,” and select your model deployment.
3. **Embeddings**: Provide the Azure OpenAI Embedding endpoint and select the embedding model deployment.
4. **Image Generation** (optional): Enable to add an “Image” button in chat for AI image generation.
5. **Web Search** (Bing): Toggle to enable or disable web-based augmentation with Bing Search.
6. **External APIs** (optional): If you have custom chunking or embedding endpoints, set them here.
7. **Other**: Additional limits (max file size, conversation history limit, default system prompt, etc.).

Changes are stored in your Azure Cosmos DB’s configuration container. Once saved, the new settings are applied almost immediately, without editing `.env`.

### Azure Government Configuration

For deployments in **Azure Government**, ensure that the endpoints for **Azure Cosmos DB**, **Azure Cognitive Search**, **Azure Document Intelligence**, etc., use the `.azure.us` suffix (or region-specific endpoints).

## Usage

1. **Login**: Users must log in via Azure Active Directory.

2. **Chat**: Start a conversation with the AI or retrieve previous conversations.

3. Upload Documents

    (Personal or Group):

   - Personal documents are indexed in `simplechat-user-index`.
   - Group documents are indexed in `simplechat-group-index` and only visible to group members.

4. **Toggle Hybrid Search**: Optionally switch on the “Search Documents” button to retrieve context from your docs.

5. **Upload Ephemeral Documents**: Files that live for one conversation only (not in Cognitive Search).

6. **Bing Web Search** (optional): Toggle “Search the Web” for external augmentation.

7. **Image Generation** (optional): Enable “Image” mode to generate images via Azure OpenAI.

8. Groups

   :

   - Create or join existing groups; each group has an owner and optional admins.
   - Switch to the “active group” to see that group’s documents.

### User Workflow

1. **Login** via Azure AD → The user is assigned a role.
2. **Choose Group**: If applicable, pick or set an active group.
3. **Chat**: Compose messages in the chat UI.
4. **Attach Docs**: Upload personal or group docs to store or ephemeral docs for a single conversation.
5. **Hybrid Search**: Enable searching your personal or group docs for context.
6. **Review Past Chats**: The user can revisit conversation history stored in Azure Cosmos DB.
