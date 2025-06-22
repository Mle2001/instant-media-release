# 🚀 Instant Media Release - Conversational AI System

**AI-powered conversational press release automation for Vietnamese SMEs using Agno AI Multi-Agent framework with real-time interaction.**

## ✨ New Features (v3.0)

- **🤖 7 Specialized Conversational AI Agents**: Natural Vietnamese conversation → Content Analysis → Document Processing → Media Matching → Pricing → Reporting → Plan Modification
- **💬 Natural Vietnamese Conversation**: Interactive chatbot with contextual understanding and memory
- **📱 Real-time WebSocket Updates**: Live progress tracking and instant results delivery
- **📄 Document Upload & Analysis**: PDF/DOC processing with AI-powered content extraction
- **🎯 Smart Media Recommendations**: Vector search through 100+ Vietnamese media outlets database
- **💰 Intelligent Pricing**: Automated package optimization with conversation context
- **📊 Interactive Results Display**: Rich UI with detailed analysis breakdown
- **🔄 Plan Modification**: Real-time plan adjustments based on user feedback
- **⚡ Lightning Fast**: Agno framework with async processing and WebSocket communication

## 🏗️ Enhanced Architecture

```
Frontend (Conversational UI)
    ↓ WebSocket + REST API
FastAPI Server (Real-time)
    ↓ Multi-Agent Orchestration
7 Agno AI Agents (Conversational)
    ↓ Vector Search + Analysis
Enhanced Database (100+ Media)
    ↓ SQLite + ChromaDB + Document Store
Vietnamese Media Ecosystem
```

## 🤖 Conversational AI Agents

### 1. **Conversation Agent** - Vietnamese PR Consultant
```python
# Manages natural conversation flow
- Greets users in Vietnamese
- Extracts project information through dialogue
- Understands context and intent
- Guides users through the process
- Handles questions and clarifications
```

### 2. **Content Analysis Agent** - Content Strategist
```python
# Analyzes user input with conversation context
- Language detection (Vietnamese/English/Both)
- Industry classification (Tech/Finance/Health/etc)
- Target audience identification (SME/Youth/B2B)
- Content tone and urgency assessment
- Keyword extraction for media matching
- Confidence scoring (0-1)
```

### 3. **Document Analysis Agent** - Document Processor
```python
# Processes uploaded files with conversation awareness
- PDF/DOC/DOCX content extraction
- Key information identification
- Media angle suggestions
- Supporting data extraction
- Content quality assessment
- Document-conversation alignment
```

### 4. **Media Matching Agent** - Vietnamese Media Expert
```python
# Matches content with optimal media outlets
- Vector semantic search (100+ outlets)
- Budget constraint filtering
- Tier-based credibility scoring (Tier-1: VnExpress, 24H)
- Audience alignment analysis
- Language compatibility check
- Success rate prediction
```

### 5. **Pricing Optimization Agent** - Business Strategist
```python
# Calculates optimal packages with conversation context
- Starter: 12M VND (1-3 days, 2-3 tier-2 outlets)
- Standard: 30M VND (5-7 days, 12-15 outlets with tier-1)
- Premium: 50M VND (10-14 days, 15-18 outlets + interviews)
- ROI projection and budget utilization
- Timeline optimization
```

### 6. **Report Generation Agent** - Executive Consultant
```python
# Creates comprehensive strategy reports
- Executive summary with key insights
- Strategic media plan with implementation steps
- Success metrics and KPIs
- Risk mitigation strategies
- Competitive advantage analysis
- Personalized recommendations
```

### 7. **Plan Modification Agent** - Adaptation Specialist
```python
# Handles real-time plan modifications
- User feedback analysis
- Feasibility assessment
- Alternative solution generation
- Cost-benefit impact calculation
- Plan coherence maintenance
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone repository
git clone <repo-url>
cd instant-media-release

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 2. Required API Keys

```bash
# Choose one AI provider (in .env file):
OPENAI_API_KEY=sk-proj-your_openai_key    # Recommended for production
# OR
GROQ_API_KEY=your_groq_key                # Fast & free alternative

# Optional configurations
DATABASE_URL=sqlite:///./media_release.db  # Default SQLite
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

### 3. Initialize & Start

```bash
# Initialize database with 100+ Vietnamese media outlets
python database.py

# Start conversational server
python main.py

# Server will be available at:
# 🌐 Demo: http://localhost:8000
# 📚 API Docs: http://localhost:8000/docs
# 🔍 Health: http://localhost:8000/health
```

## 📊 Enhanced Media Database

Pre-loaded with **100 real Vietnamese media outlets** with comprehensive analytics:

### Tier-1 Media (56 outlets)
| Media | Monthly Visits | Cost (VND) | Audience | Focus |
|-------|---------------|------------|----------|-------|
| **VnExpress** | 218M | 15M | General/Business | Mainstream news leader |
| **24H** | 86M | 12M | Male-dominant | Sports & entertainment |
| **Dân trí** | 60M | 10M | Education-focused | Society & education |
| **CafeF** | 28M | 8M | Business professionals | Finance & investing |
| **Tuổi trẻ** | 48M | 9M | Youth-oriented | Government & society |

### Tier-2 Media (29 outlets)
- Specialized industry publications
- Regional and local media
- Niche audience targeting

### Tier-3 Media (15 outlets)
- Local community media
- Startup and SME focused
- Cost-effective options

### Categories Available
- **MAINSTREAM** (26 outlets): VnExpress, 24H, Dân trí, Tuổi trẻ
- **BUSINESS** (24 outlets): CafeF, CafeBiz, VnEconomy, Forbes Vietnam
- **TECHNOLOGY** (8 outlets): Tinh tế, GenK, TechRum
- **YOUTH_ENTERTAINMENT** (10 outlets): Kênh 14, SaoStar, YAN News
- **WOMAN_FAMILY** (7 outlets): Eva, aFamily, Phụ nữ Việt Nam
- **HEALTH** (2 outlets): Sức khỏe và Đời sống, Alo Bác sĩ
- **AUTOMOTIVE** (6 outlets): Giao thông, AutoPro, Ô tô Sài Gòn
- **EDUCATION** (5 outlets): Giáo dục Thời đại, Hoa học trò
- **AGRICULTURE** (7 outlets): Dân Việt, Nông nghiệp & Môi trường
- **TOURISM** (1 outlet): Tạp chí Du lịch TP.HCM

## 💬 Conversational Flow

### User Journey
```
1. 🤝 Greeting → AI introduces itself as ChiCom AI PR consultant
2. 📝 Project Input → User describes project in natural Vietnamese
3. 💰 Budget Discussion → AI helps determine appropriate budget range
4. 🎯 Goals Clarification → AI understands objectives (awareness/leads/credibility)
5. 📄 Document Upload → Optional: Upload supporting documents
6. 🚀 AI Analysis → Real-time progress with 7 specialized agents
7. 📊 Results Review → Interactive report with detailed recommendations
8. 🔄 Plan Modification → Real-time adjustments based on feedback
9. ✅ Approval → Final plan approval and next steps
```

### Sample Conversation
```
User: "Chúng tôi là startup fintech VietPay phát triển app thanh toán cho SME"

AI: "Tuyệt! Fintech cho SME là lĩnh vực rất tiềm năng. Để tôi hiểu rõ hơn về VietPay:
    • Bạn muốn tăng awareness hay thu hút khách hàng cụ thể?
    • Ngân sách dự kiến cho chiến dịch truyền thông?
    • Timeline mong muốn?"

User: "Ngân sách 30 triệu, muốn tăng awareness trong 2 tuần"

AI: "Perfect! Với 30 triệu và timeline 2 tuần, tôi có thể tạo chiến lược Standard Package 
    targeting báo chí tier-1 như VnExpress, CafeF. Bạn có muốn tôi bắt đầu phân tích AI không?"

[Real-time AI processing with progress bar]

AI: "✅ Phân tích hoàn thành! Gói Standard (30M VND) với 5 báo chí chất lượng cao..."
```

## 🛠️ API Endpoints

### Conversational Chat API
```bash
POST /api/chat/start                    # Start new conversation
POST /api/chat/continue                 # Continue conversation
POST /api/chat/trigger-workflow         # Trigger AI analysis
POST /api/chat/modify-plan             # Modify existing plan
POST /api/chat/upload                  # Upload documents
GET  /api/chat/session/{id}            # Get session info
DELETE /api/chat/session/{id}          # Clear session
```

### WebSocket Real-time Updates
```bash
WS   /ws/{session_id}                  # Real-time progress & results
```

### Media Search & Analytics
```bash
GET  /api/media/search                 # Advanced media search
GET  /api/media/categories             # Available categories
GET  /api/media/stats                  # Database statistics
GET  /api/media/top-traffic            # Top media by traffic
```

### System Management
```bash
GET  /api/health                       # System health check
GET  /api/admin/sessions               # Active conversations
GET  /api/admin/system-stats           # System analytics
POST /api/demo/quick-test              # Quick system test
```

## 📡 WebSocket Events

### Progress Updates
```javascript
{
  "type": "progress_update",
  "data": {
    "step": "Content Analysis",
    "message": "📊 Phân tích nội dung và yêu cầu...",
    "completed": 2,
    "total": 5,
    "percentage": 40
  }
}
```

### Workflow Completion
```javascript
{
  "type": "workflow_completed",
  "data": {
    "message": "✅ Phân tích hoàn thành!",
    "state": "reviewing",
    "data": {
      "content_analysis": { ... },
      "media_recommendations": [ ... ],
      "pricing_analysis": { ... },
      "executive_report": { ... }
    }
  }
}
```

## 🧪 Testing

### Manual Testing
```bash
# 1. Start conversation
curl -X POST http://localhost:8000/api/chat/start

# 2. Continue with project info
curl -X POST http://localhost:8000/api/chat/continue \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "message": "Startup fintech VietPay, app thanh toán SME, ngân sách 30 triệu"
  }'

# 3. Trigger AI workflow
curl -X POST http://localhost:8000/api/chat/trigger-workflow \
  -H "Content-Type: application/json" \
  -d '{"session_id": "your-session-id"}'
```

### Quick Demo Test
```bash
# End-to-end system test
curl -X POST http://localhost:8000/api/demo/quick-test
```

### Frontend Testing
1. Go to **http://localhost:8000**
2. Open **Developer Tools > Console** (for debugging)
3. Start conversation: *"Công ty fintech phát triển app thanh toán, ngân sách 25 triệu"*
4. Click **"🚀 Bắt đầu phân tích AI"**
5. Watch real-time progress and results

## 🔧 Configuration

### Package Pricing (VND)
```python
STARTER_PACKAGE = {
    "price": 12_000_000,      # 12M VND
    "media_count": 3,         # 2-3 tier-2 outlets
    "timeline": "1-3 days",
    "features": ["Light editing", "Basic reporting"]
}

STANDARD_PACKAGE = {
    "price": 30_000_000,      # 30M VND  
    "media_count": 15,        # 12-15 outlets with tier-1
    "timeline": "5-7 days",
    "features": ["Full writing", "Detailed reporting"]
}

PREMIUM_PACKAGE = {
    "price": 50_000_000,      # 50M VND
    "media_count": 18,        # 15-18 outlets + interviews
    "timeline": "10-14 days", 
    "features": ["Strategy + writing", "Social media", "PR consultation"]
}
```

### Agent Configuration
```python
# In .env file
AGENT_MEMORY_ENABLED=true
AGENT_REASONING_ENABLED=true
AGENT_PARALLEL_PROCESSING=true
MAX_AGENT_RETRIES=3
AGENT_TIMEOUT_SECONDS=120
```

## 🐛 Troubleshooting

### Common Issues & Solutions

**1. Conversation not progressing**
```bash
# Check WebSocket connection in browser DevTools > Network > WS
# Ensure no firewall blocking WebSocket connections
```

**2. AI Agents failing**
```bash
# Verify API keys
echo $OPENAI_API_KEY
# Check agent memory database
ls -la agent_memory.db
```

**3. Media search returning empty results**
```bash
# Verify database initialization
curl http://localhost:8000/api/media/stats
# Should return 100+ outlets
```

**4. Document upload fails**
```bash
# Check file size (max 15MB) and format (PDF/DOC/DOCX)
# Verify document processor initialization in logs
```

**5. Real-time progress not updating**
```bash
# Check WebSocket connection status
# Verify no ad-blockers interfering
# Check browser console for JavaScript errors
```

### Performance Optimization

**1. Use Groq for faster responses**
```bash
# In .env
GROQ_API_KEY=your_groq_key
# Remove or comment out OPENAI_API_KEY
```

**2. Increase parallel processing**
```python
# In agents.py
PARALLEL_PROCESSING = True
async def process_agents_parallel():
    tasks = [agent1.arun(prompt1), agent2.arun(prompt2)]
    results = await asyncio.gather(*tasks)
```

**3. Enable caching for repeated queries**
```python
# Redis caching for vector search results
# Database connection pooling
# Response compression
```

## 🚀 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create necessary directories
RUN mkdir -p logs uploads chroma_db

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "main.py"]
```

```bash
# Build and run
docker build -t instant-media-release .
docker run -p 8000:8000 --env-file .env instant-media-release
```

### AWS/Cloud Deployment
```bash
# Environment variables for production
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=["https://yourdomain.com"]
SECRET_KEY=your-super-secret-production-key

# Database for production
DATABASE_URL=postgresql://user:password@localhost:5432/media_release

# Performance settings
UVICORN_WORKERS=4
UVICORN_BACKLOG=2048
MAX_CONCURRENT_REQUESTS=100
```

### Monitoring & Analytics
```bash
# Optional integrations in .env
AGNO_API_KEY=your-agno-monitoring-key
LANGTRACE_API_KEY=your-langtrace-key

# System metrics
GET /api/admin/system-stats
GET /api/admin/sessions
```

## 📈 Extending the System

### Add New Media Outlets
```python
# In database.py VIETNAMESE_MEDIA_DATA
{
    "name": "New Media Outlet",
    "website": "https://newmedia.vn",
    "category": "TECHNOLOGY",
    "tier": 1,
    "monthly_visits": 5000000,
    "cost_per_article": 3000000,
    "top_categories": ["Technology", "Innovation"],
    "language": "Vietnamese"
}
```

### Custom AI Models
```python
# In agents.py - Use different models per agent
from agno.models.anthropic import Claude
from agno.models.google import Gemini

conversation_agent = Agent(model=Claude(...))
pricing_agent = Agent(model=Gemini(...))
```

### Additional Tools & Integrations
```python
# Add tools to agents
from agno.tools.email import EmailTools
from agno.tools.calendar import CalendarTools
from agno.tools.slack import SlackTools

agent = Agent(
    tools=[DuckDuckGoTools(), EmailTools(), SlackTools()]
)
```

### Custom Business Logic
```python
# Industry-specific packages
FINTECH_PACKAGES = {
    "Startup": {"price": 15_000_000, "features": ["Regulatory compliance focus"]},
    "SME": {"price": 35_000_000, "features": ["B2B media targeting"]},
    "Enterprise": {"price": 75_000_000, "features": ["Executive interviews"]}
}
```

## 📄 Project Structure

```
instant-media-release/
├── main.py                 # FastAPI server + WebSocket + conversational endpoints
├── agents.py               # 7 Agno AI agents + conversational workflow
├── database.py             # Enhanced database + 100 Vietnamese media outlets
├── document_processor.py   # PDF/DOC processing + vector storage
├── demo.html              # Conversational UI with real-time updates
├── requirements.txt        # Dependencies including Agno AI framework
├── .env.example           # Environment configuration template
├── README.md              # This comprehensive guide
│
# Auto-generated files
├── media_release.db        # SQLite database with media outlets
├── agent_memory.db         # Conversational agent memory
├── chroma_db/             # Vector database for semantic search
├── chroma_db_docs/        # Document vector storage
├── uploads/               # Temporary document storage
└── logs/                  # Application logs
```

## 🔐 Security Considerations

### Production Security
```python
# Environment-based secrets
SECRET_KEY=use-strong-secret-key-in-production
CORS_ORIGINS=["https://yourdomain.com"]  # Restrict origins

# API rate limiting
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=300

# File upload security
MAX_FILE_SIZE=15MB
ALLOWED_EXTENSIONS=[".pdf", ".doc", ".docx"]
```

### Data Privacy
- **No persistent user data**: Sessions cleared after completion
- **Document processing**: Files deleted after analysis
- **Agent memory**: Can be disabled via `AGENT_MEMORY_ENABLED=false`
- **Audit logging**: All interactions logged for monitoring

## 🎯 Business Applications

### Target Markets
- **Vietnamese SMEs**: Primary target with localized content
- **Startups**: Fast, cost-effective PR solutions
- **Agencies**: White-label PR automation tool
- **Enterprises**: Scalable media relationship management

### Revenue Model
- **SaaS Subscription**: Monthly/yearly plans
- **Pay-per-campaign**: Usage-based pricing
- **Enterprise**: Custom packages with dedicated support
- **API licensing**: Developer integrations

### Competitive Advantages
- **Vietnamese market expertise**: 100+ local media database
- **Conversational UX**: Natural language interaction
- **Real-time processing**: Instant results with progress tracking
- **AI-powered recommendations**: Data-driven media selection
- **Cost transparency**: Clear pricing with ROI projections

## 📞 Support & Development

- **Documentation**: Complete API docs at `/docs` endpoint
- **Health Monitoring**: Real-time system status at `/health`
- **Debug Tools**: Built-in testing and debugging features
- **Community**: GitHub issues and discussions
- **Enterprise Support**: Custom development and integration

## 📋 Changelog

### v3.0.0 (Current) - Conversational AI System
- ✅ Complete conversational interface with Vietnamese language support
- ✅ 7 specialized AI agents with real-time coordination
- ✅ WebSocket-based real-time progress tracking
- ✅ Document upload and analysis capabilities
- ✅ Enhanced media database with 100+ Vietnamese outlets
- ✅ Interactive plan modification and approval workflow
- ✅ Comprehensive error handling and fallback mechanisms

### v2.0.0 - Multi-Agent Framework
- ✅ Agno AI framework integration
- ✅ 4 specialized AI agents
- ✅ Vector search capabilities

### v1.0.0 - Basic API
- ✅ Simple chatbot interface
- ✅ Basic media recommendations
- ✅ SQLite database

## 📄 License

MIT License - See LICENSE file for details.

---

**Built with ❤️ using Agno AI Framework**

🚀 **Ready to revolutionize conversational PR automation for Vietnamese SMEs!**

*For technical support or custom development, please contact the development team.*