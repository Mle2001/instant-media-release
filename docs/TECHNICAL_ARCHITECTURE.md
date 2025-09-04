# 🏗️ Kiến Trúc Kỹ Thuật Hệ Thống ML-Enhanced Ranking

## 📁 Cấu Trúc Thư Mục Chi Tiết

```
instant-media-release/
├── 📋 Core System Files
│   ├── main.py                     # FastAPI server chính
│   ├── agents.py                   # Multi-agent orchestration system
│   ├── database.py                 # Database management & vector store
│   ├── content_generator.py        # Content generation logic
│   └── document_processor.py       # Document processing pipeline
│
├── 🤖 ML-Enhanced Ranking System
│   └── ml_ranking_system/
│       ├── __init__.py             # Module initialization
│       ├── universal_features.py   # Feature extraction engine
│       ├── ground_truth_collector.py # Feedback collection system
│       ├── ml_ranking_model.py     # Core ML ranking model
│       ├── continuous_learning.py  # Learning management system
│       ├── enterprise_data_port.py # Enterprise API endpoints
│       ├── performance_monitor.py  # System monitoring
│       └── model_safety_validator.py # Safety validation
│
├── 📊 Enterprise Dashboards
│   └── dashboards/
│       ├── __init__.py
│       ├── enterprise_data_upload.py # Data upload interface
│       └── ml_monitoring.py        # Performance monitoring UI
│
├── ⚙️ Configuration & Data
│   ├── config/
│   │   ├── ml_config.yaml          # ML system configuration
│   │   ├── enterprise_tokens.json  # Authentication tokens
│   │   └── ml_requirements.txt     # ML dependencies
│   ├── schemas/
│   │   └── feedback_data_schema.json # Data validation schema
│   └── chroma_db/                  # Vector database storage
│
├── 🧪 Testing & Validation
│   ├── tests/
│   │   ├── test_basic_functionality.py
│   │   ├── test_universal_features.py
│   │   ├── test_ground_truth_collector.py
│   │   └── test_ground_truth_simple.py
│   ├── test_ml_system.py           # System integration test
│   └── run_dashboards.py           # Dashboard launcher
│
├── 📂 Runtime Data
│   ├── media_release.db            # SQLite database
│   ├── team_memory.db             # Agent memory storage
│   ├── logs/                      # System logs
│   ├── uploads/                   # File upload storage
│   └── processed_documents/       # Document processing cache
│
└── 📚 Documentation
    ├── README.md                   # Project overview
    ├── ENTERPRISE_USER_GUIDE.md    # User guide for enterprises
    ├── RANKING_SYSTEM_THEORY.md    # Theoretical foundation
    └── TECHNICAL_ARCHITECTURE.md   # This file
```

---

## 🔧 Kiến Trúc Hệ Thống

### 1. Tổng Quan Kiến Trúc

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer                             │
├─────────────────────────────────────────────────────────────┤
│  Web UI (8080)  │  Dashboard 1 (8501)  │  Dashboard 2 (8502)│
├─────────────────────────────────────────────────────────────┤
│                    API Gateway                              │
├─────────────────────────────────────────────────────────────┤
│           │                                │                │
│  Core API │        Enterprise API          │   ML Monitor   │
│  (FastAPI)│      (Data Collection)         │   (Streamlit)  │
├─────────────────────────────────────────────────────────────┤
│                  Business Logic Layer                       │
├─────────────────────────────────────────────────────────────┤
│ Agent System │  ML Ranking Engine  │  Content Generator    │
├─────────────────────────────────────────────────────────────┤
│                    Data Layer                               │
├─────────────────────────────────────────────────────────────┤
│ SQLite DB │ Vector Store │ File Storage │ Model Storage     │
└─────────────────────────────────────────────────────────────┘
```

### 2. ML Ranking System Architecture

```
┌───────────────────────────────────────────────────────────┐
│                   Input Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │Content Data │  │User Context │  │Business Info│      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└───────────────────┬───────────────────────────────────────┘
                    │
┌───────────────────▼───────────────────────────────────────┐
│              Feature Extraction Layer                    │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         Universal Structure Extractor               │ │
│  │  ┌────────────┐ ┌────────────┐ ┌─────────────────┐ │ │
│  │  │Content     │ │Audience    │ │Business Context │ │ │
│  │  │Features    │ │Features    │ │Features         │ │ │
│  │  │(15 dims)   │ │(12 dims)   │ │(10 dims)        │ │ │
│  │  └────────────┘ └────────────┘ └─────────────────┘ │ │
│  │  ┌────────────┐ ┌────────────┐                     │ │
│  │  │Timing      │ │Competitive │                     │ │
│  │  │Features    │ │Features    │                     │ │
│  │  │(8 dims)    │ │(5 dims)    │                     │ │
│  │  └────────────┘ └────────────┘                     │ │
│  └──────────────────────────────────────────────────────┘ │
└───────────────────┬───────────────────────────────────────┘
                    │ 50-dimensional feature vector
┌───────────────────▼───────────────────────────────────────┐
│                ML Model Layer                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              LSTM + Attention Network                │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐ │ │
│  │  │PhoBERT      │ │Multi-Head   │ │Output Layer     │ │ │
│  │  │Embeddings   │ │Attention    │ │(Media Scores)   │ │ │
│  │  │(768 dims)   │ │(4 heads)    │ │                 │ │ │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘ │ │
│  └──────────────────────────────────────────────────────┘ │
└───────────────────┬───────────────────────────────────────┘
                    │ Ranking scores for each media outlet
┌───────────────────▼───────────────────────────────────────┐
│              Continuous Learning Layer                   │
│  ┌──────────────────────────────────────────────────────┐ │
│  │           Ground Truth Collection                    │ │
│  │  Campaign Results → Training Labels → Model Update   │ │
│  └──────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

---

## 📋 Chi Tiết Từng Component

### 1. Core System Files

#### `main.py` - FastAPI Server
**Chức năng:**
- API endpoints cho web interface
- WebSocket cho real-time updates
- Authentication và authorization
- Request/response handling

**Key Components:**
```python
# Main API routes
@app.post("/api/analyze")     # Content analysis
@app.post("/api/recommend")   # Media recommendations  
@app.get("/api/status")       # System status
@app.websocket("/ws")         # Real-time updates
```

#### `agents.py` - Multi-Agent System
**Chức năng:**
- Orchestrates multiple AI agents
- Content analysis agent
- Media specialist agent (Enhanced with ML)
- Presentation agent

**Architecture:**
```python
class EnhancedTeamSystem:
    - content_analyst: Agent          # Content analysis
    - media_specialist: Agent         # ML-enhanced ranking
    - presentation_agent: Agent       # Output formatting
    - orchestrator: Team              # Coordination
```

#### `database.py` - Data Management
**Chức năng:**
- SQLite database management
- ChromaDB vector store
- Media outlet data storage
- ML training data persistence

**Tables:**
```sql
-- Core tables
media_outlets         # Media outlet information
conversations         # Chat history
documents            # Processed documents

-- ML tables (Added)
ml_feedback_data     # Enterprise feedback
ml_model_versions    # Model versioning
ml_training_jobs     # Training job tracking
```

### 2. ML Ranking System

#### `universal_features.py` - Feature Engineering
**Chức năng:**
- Trích xuất 50+ features từ input
- Sử dụng PhoBERT cho Vietnamese NLP
- Feature categories: Content, Audience, Business, Timing, Competitive

**Core Class:**
```python
class UniversalStructureExtractor:
    def extract_universal_features(self, content_data, context_data):
        # Returns 50-dimensional feature vector
        return UniversalFeatures(
            content_features=dict,      # 15 dimensions
            audience_features=dict,     # 12 dimensions  
            business_features=dict,     # 10 dimensions
            timing_features=dict,       # 8 dimensions
            competitive_features=dict   # 5 dimensions
        )
```

#### `ml_ranking_model.py` - Core ML Model
**Chức năng:**
- LSTM + Multi-head Attention architecture
- Transfer learning với PhoBERT
- Hybrid scoring (70% ML + 30% traditional)

**Model Architecture:**
```python
class EnhancedMediaRankingAgent:
    - feature_extractor: UniversalStructureExtractor
    - lstm_model: torch.nn.LSTM
    - attention_heads: MultiHeadAttention (4 heads)
    - output_layer: torch.nn.Linear
```

#### `ground_truth_collector.py` - Feedback Collection
**Chức năng:**
- Thu thập kết quả chiến dịch thực tế
- Chuyển đổi business metrics thành ML labels
- Data validation và quality control

**Data Models:**
```python
class CampaignFeedback:
    campaign_info: CampaignInfo
    media_results: Dict[str, MediaResult]
    business_metrics: BusinessMetrics
    computed_labels: Dict[str, float]  # ML training labels
```

#### `continuous_learning.py` - Learning Management
**Chức năng:**
- Quản lý vòng đời training
- A/B testing cho model deployment
- Model versioning và rollback
- Performance monitoring

**Learning Pipeline:**
```python
class ContinuousLearningManager:
    def learning_cycle(self):
        1. collect_new_feedback()
        2. validate_data_quality()
        3. retrain_model()
        4. validate_model_safety()
        5. a_b_test_deployment()
        6. monitor_performance()
```

#### `enterprise_data_port.py` - Enterprise API
**Chức năng:**
- RESTful API cho enterprise data submission
- Authentication với enterprise tokens
- Rate limiting và data validation
- Integration với main system

**API Endpoints:**
```python
POST /submit_feedback      # Submit campaign results
GET  /learning_stats       # Get learning statistics
POST /batch_upload         # Bulk data upload
GET  /model_performance    # Model metrics
```

### 3. Dashboard System

#### `enterprise_data_upload.py` - Data Upload UI
**Features:**
- Single campaign upload form
- CSV batch upload
- Data preview và validation
- Upload progress tracking

#### `ml_monitoring.py` - Performance Monitoring  
**Features:**
- Real-time model performance
- Training progress visualization
- Feature importance analysis
- System health dashboard

---

## ⚡ Data Flow Architecture

### 1. Request Processing Flow

```
1. User Request (Web/API)
        ↓
2. Authentication & Validation
        ↓
3. Agent Orchestration
        ↓
4. Feature Extraction (Universal Features)
        ↓
5. ML Model Inference
        ↓
6. Traditional Ranking (Fallback)
        ↓
7. Hybrid Score Calculation
        ↓
8. Results Ranking & Filtering
        ↓
9. Response Formatting
        ↓
10. Client Response
```

### 2. Continuous Learning Flow

```
1. Enterprise Submits Campaign Results
        ↓
2. Data Validation & Quality Check
        ↓
3. Ground Truth Label Generation
        ↓
4. Training Data Augmentation
        ↓
5. Model Retraining (Incremental)
        ↓
6. Model Safety Validation
        ↓
7. A/B Testing Deployment
        ↓
8. Performance Monitoring
        ↓
9. Model Promotion/Rollback Decision
```

### 3. Feature Engineering Pipeline

```
Raw Input Data
        ↓
Content Analysis (PhoBERT)
        ↓
Business Context Extraction
        ↓
Audience Signal Processing
        ↓
Timing Feature Engineering
        ↓
Competitive Analysis
        ↓
Feature Vector Assembly (50D)
        ↓
Feature Normalization
        ↓
ML Model Input
```

---

## 🗄️ Database Schema

### Core Tables

```sql
-- Media outlets information
CREATE TABLE media_outlets (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    audience_size INTEGER,
    credibility_score REAL,
    response_rate REAL,
    metadata JSON
);

-- Conversation history
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    user_message TEXT,
    ai_response TEXT,
    timestamp DATETIME,
    session_data JSON
);
```

### ML System Tables

```sql
-- Enterprise feedback data
CREATE TABLE ml_feedback_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enterprise_id TEXT NOT NULL,
    campaign_name TEXT NOT NULL,
    campaign_data JSON NOT NULL,
    feedback_data JSON NOT NULL,
    training_labels JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Model versions tracking
CREATE TABLE ml_model_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_name TEXT NOT NULL,
    model_path TEXT NOT NULL,
    performance_metrics JSON,
    is_active BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Training jobs management
CREATE TABLE ml_training_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL,
    config JSON,
    metrics JSON,
    error_log TEXT,
    started_at DATETIME,
    completed_at DATETIME
);
```

---

## 🔒 Security & Performance

### Security Measures

1. **Authentication:**
   - Enterprise token-based auth
   - Rate limiting per enterprise
   - Input validation và sanitization

2. **Data Protection:**
   - Encrypted data storage
   - Secure API endpoints
   - PII data anonymization

3. **Model Security:**
   - Model safety validation
   - Adversarial attack protection  
   - Rollback mechanisms

### Performance Optimization

1. **Caching:**
   - Feature vector caching
   - Model prediction caching
   - Database query optimization

2. **Async Processing:**
   - Background training jobs
   - Async API endpoints
   - Queue-based data processing

3. **Scalability:**
   - Horizontal scaling ready
   - Microservice architecture
   - Load balancing support

---

## 🚀 Deployment Architecture

### Production Setup

```
Load Balancer
    ↓
┌─────────────────────────────────────┐
│           API Gateway               │
├─────────────────────────────────────┤
│  Main App    │  ML Service  │  UI   │
│  (FastAPI)   │  (Python)    │(React)│
├─────────────────────────────────────┤
│     Database Layer                  │
│  SQLite/PostgreSQL │  ChromaDB      │
├─────────────────────────────────────┤
│       Storage Layer                 │
│  File Storage  │  Model Storage     │
└─────────────────────────────────────┘
```

### Monitoring & Logging

- Application metrics (FastAPI)
- ML model performance tracking
- System resource monitoring
- Error logging và alerting
- User behavior analytics

---

## 📈 Future Extensions

### Planned Enhancements

1. **Advanced ML Features:**
   - Transformer models (GPT-style)
   - Multi-modal learning (text + images)
   - Federated learning support

2. **Integration Capabilities:**
   - CRM system integration
   - Social media APIs
   - Analytics platforms

3. **Business Intelligence:**
   - Predictive analytics
   - Market trend analysis
   - Competitor monitoring

---

*Tài liệu này cung cấp overview comprehensive về kiến trúc kỹ thuật của hệ thống ML-Enhanced Ranking. Để biết thêm chi tiết implementation cụ thể, vui lòng tham khảo source code và comments trong từng file.*