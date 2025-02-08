# functions_content.py

from config import *
from functions_settings import *

def extract_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_markdown_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_content_with_azure_di(file_path):
    try:
        with open(file_path, "rb") as f:
            poller = document_intelligence_client.begin_analyze_document(
                model_id="prebuilt-read",
                document=f
            )
        
        # Manual polling to check status periodically
        max_wait_time = 600  # e.g., wait up to 10 minutes
        start_time = time.time()

        #print ("Polling for document analysis status...")
        while True:
            status = poller.status()
            #print(f"Current analysis status: {status}")
            if status in ["succeeded", "failed", "canceled"]:
                #print(f"Analysis completed with status: {status}")
                break
            if time.time() - start_time > max_wait_time:
                #print("Timeout error: Document analysis took too long.")
                raise TimeoutError("Document analysis took too long.")
            time.sleep(30)

        # Once we exit the loop and status is 'succeeded', 'failed', or 'canceled'
        result = poller.result()  # Get the actual result now
        #print(f"Document analysis result: {result}")

        extracted_content = ""

        if result.content:
            extracted_content = result.content
            #print(f"Content extracted successfully from {file_path}.")
            #print(f"Extracted content: {extracted_content[:100]}...")
        else:
            #print("No content extracted from document.")
            for page in result.pages:
                #print(f"Page {page.page_number} has {len(page.lines)} lines.")
                for line in page.lines:
                    extracted_content += line.content + "\n"
                extracted_content += "\n"
                #print(f"Extracted content: {extracted_content[:100]}...")

        #print(f"Extracted content length: {len(extracted_content)}")
        return extracted_content

    except Exception as e:
        #print(f"Error extracting content with Azure DI: {str(e)}")
        raise

def extract_table_file(file_path, file_ext):
    try:
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file extension for table extraction.")
        
        table_html = df.to_html(index=False, classes='table table-striped table-bordered')
        #print(f"Table extracted successfully from {file_path}.")
        return table_html
    except Exception as e:
        #print(f"Error extracting table from file: {str(e)}")
        raise

def chunk_text(text, chunk_size=2000, overlap=200):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    #print(f"Text chunked into {len(chunks)} chunks.")
    return chunks

def generate_embedding(
    text,
    max_retries=5,
    initial_delay=1.0,  # initial delay in seconds for backoff
    delay_multiplier=2.0  # multiplier to increase delay after each retry
):
    #print("Function generate_embedding called")
    #print(f"Text input for embedding (truncated): {text[:100]}...")
    settings = get_settings()

    retries = 0
    current_delay = initial_delay

    enable_image_gen_apim = settings.get('enable_image_gen_apim', False)

    if enable_image_gen_apim:
        embedding_model = settings.get('azure_apim_embedding_deployment')
        embedding_client = AzureOpenAI(
            api_version = settings.get('azure_apim_embedding_api_version'),
            azure_endpoint = settings.get('azure_apim_embedding_endpoint'),
            api_key=settings.get('azure_apim_embedding_subscription_key'))
    else:
        embedding_client = AzureOpenAI(
            api_version=settings.get('azure_openai_embedding_api_version'),
            azure_endpoint=settings.get('azure_openai_embedding_endpoint'),
            api_key=settings.get('azure_openai_embedding_key'))
        
        embedding_model_obj = settings.get('embedding_model', {})
        if embedding_model_obj and embedding_model_obj.get('selected'):
             selected_embedding_model = embedding_model_obj['selected'][0]
             embedding_model = selected_embedding_model['deploymentName']

    while True:
        random_delay = random.uniform(0.5, 2.0)
        time.sleep(random_delay)

        try:
            response = embedding_client.embeddings.create(
                model=embedding_model,
                input=text
            )

            #print("OpenAI API call successful")
            embedding = response.data[0].embedding
            #print(f"Embedding generated successfully: Length {len(embedding)}")
            return embedding

        except RateLimitError as e:
            retries += 1
            if retries > max_retries:
                #print("Max retries reached due to RateLimitError. Returning None.")
                return None

            wait_time = current_delay * random.uniform(1.0, 1.5)
            #print(f"Rate limit reached. Retrying in {wait_time:.2f} seconds...")
            time.sleep(wait_time)
            current_delay *= delay_multiplier  # Exponential backoff

        except Exception as e:
            #print(f"Error in generating embedding: {str(e)}")
            return None