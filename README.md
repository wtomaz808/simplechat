<!-- BEGIN README.MD BLOCK -->

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
- **Optional Content Safety**: Toggle content safety to analyze all user messages before they are sent to any service. Provides access to Admin and User specific Safety Violation pages.
- **Optional Feedback System**: Toggle feedback for users to submit feedback on AI generated content. Provide access to Admin and user specific Feedback pages.
- **Optional Bing Web Search**: Toggle web-search-based augmentation from the Admin Settings.  
- **Optional Image Generation**: Toggle image generation with Azure OpenAI from the Admin Settings.
- **Authentication & RBAC**: Secured via Azure Active Directory (AAD) integration, using MSAL (Microsoft Authentication Library), managed identities, plus group-based access control and app roles.

![Architecture Diagram](./images/architecture.png)

## Latest Features 
Below is a suggested “What’s New” or “Latest Features” section you can add to your README (or Release Notes) based on the diffs provided. Feel free to adjust the version number, headings, or wording to match your project’s style.

### (v0.202.21)

- **Azure Government Support**:

  - Introduced an `AZURE_ENVIRONMENT` variable (e.g. `"public"` or `"usgovernment"`) and logic to handle separate authority hosts, resource managers, and credential scopes.

  ```
  # Azure Cosmos DB
  AZURE_COSMOS_ENDPOINT="<your-cosmosdb-endpoint>"
  AZURE_COSMOS_KEY="<your-cosmosdb-key>"
  AZURE_COSMOS_AUTHENTICATION_TYPE="key" # key or managed_identity
  
  # Azure Bing Search
  BING_SEARCH_ENDPOINT="https://api.bing.microsoft.com/"
  
  # Azure AD Authentication
  CLIENT_ID="<your-client-id>"
  TENANT_ID="<your-tenant-id>"
  AZURE_ENVIRONMENT="public" #public, usgovernment
  SECRET_KEY="32-characters" # Example - "YouSh0uldGener8teYour0wnSecr3tKey!", import secrets; print(secrets.token_urlsafe(32))
  ```

- **Admin Settings Overhaul**:

  - **Route & UI**: Added `route_backend_settings.py` and significantly expanded `admin_settings.html` to configure GPT, Embeddings, Image Gen, Content Safety, Web Search, AI Search, and Document Intelligence—all from a single Admin page.
  - **APIM Toggles**: Each service (GPT, Embeddings, Image Generation, Content Safety, etc.) can now be routed through Azure API Management instead of direct endpoints by switching a toggle.
  - **“Test Connection” Buttons**: Each service (GPT, Embeddings, Image Generation, Content Safety, Bing Web Search, Azure AI Search, and Document Intelligence) now has a dedicated “Test Connection” button that performs a live connectivity check.

- **Improved Safety Features**:

  - New pages/sections for “Admin Safety Violations” vs. “My Safety Violations.”

- **Miscellaneous Frontend & Template Updates**:

  - All templates now reference an `app_settings.app_title` for a dynamic page title.
  - Enhanced navigation and labeling in “My Documents,” “My Groups,” and “Profile” pages.

#### Bug Fixes

- **Conversation Pipeline**:
  - Removed the `"image"` role from the allowed conversation roles to streamline message handling.
- **Group Management**:
  - Now correctly passes and references the current user’s ID in various group actions.

## Release Notes
For a detailed list of features released by version, please refer to the [Release Notes](./RELEASE_NOTES.md).

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

### Provision Azure Resources

For a quick estimate of monthly costs based on our recommended baseline SKUs for a Demo/POV/MVP solution, check out the [Azure Pricing Calculator](https://azure.com/e/11e3a66700924f248722186c089b275c). Below are the services and SKUs reflected in that link:

> [!IMPORTANT]
>
> The following recommended SKUS are for Development/Demo/POC/MVP. You will need to scale services appropriately as you increase user counts or move into Production

| Service Type           | Description                                                  |
| ---------------------- | ------------------------------------------------------------ |
| Front End App Service  | Basic Tier; 1 B1 (1 Core(s), 1.75 GB RAM, 10 GB Storage) x 730 Hours; Windows OS; 0 SNI SSL Connections; 0 IP SSL Connections; 0 Custom Domains; 0 Standard SLL Certificates; 0 Wildcard SSL Certificates |
| Azure OpenAI GPT Model | Language Models, Standard (On-Demand), GPT-4o US/EU Data Zones, 10,000 x 1,000 input tokens, 3,000 x 1,000 output tokens |
| Azure OpenAI Embedding | Embedding Models, Text-Embedding-3-Small, 1,000,000 x 1,000 Tokens |
| Azure OpenAI Image Gen | Image Models, Dall-E-3, 1 x 100 Standard 1024 x 1024 images, 1 x 100 Standard 1024 x 1792 images, 1 x 100 HD 1024 x 1024 images, 1 x 100 HD 1024 x 1792 images |
| Azure AI Search        | Standard S1, 1 Unit(s), 360 Hours, 10K semantic queries      |
| Content Safety         | Azure AI Content Safety, Standard: 10 x 1,000 text records and 1 x 1,000 images included per month |
| Document Intelligence  | Azure Form Recognizer, Pay as you go, S0: 0 x 1,000 Custom pages, 1 x 1,000 Pre-built pages, 1 x 1,000 Read pages, 1 x 1,000 Add-on pages, 1 x 1,000 Query pages |
| Bing Search            | Bing Search, S1 tier: 1,000 transactions                     |
| Azure Cosmos DB        | Azure Cosmos DB for NoSQL (RU), Autoscale provisioned throughput, Always-free quantity disabled, Pay as you go, Single Region Write (Single-Master) - East US (Write Region), 1,000 RU/s x 730 Hours x 30% Avg Utilization x 1.5 Autoscale factor, 100 GB transactional storage, Analytical storage disabled, 2 copies of periodic backup storage |

> **Note**: Pricing is subject to change and may vary based on your usage, region, and specific configuration. Always confirm with the official Azure Pricing Calculator and your Azure subscription details for the most accurate cost estimates.

1. **Create or Select a Resource Group**  
   - It’s often easiest to group all resources together under one Azure Resource Group (e.g., `rg-simple-chat`).  
   - For best performance, match regions as shown above (e.g., `East US` for Azure OpenAI, `West US` for App Service) or adjust to your local region needs.
2. **Deploy App Service**  
   - Create an **Azure App Service**: 
     - Publish = **Code**
     - Operating system = **Linux**
     - Linux Plan = Use **P0v3**
     - Zone redundancy = **Disabled**
   - After creation, note the **App Name** and **URL** (e.g., `https://my-simplechat-app.azurewebsites.net`).
3. **Deploy Azure OpenAI**  
   - Create a **Standard S0**. 
   - Deploy one or more **Azure OpenAI** resources in whichever region best supports your requirements.
   - Enable the necessary 
     - **GPT** model (`gpt-4o` but you can use any GPT or o level model)
     - **Embedding** model (`text-embedding-3-small`), 
     - **Image Generation** (`DALL-E 3`).  
   - If using **Managed Identity**, make sure to assign the App Service the correct role in your Azure OpenAI resource.
4. **Deploy Azure AI Search**  
   - Create a **Standard S1**.  
   - [Initialize indexes](#initializing-indexes-in-azure-ai-search) (personal and group).
   - If using **Managed Identity**, make sure to assign the App Service the correct role in your Azure OpenAI resource.
5. **Deploy Azure Cosmos DB**  
   - Use **Azure Cosmos DB for NoSQL** with RU-based autoscale (1,000 RU/s)
     - Provisioned throughput.
     - DO NOT APPLY free discount tier (it does not have enough throughput).
     - Uncheck (aka DISABLE) limit total account throughput.
   - Optionally, set up **Managed Identity** authentication if you do not want to store keys.
6. **Deploy Azure AI Document Intelligence**
   1. Create a **Standard S0**.  
   2. If using **Managed Identity**, make sure to assign the App Service the correct role in your Azure OpenAI resource.

7. **Deploy Azure AI Content Safety** (optional)  
   1. Create a **Standard S0**.  
   2. If using **Managed Identity**, make sure to assign the App Service the correct role in your Azure OpenAI resource.

8. **Deploy Bing Search** (optional)  
   1. Create a **Standard S1**.  
   2. Provide that **Bing Search** key in the **App Settings**.


### Configure Environment / `.env` File

- Configure your **App Service** or local `.env` with connection strings, keys, or **Managed Identity** references.  
- Refer to the [Configuration and Environment Variables](#configuring-environment-variables-and-env-file) section for step-by-step instructions or the Advanced Edit JSON approach.

### Proceed with Application-Specific Configuration

Follow the remaining steps in this README for:
- [AAD Integration](#setting-up-authentication-for-the-simple-chat-application)
- [Uploading Index Schemas](#initializing-indexes-in-azure-ai-search)
- [Admin Settings for GPT / Embeddings / Image Generation](#admin-settings-configuration)
- [Deployment Instructions](#installing-and-deploying)

Once your Azure services are provisioned and the environment variables are set, you can deploy the **Simple Chat Application** (via Azure CLI, VS Code, or other preferred methods) and start using it in your Azure subscription.

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
> Replace the placeholder values (e.g., `MICROSOFT_PROVIDER_AUTHENTICATION_SECRET`, `SECRET_KEY`, `APPLICATIONINSIGHTS_CONNECTION_STRING`, `AZURE_COSMOS_ENDPOINT`, `AZURE_COSMOS_KEY`, `AZURE_COSMOS_AUTHENTICATION_TYPE`, `CLIENT_ID`, `TENANT_ID`, `WEBSITE_AUTH_AAD_ALLOWED_TENANTS`) with your actual configuration values.

```json
[
    { "name": "APPLICATIONINSIGHTS_CONNECTION_STRING", "value": "InstrumentationKey=<your-instrumentation-key>;IngestionEndpoint=<your-ingestion-endpoint>;LiveEndpoint=<your-live-endpoint>;ApplicationId=<your-application-id>", "slotSetting": false },
    { "name": "MICROSOFT_PROVIDER_AUTHENTICATION_SECRET", "value": "<your-authentication-secret>", "slotSetting": true },
    { "name": "WEBSITE_AUTH_AAD_ALLOWED_TENANTS", "value": "<your-allowed-tenant-id>", "slotSetting": false },
    { "name": "AZURE_COSMOS_ENDPOINT", "value": "<your-cosmosdb-endpoint>", "slotSetting": false },
    { "name": "AZURE_COSMOS_KEY", "value": "<your-cosmosdb-key>", "slotSetting": false },
    { "name": "AZURE_COSMOS_AUTHENTICATION_TYPE", "value": "key", "slotSetting": false },
    { "name": "CLIENT_ID", "value": "<your-client-id>", "slotSetting": false },
    { "name": "TENANT_ID", "value": "<your-tenant-id>", "slotSetting": false },
    { "name": "SECRET_KEY", "value": "<your-32-character-secret>", "slotSetting": false },
    { "name": "BING_SEARCH_ENDPOINT", "value": "https://api.bing.microsoft.com/", "slotSetting": false },
    { "name": "SCM_DO_BUILD_DURING_DEPLOYMENT", "value": "true", "slotSetting": false },
    { "name": "WEBSITE_HTTPLOGGING_RETENTION_DAYS", "value": "7", "slotSetting": false },
    { "name": "APPINSIGHTS_INSTRUMENTATIONKEY", "value": "<your-instrumentation-key>", "slotSetting": false },
    { "name": "ApplicationInsightsAgent_EXTENSION_VERSION", "value": "~3", "slotSetting": false },
    { "name": "APPLICATIONINSIGHTSAGENT_EXTENSION_ENABLED", "value": "true", "slotSetting": false },
    { "name": "XDT_MicrosoftApplicationInsights_Mode", "value": "default", "slotSetting": false },
    { "name": "APPINSIGHTS_PROFILERFEATURE_VERSION", "value": "1.0.0", "slotSetting": false },
    { "name": "APPINSIGHTS_SNAPSHOTFEATURE_VERSION", "value": "1.0.0", "slotSetting": false },
    { "name": "SnapshotDebugger_EXTENSION_VERSION", "value": "disabled", "slotSetting": false },
    { "name": "InstrumentationEngine_EXTENSION_VERSION", "value": "disabled", "slotSetting": false },
    { "name": "XDT_MicrosoftApplicationInsights_BaseExtensions", "value": "disabled", "slotSetting": false },
    { "name": "XDT_MicrosoftApplicationInsights_PreemptSdk", "value": "disabled", "slotSetting": false }
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

6. **Bing Web Search** (optional): Toggle “Search the Web” for internet augmentation.

7. **Image Generation** (optional): Enable “Image” mode to generate images via Azure OpenAI.

8. Groups
   - Create or join existing groups; each group has an owner and optional admins.
   - Switch to the “active group” to see that group’s documents.

### User Workflow

1. **Login** via Azure AD → The user is assigned a role.
2. **Choose Group**: If applicable, pick or set an active group.
3. **Chat**: Compose messages in the chat UI.
4. **Attach Docs**: Upload personal or group docs to store or ephemeral docs for a single conversation.
5. **Hybrid Search**: Enable searching your personal or group docs for context.
6. **Review Past Chats**: The user can revisit conversation history stored in Azure Cosmos DB.
