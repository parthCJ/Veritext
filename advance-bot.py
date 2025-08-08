import os
import json
import fitz  # PyMuPDF
import io
import re
from PIL import Image
import pytesseract
from groq import Groq
from dotenv import load_dotenv

# Load API Key from .env file
load_dotenv()

def extract_text_from_all_pages(pdf_path):
    """Extracts text and OCRs images from all pages, returning a list of page data."""
    print(f"📖 Processing all pages of '{pdf_path}'...")
    document_pages = []
    try:
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc):
            page_content = ""
            print(f"  - Processing page {page_num + 1}/{len(doc)}...")
            page_content += page.get_text() + "\n"
            image_list = page.get_images(full=True)
            if image_list:
                page_content += "\n--- OCR Text from Images on this Page ---\n"
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image = Image.open(io.BytesIO(image_bytes))
                    page_content += pytesseract.image_to_string(image) + "\n"
            document_pages.append({"page_number": page_num + 1, "content": page_content})
        doc.close()
        print("✅ All pages processed and ready for questions.")
        return document_pages
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        return []

def find_relevant_page(pages_data, question, model_name="llama3-8b-8192"):
    """Acts as a 'search' agent to find the most relevant page number."""
    print("\n--- Step A: Running Smart Search to find relevant page...")
    summary = "\n".join([f"Page {p['page_number']}: {p['content'][:300]}..." for p in pages_data])
    prompt = f"You are a routing assistant. Your job is to find the most relevant page number to answer the user's question based on the page summaries. Prioritize figures/images if mentioned. Respond with ONLY the page number as an integer.\n\n--- Page Summaries ---\n{summary}\n\nUser Question: \"{question}\"\n\nMost relevant page number is:"
    try:
        client = Groq()
        chat_completion = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=model_name, temperature=0.0)
        raw_response = chat_completion.choices[0].message.content
        match = re.search(r'\d+', raw_response)
        if match:
            page_number = int(match.group(0))
            print(f"✅ Smart Search found relevant page: {page_number}")
            return page_number
        else:
            return None
    except Exception as e:
        print(f"❌ Error in smart search step: {e}")
        return None

def get_cited_answer_agent(pages_data, question, model_name="llama3-8b-8192"):
    """Takes page data and a question, and returns a high-fidelity answer with a structured reference."""
    print(f"\n--- Step B: Sending question to Groq model...")
    formatted_pages = "\n\n".join([f"--- Page {p['page_number']} ---\n{p['content']}" for p in pages_data])
    prompt = f"You are a research assistant. Your task is to answer a question based ONLY on the text in <DOCUMENT_CONTEXT>. You are forbidden from using outside knowledge.\n\n<DOCUMENT_CONTEXT>\n{formatted_pages}\n</DOCUMENT_CONTEXT>\n\nYour response MUST be in this format:\n**Answer:**\n[Your answer.]\n\n<EVIDENCE>\n<QUOTE>An exact quote proving your answer.</QUOTE>\n<SOURCE>Page X</SOURCE>\n</EVIDENCE>\n\nCRITICAL RULE: If the answer is not in the document, respond ONLY with: 'The answer could not be found in the provided document.'\n\nUSER QUESTION: {question}"
    try:
        client = Groq()
        chat_completion = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=model_name, temperature=0.0)
        answer = chat_completion.choices[0].message.content
        print("✅ High-quality answer received from Groq.")
        return answer
    except Exception as e:
        print(f"❌ An error occurred with the Groq API call: {e}")
        return "Sorry, I could not process the request to the AI model."

def save_answer_clip(pdf_path, page_number, text_to_find):
    """Finds a text snippet on a PDF page and saves a snapshot of that area."""
    output_filename = f"reference_clip_page_{page_number}.png"
    print(f"💾 Searching for quote to create visual clip...")
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_number - 1)
        search_results = page.search_for(text_to_find, quads=True)
        if search_results:
            clip_coords = search_results[0]
            pix = page.get_pixmap(clip=clip_coords, dpi=200)
            pix.save(output_filename)
            print(f"✅ Saved visual reference to '{output_filename}'")
            return output_filename
        else:
            print("⚠️ Could not find the exact quote on the page to create a clip.")
            return None
        doc.close()
    except Exception as e:
        print(f"❌ Could not save reference clip: {e}")
        return None

def start_chat_session(pdf_file):
    """The main interactive chat loop for a standard terminal."""
    all_pages_data = extract_text_from_all_pages(pdf_file)
    if not all_pages_data:
        print("Could not process the PDF. Exiting.")
        return

    print("\n--- Document analysis complete. You can now ask questions. ---")
    while True:
        try:
            user_question = input("\nYou (type 'quit' to exit): ")
        except KeyboardInterrupt:
            print("\nExiting chat. Goodbye!")
            break
        
        if user_question.lower() in ['quit', 'exit']:
            print("Exiting chat. Goodbye!")
            break
        
        relevant_page_num = find_relevant_page(all_pages_data, user_question)
        if relevant_page_num:
            relevant_page_data = [p for p in all_pages_data if p['page_number'] == relevant_page_num]
            final_answer = get_cited_answer_agent(relevant_page_data, user_question)
            
            print("\nAssistant:")
            print(final_answer)  # <-- REPLACED display() WITH print()
            
            quote_match = re.search(r'<QUOTE>(.*?)</QUOTE>', final_answer, re.DOTALL)
            if quote_match:
                quote = quote_match.group(1).strip()
                saved_clip_file = save_answer_clip(pdf_file, relevant_page_num, quote)
                if saved_clip_file:
                    # --- REPLACED display() WITH A HELPFUL print() MESSAGE ---
                    print(f"\n🖼️  A visual clip has been saved. Please open the file: {saved_clip_file}")
            else:
                print("ℹ️ No <QUOTE> tag was found in the answer to create a visual clip.")
        else:
            print("\nAssistant: Sorry, I couldn't determine a relevant page for that question.")

# --- Main Execution block for a standard Python script ---
if __name__ == "__main__":
    pdf_to_chat = "media/pooling-layes.pdf" # Make sure this PDF is in the same folder
    start_chat_session(pdf_to_chat)