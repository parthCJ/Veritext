import os
import json
import fitz  # PyMuPDF
import io
import base64
from PIL import Image
import pytesseract
from groq import Groq
from dotenv import load_dotenv

# Load API Key from .env file
load_dotenv()

def extract_text_and_images_from_all_pages(pdf_path):
    """Extracts text and images from all pages, returning a list of page data."""
    print(f"📖 Processing all pages of '{pdf_path}'...")
    document_pages = []
    try:
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            page_images = []
            
            print(f"  - Processing page {page_num + 1}/{len(doc)}...")
            
            # Extract images
            image_list = page.get_images(full=True)
            if image_list:
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Convert to base64 for API
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    
                    # Also do OCR as backup
                    image_pil = Image.open(io.BytesIO(image_bytes))
                    ocr_text = pytesseract.image_to_string(image_pil)
                    
                    page_images.append({
                        "image_base64": image_base64,
                        "ocr_text": ocr_text,
                        "format": base_image["ext"]
                    })
            
            document_pages.append({
                "page_number": page_num + 1,
                "text": page_text,
                "images": page_images
            })
        
        doc.close()
        print("✅ All pages processed and ready for questions.")
        return document_pages
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        return []

def find_relevant_page(pages_data, question, model_name="llama3-8b-8192"):
    """Acts as a 'search' agent to find the most relevant page number."""
    print("\n--- Step A: Finding relevant page...")
    summary = "\n".join([
        f"Page {p['page_number']}: Text preview: {p['text'][:200]}... | Images: {len(p['images'])}"
        for p in pages_data
    ])
    
    prompt = f"""You are a routing assistant. Find the most relevant page number to answer the question.
    
--- Page Summaries ---
{summary}

User Question: "{question}"

Respond with ONLY the page number as an integer."""
    
    try:
        client = Groq()
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model_name,
            temperature=0.0
        )
        page_number = int(chat_completion.choices[0].message.content.strip())
        print(f"✅ Relevant page found: {page_number}")
        return page_number
    except Exception as e:
        print(f"❌ Error in search step: {e}")
        return None

def get_cited_answer_with_vision(page_data, question, model_name="llama-3.2-90b-vision-preview"):
    """
    Uses Groq's vision model to answer questions about text AND images.
    """
    print(f"\n🤖 Sending question with images to vision model...")
    
    # Build message content with text and images
    content = [
        {
            "type": "text",
            "text": f"""You are a research assistant analyzing page {page_data['page_number']} of a document.

Page Text:
{page_data['text']}

Answer this question based on the text and images provided: {question}

Provide:
1. A clear answer
2. Direct quotes or references to images
3. Page number citation"""
        }
    ]
    
    # Add images to the content
    for idx, img_data in enumerate(page_data['images']):
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/{img_data['format']};base64,{img_data['image_base64']}"
            }
        })
        # Add OCR text as context
        content.append({
            "type": "text",
            "text": f"[OCR from Image {idx + 1}]: {img_data['ocr_text']}"
        })
    
    try:
        client = Groq()
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ],
            model=model_name,
            temperature=0.0,
            max_tokens=1024
        )
        answer = chat_completion.choices[0].message.content
        print("✅ Answer received from vision model.")
        return answer
    except Exception as e:
        print(f"❌ Error with vision model: {e}")
        return f"Sorry, I could not process the request: {e}"


if __name__ == "__main__":
    pdf_file = "media/gradient-desceny.pdf"  
    
    all_pages_data = extract_text_and_images_from_all_pages(pdf_file)

    if all_pages_data:
        print("\n--- Document analysis complete. You can now ask questions about text AND images. ---")
        
        while True:
            user_question = input("\nYou (type 'quit' to exit): ")
            
            if user_question.lower() in ['quit', 'exit']:
                print("Exiting chat. Goodbye!")
                break
            
            relevant_page_num = find_relevant_page(all_pages_data, user_question)

            if relevant_page_num:
                relevant_page_data = next(
                    (p for p in all_pages_data if p['page_number'] == relevant_page_num),
                    None
                )
                
                if relevant_page_data:
                    final_answer = get_cited_answer_with_vision(relevant_page_data, user_question)
                    
                    print("\nAssistant:")
                    print(final_answer)
                else:
                    print("\nAssistant: Could not find page data.")
            else:
                print("\nAssistant: Sorry, I couldn't determine a relevant page for that question.")
    else:
        print("Could not process the PDF. Exiting.")