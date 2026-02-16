# ExamForge - Multimodal RAG Exam Assistant

An intelligent PDF assistant powered by **Multimodal RAG** and **Groq's ultra-fast LLM inference** that enables users to chat with their PDF documents and automatically generate comprehensive exam questions from study materials.

## ✨ Features

### 💬 Interactive PDF Chat
- Upload any PDF document and ask questions about its content
- Powered by **Groq Llama 3.3 70B** for lightning-fast responses
- RAG (Retrieval-Augmented Generation) ensures accurate, context-aware answers
- Efficient vector search using FAISS

### 📝 AI-Powered Exam Generator
- **Multimodal analysis** - Analyzes both text AND diagrams/images in PDFs
- Generates three types of questions:
  - Multiple Choice Questions (MCQ) with options and correct answers
  - Short Answer Questions with reference answers
  - Essay Questions with key points to cover
- Filters out administrative content (syllabus, logistics) and focuses on technical subject matter
- **Export to PDF** - Download generated exams as professionally formatted PDF documents
- Powered by **Groq Llama 4 Scout** (17B multimodal model)

## 🚀 Technology Stack

| Category | Technology |
|----------|-----------|
| **LLM Provider** | [Groq](https://groq.com/) - Ultra-fast inference |
| **LLM Models** | Llama 3.3 70B (chat), Llama 4 Scout (multimodal) |
| **Framework** | [LangChain](https://www.langchain.com/) - LLM orchestration |
| **Vector DB** | [FAISS](https://github.com/facebookresearch/faiss) - Similarity search |
| **Embeddings** | [Sentence-Transformers](https://sbert.net/) - HuggingFace (all-MiniLM-L6-v2) |
| **PDF Processing** | pdfplumber (text), PyMuPDF (images) |
| **PDF Generation** | ReportLab - Professional PDF reports |
| **UI** | [Streamlit](https://streamlit.io/) - Interactive web interface |

## 📦 Installation

### 1. Clone the Repository
```bash
https://github.com/Nawranx/ExamForge---Multimodal-RAG-Exam-Assistant.git
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
cd langchain_ver
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the `langchain_ver/` directory:

```env
GROQ_API_KEY=your_groq_api_key_here
```

> **Get your Groq API key**: Sign up at [console.groq.com](https://console.groq.com/)

## 🎯 Usage

### Run the Application
```bash
cd langchain_ver
streamlit run app_streamlit.py
```

The app will open in your browser at `http://localhost:8501`

### How to Use

1. **Upload a PDF** - Click "Upload a PDF file" and select your document
2. **Wait for Processing** - The app will extract text, create embeddings, and prepare the vector store
3. **Choose a Feature**:
   - **💬 Chat with PDF**: Ask questions in natural language
   - **📝 Exam Generator**: Click "Generate Comprehensive Exam" to create questions from your PDF
4. **Download Exam** (optional) - After generating questions, click "Download Exam PDF"

## 📁 Project Structure

```
Rag_Pdf_Assistant/
└── langchain_ver/              # Main application directory
    ├── app_streamlit.py        # Streamlit web application (main entry point)
    ├── multimodal_utils.py     # Exam generation & PDF utilities
    ├── requirements.txt        # Python dependencies
    └── .env                    # API keys (create this - see Installation)
```

## 🛠️ Core Components

### `app_streamlit.py`
- Main Streamlit application
- Handles PDF upload, text extraction, chunking
- Creates FAISS vector store with HuggingFace embeddings
- Implements RetrievalQA chain for chat functionality
- Integrates multimodal exam generation

### `multimodal_utils.py`
Three key functions:
- `convert_pdf_to_images()` - Converts PDF pages to base64 images
- `generate_exam_with_groq()` - Sends images to Groq in batches, generates questions
- `create_pdf_report()` - Creates professionally formatted PDF exam reports

## 🔒 Security Notes

- **Never commit your `.env` file** - It contains your API keys
- The `.gitignore` is configured to exclude sensitive files
- Uploaded PDFs are processed locally and not stored permanently

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## 📄 License

MIT

## 🙏 Acknowledgments

- [Groq](https://groq.com/) for ultra-fast LLM inference
- [LangChain](https://www.langchain.com/) for the RAG framework
- [Streamlit](https://streamlit.io/) for the amazing UI framework

---

**Built with ❤️ using Groq and LangChain**
