# 🧠 unHabit - AI-Driven Behavioral Recovery Platform

<div align="center">

![unHabit Logo](https://via.placeholder.com/200x200/4CAF50/FFFFFF?text=unHabit)

**Your journey to better habits starts here**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29.0-FF4B4B.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [API Docs](#-api-documentation)

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup-fastapi)
  - [Frontend Setup](#frontend-setup-streamlit)
  - [Docker Setup](#docker-setup-optional)
- [Configuration](#-configuration)
  - [Environment Variables](#environment-variables)
  - [API Keys](#api-keys-setup)
  - [n8n Workflow](#n8n-workflow-setup)
- [Usage](#-usage)
  - [Running the Application](#running-the-application)
  - [Using the Web Interface](#using-the-web-interface)
  - [API Examples](#api-examples)
- [Multi-Agent System](#-multi-agent-system)
- [API Documentation](#-api-documentation)
- [Deployment](#-deployment)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

## 🌟 Overview

**unHabit** is an AI-powered behavioral recovery platform designed to help individuals overcome addictive behaviors and build healthier habits. Using advanced LLM-based agents, unHabit provides personalized support through:

- 🧠 **Reflective Conversations** - Empathetic AI-driven dialogue to explore thoughts and patterns
- 🎯 **Goal Generation** - Automated creation of actionable, personalized goals
- 🤝 **Community Discovery** - AI-powered search for relevant support groups
- 📊 **Progress Tracking** - Comprehensive analytics and visualizations
- 📅 **Calendar Integration** - Automatic goal scheduling via n8n & Google Calendar

### Target Behaviors

unHabit helps manage and recover from:
- Social media addiction and excessive screen time
- Procrastination and task avoidance
- Overeating and unhealthy eating patterns
- Eating disorders and food-related anxiety
- Other behavioral addictions

---

## ✨ Features

### Core Capabilities

- **🤖 Multi-Agent AI System**
  - 4 specialized agents working in concert
  - Memory-aware conversations with context retention
  - Personalized insights based on user history

- **💬 Intelligent Reflection Sessions**
  - Natural language conversations
  - Empathetic responses and reflective questions
  - Automatic session summarization
  - Pause/resume functionality

- **🎯 Smart Goal Planning**
  - AI-generated SMART goals from reflections
  - Priority-based scheduling (high/medium/low)
  - Recurrence patterns (daily/weekly/monthly)
  - Google Calendar synchronization

- **🔍 Community Discovery**
  - Web search integration via Serper API
  - Filtered and ranked recommendations
  - Support for Reddit, Discord, Forums, Facebook Groups
  - User feedback collection

- **📊 Progress Analytics**
  - Real-time statistics dashboard
  - Visual charts and graphs (Plotly)
  - Emotional pattern tracking
  - Achievement system with badges

- **🗄️ Persistent Memory**
  - Vector database (ChromaDB) for semantic search
  - Long-term user state tracking
  - Historical reflection summaries
  - Goal completion history

### User Interface

- **🎨 Beautiful Streamlit UI**
  - Calming green theme with dark mode
  - Responsive design (mobile-friendly)
  - Chat-style interface
  - Card-based community display
  - Interactive charts and visualizations

- **⚡ FastAPI Backend**
  - RESTful API with automatic documentation
  - Real-time processing
  - Background task handling
  - Health monitoring endpoints

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI (Frontend)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Home   │  │Reflection│  │ Support  │  │Dashboard │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST API
┌────────────────────────▼────────────────────────────────────┐
│                  FASTAPI BACKEND (API Layer)                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Agent Orchestration                      │   │
│  │  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌─────────┐│   │
│  │  │Reflector│  │Goal Plan │  │Support │  │Assessor ││   │
│  │  │ Agent   │  │  Agent   │  │ Agent  │  │ Agent   ││   │
│  │  └─────────┘  └──────────┘  └────────┘  └─────────┘│   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────┬───────────────┬──────────────┬────────────────┘
              │               │              │
    ┌─────────▼────┐  ┌──────▼──────┐  ┌───▼─────┐
    │   ChromaDB   │  │   Gemini    │  │ Serper  │
    │   (Vector)   │  │ 2.5 Flash   │  │  (Web)  │
    └──────────────┘  └─────────────┘  └─────────┘
              │
         ┌────▼─────┐
         │   n8n    │
         │(Calendar)│
         └──────────┘
              │
         ┌────▼─────┐
         │  Google  │
         │ Calendar │
         └──────────┘
```

### Multi-Agent Architecture

1. **Reflections Agent** (Read-Only Memory Access)
   - Primary user interface for conversations
   - Retrieves past context from ChromaDB
   - Generates session summaries
   - Forwards summaries to Goal Planner

2. **Goal Planner Agent** (No Direct Memory Access)
   - Receives reflection summaries
   - Generates actionable goals using LLM
   - Sends tasks to n8n webhook
   - Reports to Assessment Agent

3. **Support Agent** (No Direct Memory Access)
   - Searches for communities via Serper API
   - Filters and ranks results
   - Collects user feedback
   - Reports to Assessment Agent

4. **Assessment Agent** (Exclusive Write Access)
   - Aggregates data from all agents
   - Performs comprehensive analysis
   - Updates ChromaDB with insights
   - Maintains user state representations

### Data Flow

```
User Input → Reflection Agent → Context Retrieval (ChromaDB)
                    ↓
              LLM Processing (Gemini)
                    ↓
             Response to User
                    ↓
         Session End → Summary Generated
                    ↓
          Goal Planner Agent
                    ↓
         Goals Generated (LLM)
                    ↓
              n8n Webhook
                    ↓
          Google Calendar Events
                    ↓
          Assessment Agent
                    ↓
     Memory Update (ChromaDB Write)
```

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.109.0
- **LLM Orchestration**: LangChain 0.1.4
- **AI Models**: 
  - Google Gemini 2.5 Flash (primary)
  - Groq Mixtral 8x7B (backup)
- **Vector Database**: ChromaDB 0.4.22
- **Web Search**: Serper API
- **Automation**: n8n (self-hosted or cloud)

### Frontend
- **Framework**: Streamlit 1.29.0
- **Visualization**: Plotly 5.18.0
- **Data Processing**: Pandas 2.1.4

### External Integrations
- **Calendar**: Google Calendar via n8n
- **Search**: Serper.dev API
- **Embeddings**: Google Generative AI Embeddings

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **HTTP Client**: Requests 2.31.0
- **Environment**: Python-dotenv 1.0.0

---

## 📁 Project Structure

```
unhabit/
├── 📄 main.py                      # FastAPI application entry point
├── 📄 agents.py                    # All 4 agent implementations
├── 📄 llm_provider.py              # LLM manager (Gemini + Groq fallback)
├── 📄 memory.py                    # ChromaDB manager with access control
├── 📄 vector_tool.py               # Vector upload tool (Assessment only)
├── 📄 serper_tool.py               # Serper API wrapper
├── 📄 prompts.py                   # System prompts for all agents
│
├── 📄 Home.py                      # Streamlit main entry point
├── 📁 pages/                       # Streamlit pages
│   ├── 1_💬_Reflection.py         # Reflection chat interface
│   ├── 2_🔍_Support.py            # Community search page
│   └── 3_📊_Dashboard.py          # Progress dashboard
│
├── 📁 .streamlit/                  # Streamlit configuration
│   ├── secrets.toml               # API keys (don't commit!)
│   └── config.toml                # UI theme configuration
│
├── 📄 requirements.txt             # Backend Python dependencies
├── 📄 requirements-streamlit.txt   # Frontend dependencies
├── 📄 .env                         # Environment variables (don't commit!)
├── 📄 .env.example                # Environment template
│
├── 📄 Dockerfile                   # Docker container definition
├── 📄 docker-compose.yml          # Multi-container orchestration
├── 📄 Makefile                    # Convenience commands
│
├── 📁 chroma_db/                  # Vector database storage (auto-created)
│   ├── user_reflections/
│   ├── user_goals/
│   ├── user_states/
│   └── user_interactions/
│
├── 📁 logs/                       # Application logs (auto-created)
├── 📁 backups/                    # Database backups (auto-created)
│
├── 📄 README.md                   # This file
├── 📄 LICENSE                     # License information
└── 📄 .gitignore                  # Git ignore rules
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **pip** (comes with Python)
- **Git** ([Download](https://git-scm.com/))
- **API Keys**:
  - Google Gemini API ([Get key](https://makersuite.google.com/app/apikey))
  - Serper API ([Get key](https://serper.dev))
  - (Optional) Groq API ([Get key](https://console.groq.com))
  - (Optional) n8n Cloud account ([Sign up](https://n8n.io))

### Backend Setup (FastAPI)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/unhabit.git
cd unhabit

# 2. Create virtual environment
python -m venv venv

# Activate on macOS/Linux:
source venv/bin/activate

# Activate on Windows:
venv\Scripts\activate

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Create environment file
cp .env.example .env

# 5. Edit .env with your API keys
nano .env  # or use your preferred editor

# 6. Run the backend
python main.py
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Frontend Setup (Streamlit)

```bash
# 1. Install Streamlit dependencies
pip install -r requirements-streamlit.txt

# 2. Create Streamlit configuration directory
mkdir -p .streamlit

# 3. Create secrets file
touch .streamlit/secrets.toml

# 4. Add your API keys to .streamlit/secrets.toml
nano .streamlit/secrets.toml

# Add:
# API_BASE_URL = "http://localhost:8000"
# GEMINI_API_KEY = "your_key_here"
# SERPER_API_KEY = "your_key_here"

# 5. Create config file
cp .streamlit/config.toml.example .streamlit/config.toml

# 6. Run Streamlit (in a new terminal)
streamlit run Home.py
```

The UI will open automatically at http://localhost:8501

### Docker Setup (Optional)

```bash
# 1. Build the image
docker-compose build

# 2. Start services
docker-compose up -d

# 3. Check logs
docker-compose logs -f

# 4. Stop services
docker-compose down
```

Access:
- **API**: http://localhost:8000
- **UI**: http://localhost:8501

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# LLM API Keys
GEMINI_API_KEY=AIzaSy...your_gemini_key
GOOGLE_API_KEY=AIzaSy...alternative_to_gemini
GROQ_API_KEY=gsk_...your_groq_key_optional

# Search API
SERPER_API_KEY=your_serper_key_here

# n8n Webhook (for Google Calendar integration)
N8N_WEBHOOK_URL=https://yourname.app.n8n.cloud/webhook/unhabit

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Database
CHROMA_PERSIST_DIR=./chroma_db
```

### API Keys Setup

#### 1. Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API Key"
4. Copy key (starts with `AIzaSy...`)
5. Add to `.env`: `GEMINI_API_KEY=your_key`

#### 2. Serper API Key

1. Go to [Serper.dev](https://serper.dev)
2. Sign up (free tier: 2,500 searches/month)
3. Go to Dashboard → API Key
4. Copy your key
5. Add to `.env`: `SERPER_API_KEY=your_key`

#### 3. Groq API Key (Optional Backup)

1. Go to [Groq Console](https://console.groq.com)
2. Sign up for account
3. Create API key
4. Add to `.env`: `GROQ_API_KEY=gsk_your_key`

### n8n Workflow Setup

#### Option 1: n8n Cloud

1. **Sign up at [n8n.io](https://n8n.io)**

2. **Create New Workflow**:
   - Click "+ New Workflow"
   - Name it "unHabit - Goal to Calendar"

3. **Add Webhook Node**:
   - Drag "Webhook" node to canvas
   - Set HTTP Method: `POST`
   - Set Path: `unhabit`
   - Click "Listen for Test Event"

4. **Add Google Calendar Node**:
   - Drag "Google Calendar" node
   - Connect to webhook
   - Action: "Create Event"
   - Configure:
     - Calendar: `primary`
     - Start: `{{DateTime.now().plus({hours: 2}).toISO()}}`
     - End: `{{DateTime.now().plus({hours: 2, minutes: $json["duration"] || 30}).toISO()}}`
     - Summary: `{{$json["summary"]}}`
     - Description: `{{$json["description"]}}`

5. **Authenticate Google Calendar**:
   - Click "Create Credential"
   - Follow OAuth flow
   - Grant calendar permissions

6. **Get Webhook URL**:
   - After saving, copy Production URL
   - Format: `https://yourname.app.n8n.cloud/webhook/unhabit`
   - Add to `.env`: `N8N_WEBHOOK_URL=...`

7. **Activate Workflow**:
   - Toggle switch in top-right to "Active"

#### Option 2: Self-Hosted n8n

```bash
# Install n8n
npm install -g n8n

# Run n8n
n8n start

# Access at http://localhost:5678
# Create workflow as above
```

---

## 📖 Usage

### Running the Application

#### Development Mode (Recommended)

**Terminal 1 - Backend:**
```bash
python main.py
```

**Terminal 2 - Frontend:**
```bash
streamlit run Home.py
```

#### Production Mode

```bash
# Using Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Or using system services (see deployment section)
```

### Using the Web Interface

#### 1. Start a Reflection

1. Open http://localhost:8501
2. Click "💬 Start Reflection"
3. Click "🟢 Start New Session"
4. Type your thoughts (e.g., "I've been scrolling social media for hours")
5. Click "📤 Send"
6. Continue conversation with AI
7. Click "🔴 End Session & Generate Goals"
8. View your personalized goals

#### 2. Find Support Communities

1. Click "🔍 Support" in sidebar
2. Enter search query (e.g., "social media addiction support")
3. Select category
4. Click "🔍 Search Communities"
5. Browse card-based results
6. Click links to visit communities
7. Provide feedback (✅ Helpful / ⭐ Interested / ❌ Not Relevant)

#### 3. Track Progress

1. Click "📊 Dashboard" in sidebar
2. View overview metrics
3. Explore activity charts
4. Review emotional patterns
5. Read reflection summaries
6. Check achievements

### API Examples

#### Start Reflection

```bash
curl -X POST "http://localhost:8000/api/reflection/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "content": "I have been procrastinating on my work"
  }'
```

Response:
```json
{
  "response": "I hear you. Procrastination can feel overwhelming. What specifically are you putting off, and what do you think might be behind that?",
  "timestamp": "2024-01-15T10:30:00"
}
```

#### Continue Reflection

```bash
curl -X POST "http://localhost:8000/api/reflection/continue" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "content": "I keep avoiding a big project that feels too daunting"
  }'
```

#### End Session & Get Goals

```bash
curl -X POST "http://localhost:8000/api/reflection/end?user_id=user123"
```

Response:
```json
{
  "summary": {
    "summary": "User struggling with procrastination on large project due to feeling overwhelmed",
    "emotional_tone": "anxious but motivated",
    "key_themes": ["procrastination", "overwhelm", "large projects"],
    "insights": ["Breaking tasks into smaller pieces might help"]
  },
  "goals": [
    {
      "title": "Break project into 3 small tasks",
      "description": "Spend 10 minutes listing 3 concrete mini-tasks for the project",
      "priority": "high",
      "duration_minutes": 10,
      "recurrence": null
    }
  ],
  "calendar_sync": {
    "status": "success",
    "tasks_sent": 3
  }
}
```

#### Search Communities

```bash
curl -X POST "http://localhost:8000/api/support/search" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "query": "procrastination recovery",
    "addiction_type": "Procrastination"
  }'
```

#### Get User Stats

```bash
curl "http://localhost:8000/api/stats/user123"
```

Response:
```json
{
  "user_id": "user123",
  "total_reflections": 5,
  "total_goals": 12,
  "total_interactions": 3,
  "current_state": "User showing progress with procrastination management...",
  "timestamp": "2024-01-15T10:35:00"
}
```

---

## 🤖 Multi-Agent System

### Agent Responsibilities

| Agent | Read Access | Write Access | Primary Function |
|-------|-------------|--------------|------------------|
| **Reflections** | ChromaDB (read) | None | User conversations, context retrieval |
| **Goal Planner** | None | None | Goal generation, n8n integration |
| **Support** | None | None | Community search, feedback collection |
| **Assessment** | ChromaDB (read) | ChromaDB (write) | Data aggregation, memory updates |

### Memory Architecture

**Strict Access Control:**
- Only Assessment Agent can write to ChromaDB
- Reflections Agent retrieves context (read-only)
- Goal Planner & Support Agents report to Assessment
- Assessment compresses and stores insights

**Collections:**
```
ChromaDB/
├── user_reflections/     # Reflection summaries
├── user_goals/           # Generated goals
├── user_states/          # Compressed user states
└── user_interactions/    # Support feedback
```

### Communication Flow

```
┌─────────────┐
│ Reflections │──reads──▶ ChromaDB
└──────┬──────┘
       │ generates summary
       ▼
┌─────────────┐
│Goal Planner │──sends──▶ n8n ──▶ Google Calendar
└──────┬──────┘
       │ reports metadata
       ▼
┌─────────────┐           ┌─────────┐
│  Support    │──reports─▶│Assessment│──writes──▶ ChromaDB
└─────────────┘           └─────────┘
```

---

## 📚 API Documentation

### Interactive Documentation

Once running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Overview

#### Health & Status
- `GET /` - Root endpoint
- `GET /api/health` - System health check

#### Reflection
- `POST /api/reflection/start` - Start new session
- `POST /api/reflection/continue` - Continue conversation
- `POST /api/reflection/end` - End session & generate goals

#### Support
- `POST /api/support/search` - Search communities
- `POST /api/support/feedback` - Submit feedback

#### Goals
- `GET /api/goals/pending/{user_id}` - Get pending goals
- `POST /api/goals/resync/{user_id}` - Resync to calendar

#### Analytics
- `GET /api/stats/{user_id}` - User statistics
- `POST /api/assessment/process/{user_id}` - Trigger assessment

#### Debug (Development Only)
- `GET /api/debug/agents` - Agent status
- `DELETE /api/debug/clear/{user_id}` - Clear session

---

## 🌐 Deployment

### Deploy to Streamlit Cloud

```bash
# 1. Push to GitHub
git add .
git commit -m "Deploy unHabit"
git push origin main

# 2. Go to streamlit.io/cloud
# 3. Click "New app"
# 4. Connect GitHub repo
# 5. Set main file: Home.py
# 6. Add secrets in dashboard:
#    API_BASE_URL=your_deployed_backend_url
#    GEMINI_API_KEY=your_key
#    SERPER_API_KEY=your_key
# 7. Deploy!
```

### Deploy Backend to Railway

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Initialize project
railway init

# 4. Add environment variables
railway variables set GEMINI_API_KEY=your_key
railway variables set SERPER_API_KEY=your_key
railway variables set N8N_WEBHOOK_URL=your_url

# 5. Deploy
railway up
```

### Deploy to Render

1. Create `render.yaml` (already in repo)
2. Connect GitHub to Render
3. Add environment variables in dashboard
4. Deploy automatically on push

### Deploy with Docker

```bash
# Build image
docker build -t unhabit:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name unhabit-api \
  unhabit:latest

# Or use docker-compose
docker-compose up -d
```

---

## 👨‍💻 Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

### Code Structure

```python
# agents.py
class ReflectionsAgent:
    """Handles user conversations"""
    
class GoalPlannerAgent:
    """Generates goals from reflections"""
    
class SupportAgent:
    """Discovers communities"""
    
class AssessmentAgent:
    """Updates memory and tracks state"""

# llm_provider.py
class LLMManager:
    """Manages Gemini/Groq with fallback"""

# memory.py
class ChromaDBManager:
    """Vector database with access control"""
```

### Adding New Features

1. **New Agent Capability**:
   ```python
   # In agents.py
   def new_agent_method(self):
       # Your implementation
       pass
   ```

2. **New API Endpoint**:
   ```python
   # In main.py
   @app.post("/api/new/endpoint")
   async def new_endpoint():
       # Your implementation
       pass
   ```

3. **New Streamlit Page**:
   ```python
   # In pages/4_🆕_NewPage.py
   import streamlit as st
   st.title("New Feature")
   ```

---

## 🐛 Troubleshooting

### Common Issues

#### "GEMINI_API_KEY not found"
```bash
# Check .env exists
ls -la .env

# Verify format (no spaces, no quotes)
cat .env

# Solution
cp .env.example .env
nano .env  # Add your key
```

#### "Cannot connect to API"
```bash
# Check FastAPI is running
curl http://localhost:8000/api/health

# Check logs
tail -f logs/unhabit.log

# Restart
python main.py
```

#### "ChromaDB errors"
```bash
# Delete and recreate
rm -rf chroma_db/
python main.py  # Auto-recreates
```

#### "n8n webhook fails"
```bash
# Test webhook directly
curl -X POST "your_n8n_url" \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'

# Check n8n workflow is Active
# Verify URL in .env matches n8n
```

#### "Streamlit secrets not found"
```bash
# Create secrets file
mkdir -p .streamlit
touch .streamlit/secrets.toml

# Add configuration
nano .streamlit/secrets.toml
```

### Debug Mode

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set in .env
LOG_LEVEL=DEBUG
```

### Getting Help

1. Check [GitHub Issues](https://github.com/yourusername/unhabit/issues)
2. Review API docs: http://localhost:8000/docs
3. Enable debug mode for detailed logs
4. Check system requirements are met

---

## 🤝 Contributing

We welcome contributions! Here's how:

### Fork & Setup

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/unhabit.git
cd unhabit
git checkout -b feature/your-feature-name
```

### Development Workflow

1. Create feature branch
2. Make changes
3. Add tests
4. Update documentation
5. Run tests: `pytest`
6. Commit: `git commit -m "Add: your feature"`
7. Push: `git push origin feature/your-feature-name`
8. Create Pull Request

### Code Standards

- Follow PEP 8 for Python
- Add docstrings to functions
- Include type hints
- Write tests for new features
- Update README if needed

### Areas for Contribution

- 🎨 UI/UX improvements
- 🧪 Additional test coverage
- 📝 Documentation enhancements
- 🌐 Internationalization (i18n)
- 🔌 New integrations (Notion, Todoist, etc.)
- 🎯 New agent capabilities
- 🐛 Bug fixes

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 unHabit Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files...
```

---

## 🙏 Acknowledgments

### Technologies
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [LangChain](https://langchain.com/) - LLM orchestration
- [Streamlit](https://streamlit.io/) - Beautiful web apps
- [Google Gemini](https://ai.google.dev/) - Advanced AI model
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [n8n](https://n8n.io/) - Workflow automation

### Inspiration
- Behavioral psychology research
- Recovery community feedback
- Mental health best practices
- AI safety principles

### Contributors
- Your name here! See [Contributing](#-contributing)

---

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/raevmood/unhabit/issues)
- **Discussions**: