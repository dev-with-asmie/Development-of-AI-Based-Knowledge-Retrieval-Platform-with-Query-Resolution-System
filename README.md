# AI-Based Knowledge Retrieval Platform with Query Resolution System

## 1. Project Overview

The **AI-Based Knowledge Retrieval Platform with Query Resolution System** is an AI-powered application designed to retrieve relevant information from uploaded documents and answer user questions using natural language.

The system uses Retrieval-Augmented Generation (RAG) to retrieve relevant document content and generate context-aware responses. It also incorporates a multi-agent architecture to understand queries, retrieve information, generate responses, handle clarification, and maintain conversational context.

## 2. Key Features (Planned)

- Upload and process PDF, DOCX, TXT, and CSV documents.
- Extract and organize document content.
- Generate embeddings and store them in a vector database.
- Retrieve relevant information using semantic search.
- Generate context-aware responses using an LLM.
- Resolve ambiguous queries through a clarification mechanism.
- Maintain conversational context using conversation memory.
- Support voice-based interaction using the Web Speech API.

## 3. Proposed Technology Stack

| Component | Technology |
|---|---|
| Frontend | React.js |
| Backend | Python, FastAPI |
| LLM | Google Gemini API |
| RAG Framework | LangChain |
| Agent Orchestration | LangGraph |
| Embedding Model | Sentence Transformers (all-MiniLM-L6-v2) |
| Vector Database | Qdrant |
| Metadata Database | PostgreSQL |
| Voice Interface | Web Speech API |
| Containerization | Docker |
| Version Control | Git and GitHub |

## 4. Project Architecture

The planned system consists of the following major components:

1. User Interface
2. Backend API
3. Document Ingestion Pipeline
4. Embedding Generation
5. Vector Database
6. RAG Retrieval Pipeline
7. Multi-Agent Query Resolution
8. LLM-Based Response Generation
9. Conversation Memory
10. Voice Interaction Module

## 5. Multi-Agent Components

The system will contain five specialized agents:

- **Query Understanding Agent:** Understands user queries and identifies intent.
- **Retrieval Agent:** Searches the knowledge base for relevant information.
- **Response Generation Agent:** Generates answers grounded in retrieved content.
- **Clarification Agent:** Handles ambiguous or incomplete questions.
- **Conversation Memory Agent:** Maintains relevant conversational context.

## 6. Repository Structure

```text
.
├── documentation/
│   └── M1.1_Research_and_Technical_Understanding.md
├── experiments/
├── README.md
└── .gitignore
```

Additional implementation folders will be introduced as development progresses.

## 7. Project Milestones

- [x] M1.1 – Research and Technical Understanding
- [ ] M1.2 – System Architecture
- [ ] M1.3 – Knowledge Base Ingestion Module
- [ ] M1.4 – RAG Retrieval Pipeline and Validation

## 8. Current Development Status

**Milestone 1.1 – Research and Technical Understanding**

Research and documentation covering RAG, chunking, embeddings, vector databases, multi-agent systems, and the Web Speech API.

Further implementation and validation will be completed in the upcoming milestones.

## 9. Documentation

Detailed M1.1 research documentation:

[`M1.1 Research and Technical Understanding`](documentation/M1.1_Research_and_Technical_Understanding.md)

## 10. Project Repository

GitHub: https://github.com/dev-with-asmie/Development-of-AI-Based-Knowledge-Retrieval-Platform-with-Query-Resolution-System