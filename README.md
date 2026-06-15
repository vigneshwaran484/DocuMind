# 🧠 Documind: Enterprise RAG Q&A System

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain)](https://python.langchain.com/)
[![FAISS](https://img.shields.io/badge/FAISS-005571?style=for-the-badge&logo=meta)](https://github.com/facebookresearch/faiss)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)
[![Groq](https://img.shields.io/badge/Groq-f55036?style=for-the-badge)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

**Documind** is a high-performance, production-ready Retrieval-Augmented Generation (RAG) platform. It empowers teams to transform static enterprise documents (PDF, DOCX, TXT, MD) into a dynamic knowledge base, enabling instant, context-aware AI interactions through a stunning glassmorphic interface.

![UI Screenshot](https://via.placeholder.com/1200x600/0f172a/10b981?text=Documind+Interface+Preview)

---

## ✨ Why Documind?

In an era of information overload, finding specific answers within hundreds of documents is a challenge. **Documind** solves this by:
- **Privacy First**: Process your sensitive enterprise data locally or within your controlled infrastructure.
- **Lightning Fast**: Optimized vector search with FAISS ensures sub-second retrieval times.
- **Persistent State**: Automated synchronization with Supabase Storage and PostgreSQL preserves your document state even on ephemeral, serverless, or containerized hosting platforms (e.g., Render, Heroku).
- **Contextual Intelligence**: Leveraging Groq's Llama 3.1 8B for human-like reasoning and cited answers.
- **Premium UX**: A "wow" factor interface designed for modern professionals.

---

## 🚀 Key Features

- 📄 **Multi-Format Ingestion**: Support for `.pdf`, `.docx`, `.txt`, and `.md`.
- 🧩 **Semantic Chunking**: Intelligent document processing using LangChain's recursive splitters.
- 🔍 **Vector Search**: Powered by **FAISS** and **HuggingFace** embeddings (`all-MiniLM-L6-v2`).
- ☁️ **Supabase Sync**: Automated background backup of FAISS index files (`index.faiss`, `index.pkl`) to Supabase Storage and document tracker tables in PostgreSQL.
- 🤖 **AI-Powered Insights**: Seamless integration with **Groq (Llama 3.1 8B)**.
- 💎 **Glassmorphic UI**: Breathtaking interface with `backdrop-filter`, floating elements, and `Outfit` typography.
- 🔌 **Developer Friendly**: Robust FastAPI backend with full Swagger/OpenAPI documentation and connectivity debug endpoints.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.9+, FastAPI, LangChain, FAISS, Supabase Python SDK.
- **Embeddings**: Sentence Transformers (`all-MiniLM-L6-v2`).
- **LLM**: Groq (Llama 3.1 8B).
- **Frontend**: Modern Vanilla HTML5, CSS3 (Glassmorphism), JavaScript (ES6+).

---

## 📋 Prerequisites

- **Python 3.9+**
- **Groq API Key**: Obtain one from the [Groq Console](https://console.groq.com/).
- **Supabase Account** (Optional, for persistent cloud storage): Create a free database and storage bucket.

---

## ⚙️ Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/vigneshwaran484/Documind
   cd Documind
   ```

2. **Initialize Virtual Environment**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   Create a `.env` file in the root:
   ```env
   # Groq API Configuration
   GROQ_API_KEY=your_groq_api_key
   GROQ_MODEL=llama-3.1-8b-instant

   # Ingestion & Search Config
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   CHUNK_SIZE=1000
   CHUNK_OVERLAP=200
   TOP_K=4
   VECTORSTORE_PATH=./vectorstore
   UPLOADS_PATH=./uploads

   # Supabase Storage Integration (Optional/Recommended for Cloud)
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key-here
   ```

---

## ☁️ Setting Up Supabase Integration

To enable persistence across ephemeral environments (like Render restarts):

1. **Create Storage Bucket**:
   - Go to your Supabase Console -> Storage.
   - Create a new bucket named `vectorstore`. Make sure it's set to private.

2. **Postgres Table**:
   - The system automatically manages metadata syncing to a database table named `documents`.
   - Ensure your Supabase anon API key and project URL are filled in your `.env`.

---

## 🏃 Running the App

1. **Start the Engine**
   ```bash
   python run.py
   ```

2. **Explore the Interface**
   Open [http://localhost:8000](http://localhost:8000) in your browser.

3. **API Documentation**
   Visit [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive Swagger UI.

4. **Diagnostics**
   - Health Check: `GET /api/health`
   - Connectivity Debug (checks Supabase connection): `GET /api/debug`

---

## 📂 Project Structure

```text
Documind/
├── backend/            # FastAPI source code
│   ├── routers/        # API endpoints (upload, query, documents)
│   ├── config.py       # Configuration and .env loader
│   ├── embeddings.py   # Embedding pipeline
│   ├── ingest.py       # Doc processing and chunking logic
│   ├── llm.py          # Groq client wrapper
│   ├── qa_chain.py     # RAG pipeline logic
│   ├── supabase_store.py # FAISS sync to cloud storage
│   └── vectorstore.py  # Local FAISS index & file operations
├── frontend/           # Vanilla JS/CSS/HTML
├── uploads/            # Temporary document storage
├── vectorstore/        # Local FAISS index storage
└── run.py              # App entry point
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/vigneshwaran484">Vigneshwaran</a>
</p>

