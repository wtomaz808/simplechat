from config import *

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
        result = poller.result()

        extracted_content  = ""

        if result.content:
            extracted_content  = result.content
        else:
            for page in result.pages:
                for line in page.lines:
                    extracted_content  += line.content + "\n"
                extracted_content  += "\n"

        print(f"Content extracted successfully from {file_path}.")
        return extracted_content 

    except Exception as e:
        print(f"Error extracting content with Azure DI: {str(e)}")
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
        print(f"Table extracted successfully from {file_path}.")
        return table_html
    except Exception as e:
        print(f"Error extracting table from file: {str(e)}")
        raise

def chunk_text(text, chunk_size=2000, overlap=200):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    print(f"Text chunked into {len(chunks)} chunks.")
    return chunks

def generate_embedding(text):
    print("Function generate_embedding called")
    print(f"Text input for embedding: {text[:100]}...")

    try:
        response = openai.Embedding.create(
            input=text,
            engine=embedding_model
        )
        print("OpenAI API call successful")

        embedding = response['data'][0]['embedding']
        print(f"Embedding generated successfully: Length {len(embedding)}")
        return embedding

    except Exception as e:
        print(f"Error in generating embedding: {str(e)}")
        return None