# 🚀 Instant Media Release

AI-powered press release automation system for Vietnamese SMEs using **Agno AI Multi-Agent framework**.

## ✨ Features

- **🤖 4 Specialized AI Agents**: Content Analysis → Media Matching → Pricing → Reporting
- **📱 Interactive Chatbot**: 7-step data collection flow
- **🎯 Smart Media Recommendations**: Vector search through Vietnamese media database
- **💰 Intelligent Pricing**: Automated package optimization (Starter/Standard/Premium)
- **📊 Comprehensive Reports**: Executive-level insights and actionable next steps
- **⚡ Lightning Fast**: Agno framework - 10,000x faster than LangGraph

## 🏗️ Architecture

```
Frontend (demo.html) 
    ↓ WebSocket + REST API
FastAPI Server (main.py)
    ↓ Multi-Agent Processing
Agno AI Agents (agents.py)
    ↓ Vector Search + Analysis  
Media Database (database.py)
    ↓ SQLite + ChromaDB
Vietnamese Media Data
```

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone <repo-url>
cd instant-media-release

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key (choose one):
# GROQ_API_KEY=your_groq_key        (Recommended - Free)
# OPENAI_API_KEY=your_openai_key    (Alternative)
```

### 3. Initialize Database

```bash
# This will create SQLite database with Vietnamese media data
python database.py
```

### 4. Start Server

```bash
# Development server
python main.py

# Production server
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. Test the System

- **Demo Chatbot**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Quick Test**: http://localhost:8000/api/demo/quick-test

## 📊 Sample Media Database

Pre-loaded with 8 real Vietnamese media outlets:

| Media | Tier | Cost (VND) | Circulation | Language |
|-------|------|------------|-------------|----------|
| VnExpress | 1 | 15M | 30M | Vietnamese |
| ZNews | 1 | 12M | 25M | Vietnamese |
| Kenh14 | 1 | 10M | 20M | Vietnamese |
| VietnamNet | 1 | 8M | 15M | Vietnamese |
| Tuoi Tre | 1 | 9M | 18M | Vietnamese |
| CafeF | 2 | 5M | 8M | Vietnamese |
| CafeBiz | 2 | 4.5M | 6M | Vietnamese |
| Vietnam News | 2 | 6M | 3M | English |

## 🤖 AI Agents Workflow

### 1. Content Analysis Agent
```python
# Analyzes user input and extracts:
- Language (Vietnamese/English/Both)
- Topics and categories
- Target audience segments
- Content tone and urgency
- Keywords for media matching
```

### 2. Media Recommendation Agent
```python
# Uses vector search to find best matches:
- Semantic similarity matching
- Budget constraint filtering
- Credibility scoring (Tier 1 > Tier 2)
- Audience alignment analysis
```

### 3. Pricing Optimization Agent
```python
# Calculates optimal package:
- Starter: 12M VND (1-3 days, 2-3 outlets)
- Standard: 30M VND (5-7 days, 12-15 outlets)
- Premium: 50M VND (10-14 days, 15-18 outlets)
```

### 4. Report Generation Agent
```python
# Creates comprehensive strategy:
- Executive summary
- Strategic media plan
- Cost-benefit analysis
- Success KPIs
- Actionable next steps
```

## 📡 API Endpoints

### Chatbot Flow
```bash
POST /api/chat/start              # Start new session
POST /api/chat/answer             # Submit answer
GET  /api/chat/session/{id}       # Get session status
```

### AI Processing
```bash
POST /api/agents/process          # Trigger AI agents
GET  /api/agents/result/{id}      # Get processing result
```

### Utilities
```bash
GET  /api/media/search?query=     # Search media outlets
GET  /api/media/list              # List all media
POST /api/demo/quick-test         # Quick demo
```

### WebSocket
```bash
WS   /ws/{session_id}             # Real-time updates
```

## 🧪 Testing Examples

### Manual API Testing

```bash
# 1. Start chat session
curl -X POST http://localhost:8000/api/chat/start

# 2. Submit answers (repeat for all 7 questions)
curl -X POST http://localhost:8000/api/chat/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": 1,
    "answer": "Tôi chưa có",
    "session_id": "your-session-id"
  }'

# 3. Process with AI agents
curl -X POST http://localhost:8000/api/agents/process \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "user_data": {...},
    "budget": 30000000
  }'

# 4. Get final result
curl http://localhost:8000/api/agents/result/your-session-id
```

### Demo Test

```bash
# Quick end-to-end test
curl -X POST http://localhost:8000/api/demo/quick-test
```

## 📁 Project Structure

```
instant-media-release/
├── main.py              # FastAPI server + chatbot endpoints
├── agents.py            # 4 Agno AI agents + multi-agent workflow  
├── database.py          # SQLite models + Vietnamese media data
├── demo.html            # Beautiful chatbot interface
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── README.md           # This file

# Generated files (auto-created)
├── media_release.db     # SQLite database
├── agent_memory.db      # Agent memory storage
└── chroma_db/          # Vector database
```

## 🔧 Configuration Options

### Environment Variables
```bash
# Required (choose one)
GROQ_API_KEY=           # Groq Llama-3.3-70B (recommended)
OPENAI_API_KEY=         # OpenAI GPT-4o-mini (backup)

# Optional
DATABASE_URL=           # Default: sqlite:///./media_release.db
HOST=                   # Default: 0.0.0.0
PORT=                   # Default: 8000
DEBUG=                  # Default: True
LOG_LEVEL=              # Default: INFO
```

### Package Pricing
```python
# Modify in agents.py
PACKAGES = {
    "Starter": {"price": 12000000, "timeline": "1-3 days"},
    "Standard": {"price": 30000000, "timeline": "5-7 days"}, 
    "Premium": {"price": 50000000, "timeline": "10-14 days"}
}
```

## 🚀 Production Deployment

### Docker (Recommended)
```bash
# Create Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Build and run
docker build -t instant-media-release .
docker run -p 8000:8000 --env-file .env instant-media-release
```

### AWS Lightsail
```bash
# Install dependencies
sudo apt update && sudo apt install python3-pip
pip3 install -r requirements.txt

# Setup systemd service
sudo nano /etc/systemd/system/media-release.service

# Start service
sudo systemctl enable media-release
sudo systemctl start media-release
```

## 🔍 Troubleshooting

### Common Issues

**1. Import Error: agno not found**
```bash
pip install agno --upgrade
```

**2. Vector Database Error**
```bash
# Delete and recreate
rm -rf chroma_db/
python database.py
```

**3. API Key Error**
```bash
# Check environment
echo $GROQ_API_KEY
# or
echo $OPENAI_API_KEY
```

**4. Database Lock Error**
```bash
# Reset database
rm media_release.db agent_memory.db
python database.py
```

### Performance Optimization

**1. Use Groq instead of OpenAI**
- 10x faster response time
- Free tier available
- Better for Vietnamese content

**2. Increase Agent Concurrency**
```python
# In agents.py
async def process_parallel():
    tasks = [
        agent1.arun(prompt1),
        agent2.arun(prompt2),
        agent3.arun(prompt3)
    ]
    results = await asyncio.gather(*tasks)
```

## 📈 Extending the System

### Add New Media Outlets
```python
# In database.py SAMPLE_MEDIA_DATA
{
    "name": "New Media",
    "publisher": "Publisher Name",
    "circulation": 5000000,
    "tier": 2,
    "cost_per_article": 3000000,
    "topics": ["Technology", "Business"],
    "target_audience": ["Tech Enthusiasts"]
}
```

### Custom AI Models
```python
# In agents.py
from agno.models.anthropic import Claude
from agno.models.google import Gemini

# Use different models per agent
content_agent = Agent(model=Claude(...))
pricing_agent = Agent(model=Gemini(...))
```

### Additional Tools
```python
# Add tools to agents
from agno.tools.email import EmailTools
from agno.tools.calendar import CalendarTools

agent = Agent(
    tools=[DuckDuckGoTools(), EmailTools(), CalendarTools()]
)
```

## 📞 Support

- **Documentation**: Check `/docs` endpoint
- **Issues**: Create GitHub issue
- **Performance**: Monitor via agent logs
- **Custom Development**: Contact development team

## 📄 License

MIT License - See LICENSE file for details.

---

**Built with ❤️ using Agno AI Framework**

🚀 **Ready to revolutionize PR automation for Vietnamese SMEs!**