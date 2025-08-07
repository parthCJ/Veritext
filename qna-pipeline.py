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

# --- HYBRID TEXT & IMAGE EXTRACTION FUNCTION ---
def extract_text_from_all_pages(pdf_path):
    """
    Extracts text and OCRs images from all pages, returning a list of page data.
    """
    print(f"📖 Processing all pages of '{pdf_path}'...")
    document_pages = []
    try:
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc):
            page_content = ""
            print(f"  - Processing page {page_num + 1}/{len(doc)}...")
            
            # 1. Get standard text
            page_content += page.get_text() + "\n"

            # 2. Find and OCR embedded images
            image_list = page.get_images(full=True)
            if image_list:
                page_content += "\n--- OCR Text from Images on this Page ---\n"
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    image = Image.open(io.BytesIO(image_bytes))
                    page_content += pytesseract.image_to_string(image) + "\n"
            
            document_pages.append({
                "page_number": page_num + 1,
                "content": page_content
            })

        doc.close()
        print("✅ All pages processed.")
        return document_pages

    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        return []

# --- FINAL Q&A AGENT with Citations ---
# --- FINAL Q&A AGENT with Clearer, Quoted References ---

def get_cited_answer_agent(pages_data, question, model_name="llama3-8b-8192"):
    """
    Takes page data and a question, and returns a detailed answer with citations,
    but only considers the first 4000 characters of the document.
    """
    print(f"\n🤖 Sending question to Groq model (with 4000 character limit)...")
    
    # Format the page content for the prompt
    formatted_pages = "\n\n".join(
        [f"--- Page {p['page_number']} ---\n{p['content']}" for p in pages_data]
    )

    # The prompt is the same, but we apply the slice to the variable below
    prompt = f"""
    You are an expert research assistant. Your task is to answer the user's question based ONLY on the provided text from the document pages below.

    Your answer must follow these rules:
    1.  Be comprehensive and directly answer the question.
    2.  You MUST cite the page number for the information you use in your answer. Use the format [Page X].
    3.  If the information is found within the OCR'd text from a figure or diagram, explicitly mention it.
    4.  If you cannot find the answer in the text, you must respond with "The answer could not be found in the provided document."

    --- DOCUMENT PAGES (First 4000 characters only) ---
    {formatted_pages[:4000]} 
    ---

    QUESTION: {question}
    """
    
    try:
        client = Groq()
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model_name,
            temperature=0.1 
        )
        answer = chat_completion.choices[0].message.content
        print("✅ Answer received from Groq.")
        return answer
    except Exception as e:
        print(f"❌ An error occurred with the Groq API call: {e}")
        return "Sorry, I could not process the request to the AI model."
    


# --- Main Execution ---
if __name__ == "__main__":
    pdf_file = "lemon and orange disease classifications.pdf"
    
    # 1. Extract all content from the PDF
    all_pages_data = extract_text_from_all_pages(pdf_file)
    
    if all_pages_data:
        # 2. Ask a question and get a cited answer
        user_question = "What machine learning classifiers were used in this study, and which one performed best for oranges?"
        
        final_answer = get_cited_answer_agent(all_pages_data, user_question)
        
        print("\n--- Question ---")
        print(user_question)
        print("\n--- Answer from AI Assistant ---")
        print(final_answer)