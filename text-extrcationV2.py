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
    print("\n--- Step A: Finding relevant page...")
    summary = "\n".join([f"Page {p['page_number']}: {p['content'][:200]}..." for p in pages_data])
    prompt = f"You are a routing assistant. Your job is to find the most relevant page number to answer the user's question based on the provided page summaries. Respond with ONLY the page number as an integer.\n\n--- Page Summaries ---\n{summary}\n\nUser Question: \"{question}\"\n\nMost relevant page number is:"
    try:
        client = Groq()
        chat_completion = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model=model_name, temperature=0.0)
        page_number = int(chat_completion.choices[0].message.content)
        print(f"✅ Relevant page found: {page_number}")
        return page_number
    except Exception as e:
        print(f"❌ Error in search step: {e}")
        return None

def get_cited_answer_agent(pages_data, question, model_name="llama3-8b-8192"):
    """
    Takes page data and a question, and returns a high-fidelity answer
    with minimal hallucination.
    """
    print(f"\n🤖 Sending question to Groq model...")
    
    formatted_pages = "\n\n".join(
        [f"--- Page {p['page_number']} ---\n{p['content']}" for p in pages_data]
    )

    # This new prompt is much more demanding and explicit.
    prompt = f"""
    You are a research assistant. Your task is to answer a question based **ONLY** on the text provided within the <DOCUMENT_CONTEXT> tags. You are forbidden from using any outside knowledge.

    <DOCUMENT_CONTEXT>
    {formatted_pages}
    </DOCUMENT_CONTEXT>

    Your response MUST strictly follow these rules:
    1.  Analyze the user's question and the document context carefully.
    2.  Provide a direct answer to the question.
    3.  Your final response MUST be in the following format:
        (Answer):
        [Your clear and concise answer.]

        (Supporting Evidence:)
        - (Direct Quote:) "[An exact quote from the document that directly proves your answer.]"
        - (ref:) [Page X]
    4.  (CRITICAL RULE:) If you cannot find a direct answer within the provided <DOCUMENT_CONTEXT>, you MUST respond with only this exact phrase: "The answer could not be found in the provided document." Do not try to guess or infer an answer.

    USER QUESTION: {question}
    """
    
    try:
        client = Groq()
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model_name,
            temperature=0.0 # Force factual, deterministic output
        )
        answer = chat_completion.choices[0].message.content
        print("✅ High-fidelity answer received from Groq.")
        return answer
    except Exception as e:
        print(f"❌ An error occurred with the Groq API call: {e}")
        return "Sorry, I could not process the request to the AI model."


if __name__ == "__main__":
    pdf_file = "media\gradient-desceny.pdf"  
    
    all_pages_data = extract_text_from_all_pages(pdf_file)

    if all_pages_data:
        print("\n--- Document analysis complete. You can now ask questions. ---")
        
        while True:
            user_question = input("\nYou (type 'quit' to exit): ")
            
            if user_question.lower() in ['quit', 'exit']:
                
                print("Exiting chat. Goodbye!")
                break
            
            relevant_page_num = find_relevant_page(all_pages_data, user_question)

            if relevant_page_num:
                relevant_page_data = [p for p in all_pages_data if p['page_number'] == relevant_page_num]
                final_answer = get_cited_answer_agent(relevant_page_data, user_question)
                
                print("\nAssistant:")
                print(final_answer)
            else:
                print("\nAssistant: Sorry, I couldn't determine a relevant page for that question.")
    else:
        print("Could not process the PDF. Exiting.")