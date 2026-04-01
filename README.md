# Enterprise RAG Q&A System

A production-ready Retrieval-Augmented Generation (RAG) platform that allows users to upload enterprise documents (PDF, DOCX, TXT, MD) and interact with their content using AI-powered natural language queries. Built with a FastAPI backend and a stunning, state-of-the-art modern frontend.

![UI Screenshot](https://via.placeholder.com/1200x600/0f172a/10b981?text=Enterprise+RAG+Q%26A+System+Interface)

## 🚀 Key Features

- **Document Ingestion**: Seamlessly upload and index `.pdf`, `.docx`, `.txt`, and `.md` files.
- **Smart Chunking**: Automated processing of documents using LangChain's recursive character splitting.
- **Efficient Vector Search**: Powered by **FAISS** and **HuggingFace** embeddings (`all-MiniLM-L6-v2`) for ultra-fast, semantic document retrieval.
- **AI-Powered Answers**: Integrated with **Groq (Llama 3.1 8B)** to provide context-aware, cited, and intelligent responses.
- **Premium Glassmorphic UI**: A breathtaking, dynamic gradient interface utilizing glassmorphism (`backdrop-filter`), micro-animations, floating elements, and `Outfit` typography to deliver a state-of-the-art user experience.
- **RESTful API**: Fully documented API endpoints for document management and querying.

## 🛠️ Technology Stack

- **Backend**: Python 3.9+, FastAPI, LangChain, FAISS, Sentence Transformers.
- **Frontend**: HTML5, CSS3 (Modern Vanilla), JavaScript (ES6+).
- **LLM Provider**: Groq API.

## 📋 Prerequisites

- Python 3.9 or higher.
- A **Groq API Key** (Get one at [console.groq.com](https://console.groq.com/)).

## ⚙️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd rag1
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file in the root directory and add your Groq API key (refer to `.env.example`).
   ```bash
   cp .env.example .env
   # Edit .env with your GROQ_API_KEY
   ```

## 🏃 Running the Application

1. **Start the FastAPI server**:
   ```bash
   python run.py
   ```
   The backend logic and frontend assets will be served at `http://localhost:8000`.

2. **Access the application**:
   Open your browser and navigate to `http://localhost:8000`.

## 📂 Project Structure

```text
rag1/
├── backend/            # Python backend source code
│   ├── routers/        # API route handlers (Upload, Query, Documents)
│   ├── main.py         # FastAPI application entry point
│   ├── ingest.py       # Document parsing and chunking logic
│   ├── vectorstore.py  # FAISS vector store management
│   ├── embeddings.py   # Embedding model configuration
│   └── qa_chain.py     # LangChain Q&A pipeline
├── frontend/           # Vanilla JS/CSS/HTML frontend
├── uploads/            # Temporary storage for uploaded documents
├── vectorstore/        # Local persistent FAISS storage
├── requirements.txt    # Python dependencies
├── run.py              # Application startup script
└── .env                # Environment configuration
```
