# AI Business Agent

An AI-powered business analysis service built with **Python, LangChain, and LangGraph**. The service is designed to be connected to an existing business management application and allows users to interact with business data using natural language.

## 🚀 Technologies

* **Python** — Core logic.
* **FastAPI** — REST API for the agent service
* **LangChain** — LLM integration and tool calling
* **LangGraph** — Agent workflow, routing, and state management
* **MongoDB** — Business data and conversation persistence
* **MongoDBSaver** — LangGraph checkpoint persistence and state
* **Pydantic** — Request validation
* **Groq API / LLMs** — AI model inference

## ✨ Features
### AI & Agent Capabilities

* **Autonomous Tool Routing**: Intelligently selects the required business tools based on natural-language input.
* **Natural-Language Data Analysis**: Allows end-users to query business data without needing SQL or programming knowledge.
* **Error Handling**: Robust communication protocols between the AI agent service and the connected host application.
* **Rate Limiting & Access Control**: Built-in API rate limiting and plan-based access controls for service security.

### Domain Analytics

* **Customer Analysis**: Spending habits, order frequency, CLV, and customer rankings.
* **Order Analysis**: Counts, statuses, trends, and key performance statistics.
* **Product Analysis**: Sales volume, revenue tracking, and best-seller identification.
* **Inventory Analysis**: Real-time stock levels and warehouse insights.
* **Sales & Business Overview**: High-level performance metrics and revenue analytics.

### Persistence & Memory

* **Persistent Checkpointing**: Conversation state is stored in MongoDB via MongoDBSaver.
* **Multi-Threaded Conversations**: Supports multiple isolated user threads.
* **Context Awareness**: Remembers previous interactions to enable fluid, multi-turn follow-up queries.


## 🏗️ Architecture

The service operates as an independent AI backend connected to an existing business application.

```text
Existing Business Application
          │
          │ HTTP / REST API
          ▼
┌───────────────────────────┐
│      FastAPI Service      │
│                           │
│  ┌─────────────────────┐  │
│  │     LangGraph       │  │
│  │    Agent Workflow   │  │
│  └──────────┬──────────┘  │
│             │             │
│      ┌──────▼──────┐      │
│      │  LangChain  │      │
│      │  + LLM      │      │
│      └──────┬──────┘      │
│             │             │
│       Tool Selection      │
│             │             │
│  ┌──────────▼──────────┐  │
│  │ Business Analytics  │  │
│  │ Customer / Order    │  │
│  │ Product / Sales     │  │
│  │ Inventory / etc.    │  │
│  └─────────────────────┘  │
└─────────────┬─────────────┘
              │
              ▼
          MongoDB
```

## 🔀 Intelligent Routing

Before executing business tools, the agent determines which domain is required to answer the user's question.

For example:

```text
"How many customers do I have?"
        ↓
Customer Information

"How many customers have completed orders?"
        ↓
Customer Analysis

"Which products sold the most?"
        ↓
Product Analysis

"How much revenue did we make this month?"
        ↓
Sales Analysis
```

The routing system can also select multiple domains when a question requires information from different sources.

## 💬 Conversation Management

Each conversation is associated with a unique **thread ID**.

LangGraph checkpoints are persisted using `MongoDBSaver`, allowing the agent to maintain context across requests and conversations.

```text
User Message
     ↓
Thread ID
     ↓
LangGraph
     ↓
Previous Conversation State
     ↓
Agent Response
```

Conversations can be created, retrieved, and deleted through the service's API.

## 🔌 Integration

This project is designed as a **backend AI service**, not as a standalone application with its own user interface.

Another application communicates with the service through HTTP requests.

Example:

```text
POST /api/agent/chat
```

Request:

```json
{
  "message": "How many customers have completed orders?",
  "organization_id": "...",
  "thread_id": "..."
}
```

The service processes the request, selects the required tools, queries the business data, and returns the AI-generated response.

## 🛡️ Access & Limits

Access control is handled by the application consuming this service rather than by the AI service itself.

The connected application can control:

* User plans
* AI availability
* Organization access
* Daily message limits
* Conversation limits

The AI service focuses on **agent execution, business analysis, and conversation state management**.

## 📁 Project Structure

A simplified structure:

```text
📂app
┣ 📂database
┃ ┗ 📜DbConnection.py
┣ 📂routes
┃ ┗ 📜agent.py
┣ 📂tools
┃ ┣ 📂analytics
┃ ┃ ┣ 📜customers_analysis.py
┃ ┃ ┣ 📜inventory_analysis.py
┃ ┃ ┣ 📜orders_analysis.py
┃ ┃ ┣ 📜overview_analytics.py
┃ ┃ ┣ 📜products_analysis.py
┃ ┃ ┗ 📜sales_analysis.py
┃ ┣ 📜customers.py
┃ ┣ 📜orders.py
┃ ┗ 📜products.py
┣ 📂utils
┃ ┗ 📜dates.py
┣ 📜graph.py
┣ 📜llm.py
┣ 📜main.py
┣ 📜router.py
┣ 📜state.py
┗ 📜summarizer.py

```

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd LangGraph-AI-Agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

**Windows:**

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file containing the required configuration, such as:

```env
MONGODB_URI=your_mongodb_connection_string
MONGODB_DATABASE=your_database
GROQ_API_KEY=your_groq_api_key
```

### 6. Run the service

```bash
uvicorn main:app --reload
```

The FastAPI service will then be available locally.

## 🎯 Project Goal

The goal of this project is to build a **modular AI agent capable of interacting with real business data through natural language**, while maintaining conversation context and selecting the appropriate analytical tools automatically.

The service can be integrated into existing SaaS or business management applications without requiring the AI logic to be implemented directly inside the main application.
