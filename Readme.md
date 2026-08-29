# AI Business Agent

An AI-powered business intelligence and knowledge-base assistant built with **Python, FastAPI, LangChain, and LangGraph**.

The service is designed to integrate with the InsightFlow business management platform, allowing organizations to interact with their business data and uploaded documents using natural language.

The agent can automatically select business analytics tools, search an organization's private knowledge base using RAG, maintain conversation context, and generate concise business-focused responses.

---

## Technologies

| Technology                  | Purpose                                                         |
| --------------------------- | --------------------------------------------------------------- |
| Python                      | Core AI service logic                                           |
| FastAPI                     | REST API for the AI service                                     |
| LangChain                   | LLM integration, tools, and tool calling                        |
| LangGraph                   | Agent workflow, routing, state management, and execution        |
| Gemini                      | Large language model inference                                  |
| Google GenAI                | Gemini API and embedding integration                            |
| MongoDB Atlas               | Business data, documents, vectors, and conversation persistence |
| MongoDB Atlas Vector Search | Semantic similarity search over document embeddings             |
| Sentence Transformers       | Document and query embeddings                                   |
| MongoDBSaver                | LangGraph checkpoint persistence                                |
| Pydantic                    | Request and data validation                                     |
| PyMuPDF                     | PDF document text extraction                                    |

---

## Features

### AI Assistant

The AI assistant allows organizations to interact with their business data using natural language.

Examples:

```text
"Who are my top customers?"

"What was our revenue this month?"

"Which products sold the most?"

"How many orders were completed this week?"

"What are the main topics covered in my documents?"
```

The agent determines which tools or knowledge sources are required and executes them automatically.

### Intelligent Tool Routing

The agent uses a routing layer to determine which business domains are relevant to a user's question.

Supported domains include:

* Customers
* Orders
* Products
* Inventory
* Sales
* Business overview
* Knowledge base

A question can require one or multiple domains.

For example:

```text
"Who are my top customers?"
        ↓
Customer Analysis
        ↓
Top customers by spending
```

```text
"What products sold the most this month?"
        ↓
Product Analysis
        ↓
Product sales analysis
```

```text
"What information is contained in my documents?"
        ↓
Knowledge Base
        ↓
Vector Search
        ↓
Relevant document chunks
        ↓
Gemini
        ↓
Answer
```

### Business Analytics

The agent provides natural-language access to business analytics including:

* Customer rankings
* Customer spending
* Order frequency
* Customer lifetime value
* Order statistics
* Order status analysis
* Sales trends
* Revenue analysis
* Product performance
* Best-selling products
* Inventory information
* Business overview metrics

The underlying analytics are calculated from the organization's actual business data.

---

## Knowledge Base and RAG

The AI assistant includes a private knowledge base for each organization.

Pro organizations can upload up to **10 documents** to their knowledge base.

Uploaded documents are processed into searchable chunks and stored with their vector embeddings.

The RAG pipeline works approximately as follows:

```text
Document Upload
      ↓
Document Processing
      ↓
Text Extraction
      ↓
Text Chunking
      ↓
Embedding Generation
      ↓
MongoDB Atlas
      ↓
Document Chunks + Embeddings
```

When a user asks a question about their documents:

```text
User Question
      ↓
Query Embedding
      ↓
MongoDB Atlas Vector Search
      ↓
Relevant Document Chunks
      ↓
Gemini
      ↓
Grounded Answer
```

### Embeddings

The project uses Google Gemini Embeddings through the Google GenAI SDK.

A genai.Client is initialized using the GEMINI_API_KEY environment variable. Document chunks and user queries are converted into embeddings using Gemini and stored/searched through MongoDB Atlas Vector Search.

The same embedding model is used for both document chunks and user queries so that their vectors exist in the same semantic space.

### Vector Search

MongoDB Atlas Vector Search is used to retrieve semantically relevant document chunks.

Searches are scoped to the current organization so that one organization's documents cannot be returned for another organization's request.

The vector search stores information such as:

```text
content
embedding
organization
fileId
filename
chunkIndex
```

The `organization` field is used to isolate knowledge-base searches between organizations.

---

## Document Processing

Document processing is separated from the main request-response flow.

When a document is uploaded, it can initially be marked as:

```text
pending
```

The document-processing workflow then extracts its content, creates chunks, generates embeddings, and stores the resulting document chunks.

Once processing is complete, the document becomes available to the AI assistant.

This prevents large document-processing operations from blocking the main API request.

---

## Conversation Memory

The agent uses LangGraph state management and MongoDB checkpoint persistence to maintain conversations across requests.

Each conversation is associated with a unique thread ID.

```text
User Message
      ↓
Thread ID
      ↓
Load Previous State
      ↓
LangGraph
      ↓
Agent / Tools / RAG
      ↓
Response
      ↓
Save Checkpoint
```

### Context Management

Long conversations can cause the state to grow significantly.

To prevent excessive context size, the agent uses context management and conversation summarization.

Recent relevant messages are retained while older conversation history can be summarized or trimmed.

This helps:

* Reduce token usage
* Prevent oversized requests
* Maintain relevant conversation context
* Improve agent reliability during long conversations

---

## Agent Workflow

The agent is implemented using LangGraph.

A simplified workflow is:

```text
User Request
      ↓
Context Management
      ↓
Route / Select Tools
      ↓
Gemini
      ↓
Tool Call?
   ┌──┴──┐
   │     │
  Yes    No
   │     │
   ▼     ▼
Tools   Response
   │
   ├── Business Analytics
   │
   └── Knowledge Base / RAG
          ↓
     Tool Result
          ↓
        Gemini
          ↓
       Response
```

The agent can perform multiple tool calls when additional information is required before generating the final answer.

---

## Business Tools

The agent exposes specialized tools instead of giving the LLM direct unrestricted access to the database.

Examples include:

```text
Customer tools
Order tools
Product tools
Inventory tools
Sales tools
Overview tools
Knowledge-base search
```

This provides a controlled interface between the LLM and the application's business data.

The LLM decides which tool is appropriate based on the user's request, while the tool itself performs the actual database operation.

---

## Organization Isolation

All business analytics and knowledge-base operations are scoped to the current organization.

The organization ID is passed to the AI service with the request:

```json
{
  "message": "What are my top customers?",
  "organization_id": "...",
  "thread_id": "..."
}
```

For RAG searches, the organization ID is also used as a filter during vector search.

This prevents documents and business data from being mixed between organizations.

---

## API Integration

The AI service is an independent backend service rather than a standalone frontend application.

InsightFlow communicates with it through HTTP requests.

Example:

```http
POST /api/agent/chat
```

Request:

```json
{
  "message": "Who are my top customers?",
  "organization_id": "...",
  "thread_id": "..."
}
```

The service:

1. Receives the user's request
2. Loads relevant conversation state
3. Determines the required tools
4. Executes business analytics or RAG searches
5. Sends tool results back to Gemini
6. Generates the final response
7. Persists the conversation state

---

## Access Control and AI Limits

AI access and subscription limits are controlled by the main InsightFlow application.

The Pro plan includes:

* AI business assistant
* Knowledge base
* Up to 10 uploaded documents
* Daily AI message limits

The Free plan does not include the AI assistant or knowledge-base functionality.

The main application is responsible for enforcing plan access and daily AI usage limits before requests reach the AI service.

---

## Response Style

The assistant is designed to return concise, business-focused responses rather than unnecessarily long explanations.

For example:

```text
Top customers this month:

1. younes — $649.87
2. Amine Meziane — $529.95
3. Yasmine Kaci — $99.99
```

The agent is configured to avoid unnecessary formatting and keep analytical responses easy to scan.

---

## Persistence

LangGraph checkpoints are stored in MongoDB using `MongoDBSaver`.

Persisted state allows the system to maintain:

* Conversation history
* Thread-specific state
* Previous tool interactions
* Multi-turn context

MongoDB is also used for:

* Business data
* Document metadata
* Document chunks
* Embeddings
* Conversation data
* LangGraph checkpoints

---

## Architecture

The AI service operates independently from the main InsightFlow backend.

```text
                    InsightFlow
                         │
                         │ HTTP
                         ▼
              ┌─────────────────────┐
              │    FastAPI Service   │
              │                     │
              │      LangGraph      │
              │          │          │
              │      LangChain      │
              │          │          │
              │        Gemini       │
              └──────────┬──────────┘
                         │
              ┌──────────┴───────────┐
              │                      │
              ▼                      ▼
      Business Analytics        Knowledge Base
              │                      │
              ▼                      ▼
          MongoDB Atlas       Vector Search
                                     │
                                     ▼
                              Document Chunks
                              + Embeddings
```

Document processing runs independently through the application's background job system.

---

## Conversation Flow

A typical business-analysis request:

```text
User
 │
 │ "Who are my top customers?"
 ▼
InsightFlow Backend
 │
 ▼
FastAPI AI Service
 │
 ▼
LangGraph
 │
 ▼
Gemini
 │
 │ analyze_customers(...)
 ▼
Customer Analytics Tool
 │
 ▼
MongoDB
 │
 ▼
Tool Result
 │
 ▼
Gemini
 │
 ▼
Concise Business Response
```

A knowledge-base request:

```text
User
 │
 │ "What information is in my documents?"
 ▼
FastAPI AI Service
 │
 ▼
LangGraph
 │
 ▼
Gemini
 │
 │ search_knowledge_base(...)
 ▼
Query Embedding
 │
 ▼
MongoDB Atlas Vector Search
 │
 ▼
Relevant Document Chunks
 │
 ▼
Gemini
 │
 ▼
Grounded Response
```

---

## Project Structure

A simplified structure:

```text
app/
├── database/
│   └── DbConnection.py
│
├── rag/
│   ├── vector.py
│   ├── embeddings.py
│   ├── loader.py
│   └── service.py
│
├── routes/
│   ├── agent.py
│   └── rag.py
│
├── tools/
│   ├── analytics/
│   │   ├── customers_analysis.py
│   │   ├── inventory_analysis.py
│   │   ├── orders_analysis.py
│   │   ├── overview_analytics.py
│   │   ├── products_analysis.py
│   │   └── sales_analysis.py
│   │
│   ├── customers.py
│   ├── orders.py
│   ├── products.py
│   └── rag_tools.py
│
├── utils/
│   └── dates.py
│
├── graph.py
├── llm.py
├── main.py
├── router.py
├── state.py
└── summarizer.py
```

---

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd LangGraph-AI-Agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

Windows:

```bash
venv\Scripts\activate
```

Linux / macOS:

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file containing the required configuration:

```env
MONGODB_URI=your_mongodb_connection_string
MONGODB_DATABASE=your_database

GEMINI_API_KEY=your_gemini_api_key
```

### 6. Run the service

```bash
uvicorn main:app --reload
```

The FastAPI service will then be available locally.

---

## Requirements

The service requires:

* Python 3.10+
* MongoDB Atlas
* MongoDB Atlas Vector Search
* Gemini API key
* FastAPI
* LangChain
* LangGraph
* PyMuPDF
* Pydantic

The MongoDB Atlas cluster must contain the required collections and a configured vector search index for the knowledge-base functionality.

---

## Project Goal

The goal of this project is to build a modular AI agent capable of interacting with real business data and private organizational documents through natural language.

The system combines:

* LLM-powered tool calling
* LangGraph agent workflows
* Business analytics
* RAG
* Semantic vector search
* Document embeddings
* Conversation memory
* Context summarization
* Organization-level data isolation

The AI service can be integrated into existing SaaS and business management applications without requiring the AI logic to be implemented directly inside the main application.
