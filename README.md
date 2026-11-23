# AI-Based Knowledge Retrieval Platform with Query Resolution System

## 1. Project Overview

The **AI-Based Knowledge Retrieval Platform with Query Resolution System** is a document-based knowledge retrieval application built using a Retrieval-Augmented Generation (RAG) approach.

Users can upload knowledge documents, process their content into searchable chunks, and ask natural-language questions. The backend classifies incoming queries, retrieves relevant evidence from the knowledge base, handles ambiguous questions through clarification, and attempts to generate grounded answers using Google Gemini.

The application includes a React frontend, a FastAPI backend, a Sentence Transformers embedding model, and a local Qdrant vector database.

## 2. Implemented Features

### Document ingestion and retrieval
- Upload and validate PDF, DOCX, TXT, and CSV documents.
- Extract and clean text from supported document formats.
- Split text into overlapping chunks using a native Python chunking implementation.
- Generate 384-dimensional embeddings using Sentence Transformers (`all-MiniLM-L6-v2`).
- Store document chunk embeddings and metadata in a local Qdrant collection.
- Retrieve relevant chunks using vector similarity and the project's retrieval logic.
- Support document-filtered retrieval and structured CSV/ticket-aware retrieval.

### Query resolution and multi-agent workflow
- **Query Understanding Agent:** normalizes queries, classifies query intent, and identifies queries that may need clarification.
- **Clarification Agent:** detects ambiguous or incomplete questions and prepares clarification prompts.
- **Retrieval Agent:** invokes the existing retrieval service and filters retrieved evidence for relevance.
- **Response Generation Agent:** prepares grounded responses from retrieved evidence using Google Gemini and validates returned source references.
- **Orchestration Agent:** coordinates query understanding, clarification, retrieval, and response generation in sequence.
- Expose the orchestration workflow through `POST /documents/ask`.
- Retain `POST /documents/query` as a retrieval-only endpoint.

The response-generation agent depends on the availability of the external Gemini API. If generation is unavailable, the API can return a generation-failure status while preserving retrieved evidence. A successful local build or mocked unit test does not guarantee live Gemini API availability.

### Frontend
- React and Vite application.
- Overview, Knowledge Base, Ask Documents, Retrieval Explorer, and Evaluation sections.
- Ask Documents integration with the orchestration endpoint.
- Displays clarification prompts, generated answers when available, generation notices, and retrieved evidence.

### Evaluation and testing
- Retrieval evaluation using prepared sample documents from academic administration and computer networking domains.
- Unit tests for query understanding, clarification, response generation, orchestration, and text chunking.
- The current automated test run completed with **35 passing tests**, excluding the separate live Gemini connectivity test. The live connectivity test may require network access and can be delayed by external API retries.

## 3. Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Backend API | FastAPI |
| API server | Uvicorn |
| Frontend | React, Vite, JavaScript |
| Styling | Tailwind CSS |
| PDF extraction | pypdf |
| DOCX extraction | python-docx |
| CSV processing | Python `csv` module |
| Text chunking | Native Python implementation |
| Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`) |
| Vector database | Qdrant |
| LLM response generation | Google Gemini API (`google-genai`) |
| Testing | pytest |
| Version control | Git and GitHub |

### Proposed or not yet implemented
The following items may appear in the architecture or future-work documentation but should not be considered completed integrations:
- Persistent conversation memory.
- Voice interaction using the Web Speech API.
- PostgreSQL metadata persistence.
- Docker-based deployment.
- LangGraph-based orchestration (the current orchestration is implemented as a Python workflow).

## 4. System Architecture

The current query workflow is:

1. The user submits a question through the React frontend.
2. FastAPI receives the request at `POST /documents/ask`.
3. The Query Understanding Agent normalizes and classifies the question.
4. If the question is ambiguous or incomplete, the Clarification Agent prepares a clarification response.
5. Otherwise, the Retrieval Agent calls the knowledge retrieval service.
6. The Response Generation Agent attempts to produce an answer grounded in the retrieved evidence using Google Gemini.
7. The Orchestration Agent returns the workflow status, answer or clarification (when applicable), and retrieval evidence to the frontend.
8. The frontend displays the response and supporting evidence, including a notice if external generation is unavailable.

Document ingestion follows a separate pipeline: upload → extraction → cleaning and chunking → embedding generation → Qdrant indexing.

For the detailed architecture and design decisions, see [M1.2 – System Architecture](documentation/M1.2_System_Architecture.md).

## 5. Repository Structure

```text
.
├── backend/
│   └── app/
│       ├── agents/
│       │   ├── clarification_agent.py
│       │   ├── orchestration_agent.py
│       │   ├── query_understanding_agent.py
│       │   ├── response_generation_agent.py
│       │   └── retrieval_agent.py
│       ├── routes/
│       │   └── documents.py
│       ├── services/
│       │   ├── document_extractor.py
│       │   ├── document_processor.py
│       │   ├── document_service.py
│       │   ├── embedding_service.py
│       │   ├── ingestion_service.py
│       │   ├── qdrant_service.py
│       │   ├── retrieval_service.py
│       │   └── text_chunker.py
│       └── main.py
├── frontend/
│   ├── src/
│   │   └── App.jsx
│   └── ...
├── documentation/
│   ├── M1.1_Research_and_Technical_Understanding.md
│   ├── M1.2_System_Architecture.md
│   └── M1.4_Retrieval_and_Accuracy_Evaluation.md
├── evaluation_samples/
├── tests/
│   ├── test_clarification_agent.py
│   ├── test_gemini_connection.py
│   ├── test_orchestration_agent.py
│   ├── test_response_generation_agent.py
│   └── test_text_chunker.py
├── requirements.txt
├── README.md
└── .gitignore
```

Local uploaded files, Qdrant storage, virtual environments, environment files, and generated frontend build output should remain excluded from version control where appropriate.

## 6. Project Milestones

### Milestone 1 – Foundation and Knowledge Retrieval
- [x] **M1.1** – Research and Technical Understanding
- [x] **M1.2** – System Architecture
- [x] **M1.3** – Knowledge Base Ingestion Module
- [x] **M1.4** – RAG Retrieval Pipeline and Validation

### Milestone 2 – Multi-Agent Query Resolution
- [x] **M2.1** – Query Understanding Agent
- [x] **M2.2** – Retrieval Agent
- [x] **M2.3** – Response Generation Agent
- [x] **M2.4** – Clarification Agent
- [x] **M2.5** – Multi-Agent Orchestration

The milestone checklist reflects implementation and local testing. External Gemini response generation remains dependent on live API availability.

## 7. Retrieval Evaluation

Initial retrieval evaluation used two sample documents from academic administration and computer networking domains, containing seven indexed chunks in total, and ten prepared test questions.

| Metric | Correct results | Score |
|---|---:|---:|
| Hit@1 | 10/10 | 100% |
| Hit@3 | 10/10 | 100% |
| Hit@5 | 10/10 | 100% |

Domain-wise Hit@1:
- Academic Administration: 5/5 (100%).
- Computer Networking: 5/5 (100%).

These results apply only to the prepared sample dataset. They do not establish performance on larger or unrelated datasets. The evaluation measures retrieval of expected chunks, not the factual correctness of generated answers.

## 8. Installation and Setup

### Prerequisites
- Python 3.12 or a compatible Python version supported by the installed dependencies.
- Node.js and npm.
- Git.
- A Google Gemini API key for live answer generation.

### Clone the repository

```bash
git clone https://github.com/dev-with-asmie/Development-of-AI-Based-Knowledge-Retrieval-Platform-with-Query-Resolution-System.git
cd Development-of-AI-Based-Knowledge-Retrieval-Platform-with-Query-Resolution-System
```

### Set up the backend

Create and activate a virtual environment in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install Python dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Configure the Gemini API key in the local environment file using the environment variable expected by the backend configuration. Do not commit API keys or other secrets.

Start the backend:

```powershell
python -m uvicorn backend.app.main:app --reload
```

The backend is available at `http://127.0.0.1:8000`.

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### Set up the frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Vite prints the local frontend URL in the terminal (normally `http://localhost:5173`).

To create a production build:

```powershell
npm run build
```

## 9. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Backend welcome/status message |
| GET | `/health` | Health check |
| POST | `/documents/upload` | Upload and validate a document |
| GET | `/documents/{stored_filename}/extract` | Extract text from an uploaded document |
| POST | `/documents/{stored_filename}/process` | Process, chunk, embed, and index an uploaded document |
| POST | `/documents/query` | Retrieval-only query endpoint |
| POST | `/documents/ask` | Orchestrated query resolution and answer-generation workflow |

See the interactive API documentation at `http://127.0.0.1:8000/docs` for request and response schemas.

## 10. Running Tests

Run the automated tests from the project root:

```powershell
python -m pytest -q --ignore=tests/test_gemini_connection.py
```

The live Gemini connectivity test is separate because it calls an external service and may be affected by network availability, API quotas, or service-side delays:

```powershell
python -m pytest -q tests/test_gemini_connection.py
```

## 11. Documentation

- [M1.1 – Research and Technical Understanding](documentation/M1.1_Research_and_Technical_Understanding.md)
- [M1.2 – System Architecture](documentation/M1.2_System_Architecture.md)
- [M1.4 – Retrieval and Accuracy Evaluation](documentation/M1.4_Retrieval_and_Accuracy_Evaluation.md)

## 12. Project Repository

GitHub: [Development of AI-Based Knowledge Retrieval Platform with Query Resolution System](https://github.com/dev-with-asmie/Development-of-AI-Based-Knowledge-Retrieval-Platform-with-Query-Resolution-System)
