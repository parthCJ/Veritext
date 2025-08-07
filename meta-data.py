import os
import json
from groq import Groq
from pypdf import PdfReader
from dotenv import load_dotenv


def extract_text_from_pdf(file_path):
    """Extracts raw text content from a PDF file."""
    print(f"📖 Extracting text from '{file_path}'...")
    try:
        reader = PdfReader(file_path)
        pdf_text = "".join(page.extract_text() for page in reader.pages)
        print("✅ Text successfully extracted.")
        return pdf_text
    except Exception as e:
        print(f"❌ Error extracting text: {e}")
        return None


def generate_metadata_agent(pdf_text, model_name="llama3-8b-8192"):
    """Uses a live Groq model to read text and extract metadata."""
    print(f"\n--- Task 1: Generating Metadata with Groq ---")
    print(f"🤖 Sending text to model: {model_name}...")

    try:
        client = Groq()
        prompt_for_metadata = f"""
        You are a highly intelligent data extraction assistant. Your task is to analyze the following document text and identify key metadata points. Do not make up information that is not present in the text. If a field is not available, return null for its value. Your output must be a valid JSON object with the following keys: "title", "author", "company_name", "publication_date", "document_type", and "key_topics" (a list of 3-5 topics). Do not include any explanatory text before or after the JSON object.

        DOCUMENT TEXT:
        ---
        {pdf_text[:4000]}
        ---
        """
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_for_metadata}],
            model=model_name,
            response_format={"type": "json_object"},
            temperature=0.0
        )
        response_json_string = chat_completion.choices[0].message.content
        print("✅ Metadata received from Groq.")
        return json.loads(response_json_string)

    except Exception as e:
        print(f"❌ An error occurred with the Groq API call: {e}")
        return None

if __name__ == "__main__":
    load_dotenv()
    print("🚀 Starting PDF Analysis Pipeline with Groq...")
    
    pdf_file = "LLM articles.pdf"
    document_text = extract_text_from_pdf(pdf_file)

    if document_text:
        # Use the agent to automatically generate the metadata with a live model
        generated_metadata = generate_metadata_agent(document_text)
        
        if generated_metadata:
            print(json.dumps(generated_metadata, indent=2))