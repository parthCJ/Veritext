# PDF Vision QA Bot 🤖📄

An intelligent PDF question-answering system that can analyze both **text and images** using AI vision models. Ask questions about your PDF documents and get cited answers with page references.

## Features ✨

- 📖 **Full PDF Processing** - Extracts text and images from all pages
- 👁️ **Vision AI** - Uses Groq's vision model to understand images, charts, and diagrams
- 🔍 **Smart Page Search** - Automatically finds the most relevant page for your question
- 📝 **OCR Support** - Extracts text from images using Tesseract OCR
- 💬 **Interactive Chat** - Ask multiple questions in a conversation loop
- 📌 **Cited Answers** - Provides page numbers and direct quotes

## Prerequisites 📋

- Python 3.8+
- Tesseract OCR installed on your system
- Groq API key

## Installation 🔧

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd meta-data
```

2. **Install required packages**
```bash
pip install PyMuPDF pillow pytesseract groq python-dotenv
```

3. **Install Tesseract OCR**
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - **Mac**: `brew install tesseract`
   - **Linux**: `sudo apt-get install tesseract-ocr`

4. **Set up environment variables**

Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
```

## Usage 🚀

1. **Place your PDF** in the `media/` folder

2. **Update the PDF path** in `text-extrcationV2.py`:
```python
pdf_file = "media/your-document.pdf"
```

3. **Run the bot**:
```bash
python text-extrcationV2.py
```

4. **Ask questions**:
```
You (type 'quit' to exit): What does the diagram on page 3 show?
You (type 'quit' to exit): Explain the formula in the image
You (type 'quit' to exit): quit
```

## How It Works 🔄

1. **Extraction Phase**: Processes entire PDF, extracting text and images from all pages
2. **Search Phase**: Uses AI to find the most relevant page for your question
3. **Vision Analysis**: Sends text + images from relevant page to vision model
4. **Answer Generation**: Returns detailed answer with citations

## Models Used 🧠

- **Page Search**: `llama3-8b-8192` (fast text-only model)
- **Vision QA**: `llama-3.2-90b-vision-preview` (multimodal vision model)

## Project Structure 📁

```
meta-data/
├── text-extrcationV2.py    # Main bot script
├── media/                   # PDF files folder
│   └── gradient-desceny.pdf
├── .env                     # API keys (not committed)
├── .gitignore              # Git ignore file
└── README.md               # This file
```

## Example Questions 💡

- "What is shown in the diagram?"
- "Explain the chart on page 5"
- "What does the formula represent?"
- "Describe the image in detail"
- "What is the main topic of this page?"
- "Summarize the key points with visual evidence"

## Limitations ⚠️

- Processes one page at a time (for efficiency)
- Large PDFs may take time to initially process
- Vision model quality depends on image clarity
- Requires active internet connection for Groq API
- Image format must be supported by the vision model

## API Key Setup 🔑

Get your free Groq API key:
1. Visit [console.groq.com](https://console.groq.com)
2. Sign up and generate API key
3. Add to `.env` file

## Troubleshooting 🔧

**"Tesseract not found"**
- Ensure Tesseract is installed and in PATH
- Windows: Add Tesseract installation directory to system PATH

**"API key not found"**
- Check `.env` file exists and contains valid `GROQ_API_KEY`
- Ensure `.env` is in the same directory as the script

**"Could not find page data"**
- Verify PDF path is correct
- Check PDF is not corrupted or password-protected

**"Error with vision model"**
- Check internet connection
- Verify API key is valid
- Ensure image format is supported (jpg, png)

## Environment Variables 🔐

Create a `.env` file with:
```env
GROQ_API_KEY=gsk_your_api_key_here
```

**Note**: Never commit your `.env` file to version control!

## Dependencies 📦

```txt
PyMuPDF>=1.23.0
Pillow>=10.0.0
pytesseract>=0.3.10
groq>=0.4.0
python-dotenv>=1.0.0
```

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Future Enhancements 🚀

- [ ] Multi-page context awareness
- [ ] Support for more document formats (DOCX, PPTX)
- [ ] Conversation history/memory
- [ ] Export answers to markdown/PDF
- [ ] Web interface using Streamlit/Gradio
- [ ] Batch processing multiple PDFs

## License 📄

MIT License - feel free to use in your projects!

## Acknowledgments 🙏

- Built with [Groq AI](https://groq.com) for fast inference
- Uses [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF processing
- OCR powered by [Tesseract](https://github.com/tesseract-ocr/tesseract)

---

**Made with ❤️ using Groq AI and PyMuPDF**

For questions or issues, please open an issue on GitHub.
