import os
import json
import fitz  # PyMuPDF
import io
from PIL import Image
import pytesseract
from groq import Groq
from dotenv import load_dotenv

# Load API Key from .env file
load_dotenv()

def generate_metadata_agent(text, model_name="llama3-8b-8192"):
    print(f"\n🤖 Sending full document text to Groq model: {model_name}...")
    try:
        client = Groq()
        prompt = f"""
        You are a data extraction bot. Analyze the following document text, which includes text from paragraphs and from images across all pages, and extract key metadata. Your output MUST be a valid JSON object with keys for "title", "author", "company_name", "publication_date", "document_type", and "key_topics" and the summary also of the whole pdf. If a field is not available, return null. Do not include any text before or after the JSON.

        DOCUMENT TEXT:
        ---
        {text[:4000]}
        ---
        """
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model_name,
            response_format={"type": "json_object"},
            temperature=0.0
        )
        response_json_string = chat_completion.choices[0].message.content
        print("✅ Metadata received from Groq.")
        return json.loads(response_json_string)
    except Exception as e:
        print(f" An error occurred with the Groq API call: {e}")
        return None

# --- UPDATED HYBRID EXTRACTION FUNCTION ---
def extract_text_from_all_pages(pdf_path):
    """
    Extracts standard text and performs OCR on embedded images from ALL pages of a PDF.
    """
    print(f"📖 Processing all pages of '{pdf_path}' with hybrid method...")
    full_document_text = ""
    try:
        doc = fitz.open(pdf_path)
        
        for page_num, page in enumerate(doc):
            print(f"  - Processing page {page_num + 1}/{len(doc)}...")
            
            # 1. Get standard text (no changes here)
            full_document_text += page.get_text() + "\n"

            # 2. Find and OCR embedded images
            image_list = page.get_images(full=True)
            if image_list:
                print(f"  🖼️ Found {len(image_list)} image(s) on page {page_num + 1}. Running OCR...")
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # --- THIS IS THE NEW PART ---
                    # Perform OCR and store the result in a variable
                    ocr_text = pytesseract.image_to_string(image)
                    
                    # Print the OCR text so you can see it
                    print(f"\n    --- OCR Result from Image {img_index + 1} on Page {page_num + 1} ---")
                    print(ocr_text)
                    print("    ------------------------------------------")

                    # Add the OCR text to the main variable
                    full_document_text += ocr_text + "\n"

        doc.close()
        print("\n✅ All pages processed.")
        return full_document_text

    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        return None
    
# --- Main Execution ---
if __name__ == "__main__":
    pdf_file = "lemon and orange disease classifications.pdf"
     
    full_text = extract_text_from_all_pages(pdf_file)
    
    if full_text:
        generated_metadata = generate_metadata_agent(full_text)
        
        if generated_metadata:
            print("\n--- METADATA FROM FULL DOCUMENT ---")
            print(json.dumps(generated_metadata, indent=2))