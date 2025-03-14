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
    """
    Extracts text page-by-page using Azure Document Intelligence "prebuilt-read" 
    and returns a list of dicts, each containing page_number and content.
    """
    try:
        with open(file_path, "rb") as f:
            document_intelligence_client = CLIENTS['document_intelligence_client']
            poller = document_intelligence_client.begin_analyze_document(
                model_id="prebuilt-read",
                document=f
            )

        max_wait_time = 600
        start_time = time.time()
        time.sleep(3)

        while True:
            status = poller.status()
            if status in ["succeeded", "failed", "canceled"]:
                break
            if time.time() - start_time > max_wait_time:
                raise TimeoutError("Document analysis took too long.")
            time.sleep(10)

        result = poller.result()

        # Build a list of pages. Each element is {"page_number": int, "content": str}
        pages_data = []

        if result.pages:
            for page in result.pages:
                page_number = page.page_number
                # Build text for this page by combining all lines
                page_text = "\n".join(line.content for line in page.lines)
                pages_data.append({
                    "page_number": page_number,
                    "content": page_text
                })
        else:
            # Fallback if result.pages is empty but result.content is present
            # This may happen if the doc is recognized as a single chunk
            # or a scenario where lines/pages were not delineated
            pages_data.append({
                "page_number": 1,
                "content": result.content if result.content else ""
            })

        return pages_data

    except HttpResponseError as e:
        raise e
    except Exception as e:
        raise e


def extract_table_file(file_path, file_ext):
    try:
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xls', '.xlsx']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file extension for table extraction.")
        
        table_html = df.to_html(index=False, classes='table table-striped table-bordered')
        return table_html
    except Exception as e:
        raise

def extract_pdf_metadata(pdf_path):
    """
    Returns a tuple (title, author, subject, keywords) from the given PDF, using PyMuPDF.
    """
    try:
        with fitz.open(pdf_path) as doc:
            meta = doc.metadata
            pdf_title = meta.get("title", "")
            pdf_author = meta.get("author", "")
            pdf_subject = meta.get("subject", "")
            pdf_keywords = meta.get("keywords", "")

            return pdf_title, pdf_author, pdf_subject, pdf_keywords

    except Exception as e:
        print(f"Error extracting PDF metadata: {e}")
        return "", "", "", ""
    
def extract_docx_metadata(docx_path):
    """
    Returns a tuple (title, author) from the given DOCX, using python-docx.
    """
    try:
        doc = docx.Document(docx_path)
        core_props = doc.core_properties
        doc_title = core_props.title or ''
        doc_author = core_props.author or ''
        return doc_title, doc_author
    except Exception as e:
        print(f"Error extracting DOCX metadata: {e}")
        return '', ''

def parse_authors(author_input):
    """
    Converts any input (None, string, list, comma-delimited, etc.)
    into a list of author strings.
    """
    if not author_input:
        # Covers None or empty string
        return []

    # If it's already a list, just return it (with stripping)
    if isinstance(author_input, list):
        return [a.strip() for a in author_input if a.strip()]

    # Otherwise, assume it's a string and parse by common delimiters (comma, semicolon)
    if isinstance(author_input, str):
        # e.g. "John Doe, Jane Smith; Bob Brown"
        authors = re.split(r'[;,]', author_input)
        authors = [a.strip() for a in authors if a.strip()]
        return authors

    # If it's some other unexpected data type, fallback to empty
    return []

def convert_word_to_pdf(input_path: str, output_path: str):
    """
    Convert Word (.docx) file to PDF using the docx2pdf library.
    """
    try:
        convert(input_path, output_path)
        print(f"Successfully converted {input_path} to {output_path}")
    except Exception as e:
        print(f"Error converting {input_path} to PDF: {e}")
        raise

def chunk_text(text, chunk_size=2000, overlap=200):
    try:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks
    except Exception as e:
        # Log the exception or handle it as needed
        print(f"Error in chunk_text: {e}")
        raise e  # Re-raise the exception to propagate it

def generate_embedding(
    text,
    max_retries=5,
    initial_delay=1.0,
    delay_multiplier=2.0
):
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
        if (settings.get('azure_openai_embedding_authentication_type') == 'managed_identity'):
            token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
            embedding_client = AzureOpenAI(
                api_version=settings.get('azure_openai_embedding_api_version'),
                azure_endpoint=settings.get('azure_openai_embedding_endpoint'),
                azure_ad_token_provider=token_provider
            )
        
            embedding_model_obj = settings.get('embedding_model', {})
            if embedding_model_obj and embedding_model_obj.get('selected'):
                selected_embedding_model = embedding_model_obj['selected'][0]
                embedding_model = selected_embedding_model['deploymentName']
        else:
            embedding_client = AzureOpenAI(
                api_version=settings.get('azure_openai_embedding_api_version'),
                azure_endpoint=settings.get('azure_openai_embedding_endpoint'),
                api_key=settings.get('azure_openai_embedding_key')
            )
            
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

            embedding = response.data[0].embedding
            return embedding

        except RateLimitError as e:
            retries += 1
            if retries > max_retries:
                return None

            wait_time = current_delay * random.uniform(1.0, 1.5)
            time.sleep(wait_time)
            current_delay *= delay_multiplier

        except Exception as e:
            return None