# AI-Based Knowledge Retrieval Platform with Query Resolution System

## 1. Project Overview

The **AI-Based Knowledge Retrieval Platform with Query Resolution System** is a document-based knowledge retrieval application. It allows users to upload documents, extract and process their content, convert text chunks into vector embeddings, and retrieve relevant information through semantic search.

The project follows a Retrieval-Augmented Generation (RAG) architecture. The current implementation covers document ingestion, embedding generation, vector indexing, and semantic retrieval. Natural-language answer generation and multi-agent orchestration are part of the proposed architecture and future development; they are not yet implemented in the current backend.

## 2. Implemented Features

- Upload and validate PDF, DOCX, TXT, and CSV documents.
- Extract text from supported document formats.
- Clean and split extracted text into overlapping chunks.
- Generate 384-dimensional embeddings using Sentence Transformers (`all-MiniLM-L6-v2`).
- Store document chunk embeddings and metadata in a local Qdrant collection.
- Retrieve relevant chunks using cosine similarity search.
- Filter retrieval results by selected document filenames.
- Expose document upload, extraction, and processing endpoints through FastAPI.
- Evaluate retrieval using sample documents from academic administration and computer networking domains.

## 3. Technology Stack

### Currently implemented

| Component | Technology |
|---|---|
| Programming Language | Python |
| Backend API | FastAPI |
| API Server | Uvicorn |
| PDF Extraction | pypdf |
| DOCX Extraction | python-docx |
| CSV Processing | Python `csv` module |
| Text Chunking | LangChain Text Splitters |
| Embedding Model | Sentence Transformers (`all-MiniLM-L6-v2`) |
| Vector Database | Qdrant |
| Version Control | Git and GitHub |

### Proposed for future development

| Component | Proposed Technology |
|---|---|
| Frontend | React.js |
| LLM-based Response Generation | Google Gemini API |
| Agent Orchestration | LangGraph |
| Metadata Database | PostgreSQL |
| Voice Interaction | Web Speech API |
| Containerization | Docker |

The proposed technologies above are architectural choices and are not represented as completed integrations.

## 4. System Architecture

The planned platform is organized into the following major components:

1. User Interface
2. Backend API
3. Document Ingestion Pipeline
4. Text Extraction and Chunking
5. Embedding Generation
6. Vector Database and Semantic Retrieval
7. Multi-Agent Query Resolution
8. LLM-Based Response Generation
9. Conversation Memory
10. Voice Interaction

The current backend implements document ingestion, embedding generation, Qdrant indexing, and semantic retrieval. The multi-agent workflow, LLM response generation, conversation memory, frontend, and voice interaction remain planned components.

For the detailed proposed architecture, see [M1.2 – System Architecture](documentation/M1.2_System_Architecture.md).

## 5. Proposed Multi-Agent Components

The architecture defines five specialized agent roles:

- **Query Understanding Agent:** Understands user queries and identifies intent.
- **Retrieval Agent:** Searches the knowledge base for relevant information.
- **Response Generation Agent:** Generates answers grounded in retrieved content.
- **Clarification Agent:** Handles ambiguous or incomplete questions.
- **Conversation Memory Agent:** Maintains relevant conversational context.

These roles are currently defined in the architecture documentation. Their LangGraph orchestration and agent implementations are planned for a later development phase.

## 6. Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   │   └── documents.py
│   │   ├── services/
│   │   │   ├── document_extractor.py
│   │   │   ├── document_processor.py
│   │   │   ├── document_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── ingestion_service.py
│   │   │   ├── qdrant_service.py
│   │   │   ├── retrieval_service.py
│   │   │   └── text_chunker.py
│   │   └── main.py
│   ├── uploads/                 # Local uploaded files; not committed
│   └── qdrant_storage/          # Local vector database; not committed
├── documentation/
│   ├── M1.1_Research_and_Technical_Understanding.md
│   ├── M1.2_System_Architecture.md
│   └── M1.4_Retrieval_and_Accuracy_Evaluation.md
├── evaluation_samples/
│   ├── academic_policy_sample.txt
│   └── networking_sample.txt
├── experiments/
├── evaluate_chunk_retrieval.py
├── evaluate_retrieval.py
├── inspect_evaluation_chunks.py
├── test_retrieval.py
├── requirements.txt
├── README.md
└── .gitignore
```

## 7. Project Milestones

- [x] **M1.1** – Research and Technical Understanding
- [x] **M1.2** – System Architecture
- [x] **M1.3** – Knowledge Base Ingestion Module
- [x] **M1.4** – RAG Retrieval Pipeline and Validation

## 8. Current Development Status

**Milestone 1 – Foundation and Knowledge Retrieval**

The research, architecture design, core document ingestion pipeline, semantic retrieval service, and initial retrieval evaluation have been completed.

### M1.1 – Research and Technical Understanding

Research and documentation covering RAG architecture, chunking, embeddings, vector databases, multi-agent systems, and the Web Speech API.

### M1.2 – System Architecture

Documented the proposed system architecture, component responsibilities, five agent roles, orchestration flow, and data models.

### M1.3 – Knowledge Base Ingestion Module

Implemented and tested:
- File upload and validation for PDF, DOCX, TXT, and CSV.
- Text extraction and preprocessing.
- Text chunking with overlap.
- Embedding generation using `all-MiniLM-L6-v2`.
- Qdrant collection creation and vector indexing.

### M1.4 – RAG Retrieval Pipeline and Validation

Implemented semantic retrieval using query embeddings and Qdrant cosine similarity search.

Initial evaluation used two sample documents from two domains, containing seven indexed chunks in total, and ten test questions.

| Metric | Correct Results | Score |
|---|---:|---:|
| Hit@1 | 10/10 | 100% |
| Hit@3 | 10/10 | 100% |
| Hit@5 | 10/10 | 100% |

Domain-wise Hit@1:
- Academic Administration: 5/5 (100%)
- Computer Networking: 5/5 (100%)

These results apply to the prepared sample dataset and do not establish performance on larger or unrelated datasets. The evaluation measures retrieval of expected chunks, not the factual correctness of generated answers.

## 9. Documentation

- [M1.1 – Research and Technical Understanding](documentation/M1.1_Research_and_Technical_Understanding.md)
- [M1.2 – System Architecture](documentation/M1.2_System_Architecture.md)
- [M1.4 – Retrieval and Accuracy Evaluation](documentation/M1.4_Retrieval_and_Accuracy_Evaluation.md)

## 10. Running the Backend

### Prerequisites

- Python 3.12 recommended
- Git

### Installation

Clone the repository:

```bash
git clone https://github.com/dev-with-asmie/Development-of-AI-Based-Knowledge-Retrieval-Platform-with-Query-Resolution-System.git
cd Development-of-AI-Based-Knowledge-Retrieval-Platform-with-Query-Resolution-System
```

Create and activate a virtual environment (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Start the backend:

```powershell
python -m uvicorn backend.app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`.

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### Available API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Backend welcome/status message |
| GET | `/health` | Health check |
| POST | `/documents/upload` | Upload and validate a document |
| GET | `/documents/{stored_filename}/extract` | Extract text from an uploaded document |
| POST | `/documents/{stored_filename}/process` | Process, chunk, embed, and index an uploaded document |

The semantic retrieval service is currently implemented as a backend service and used by the evaluation scripts; a public query API and LLM-generated answer endpoint have not yet been added.

## 11. Project Repository

GitHub: [Development of AI-Based Knowledge Retrieval Platform with Query Resolution System](https://github.com/dev-with-asmie/Development-of-AI-Based-Knowledge-Retrieval-Platform-with-Query-Resolution-System)
