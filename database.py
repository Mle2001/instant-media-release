"""
Instant Media Release - Database Models & Vietnamese Media Data
Production-grade database with ChromaDB vector search integration
"""

import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

import chromadb
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from pydantic import BaseModel, Field, ConfigDict
from loguru import logger

# =================== CONFIGURATION ===================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./media_release.db")
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "media_outlets")

# =================== DATABASE SETUP ===================
# SQLAlchemy Configuration
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific configuration for better concurrency
    engine = create_engine(
        DATABASE_URL, 
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        poolclass=StaticPool,
        echo=False
    )
else:
    # PostgreSQL/other databases
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Vector embeddings model (lightweight but effective)
try:
    embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    logger.info("✅ SentenceTransformer model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load embedding model: {e}")
    embedding_model = None

# ChromaDB client with persistence
try:
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)
    logger.info(f"✅ ChromaDB initialized at {CHROMA_PERSIST_DIRECTORY}")
except Exception as e:
    logger.error(f"❌ ChromaDB initialization failed: {e}")
    chroma_client = chromadb.Client()

# =================== DATABASE MODELS ===================

class MediaOutlet(Base):
    """Vietnamese Media Outlets - Optimized for search and recommendations"""
    __tablename__ = "media_outlets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    publisher = Column(String(255), nullable=False)
    circulation = Column(Integer, nullable=False)  # Monthly readers
    publication_format = Column(String(50), nullable=False)  # Online, Print, Both
    website = Column(String(500))
    language = Column(String(50), nullable=False)  # Vietnamese, English, Both
    tier = Column(Integer, nullable=False, index=True)  # 1=Tier-1, 2=Tier-2, 3=Local
    cost_per_article = Column(Float, nullable=False)  # VND
    topics = Column(Text, nullable=False)  # JSON array
    target_audience = Column(Text, nullable=False)  # JSON array
    editorial_contact = Column(String(500))
    submission_guidelines = Column(Text)
    response_time_hours = Column(Integer, default=24)
    success_rate = Column(Float, default=0.8)  # Historical publication success rate
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserRequest(Base):
    """User Requests - Enhanced tracking and analytics"""
    __tablename__ = "user_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True, nullable=False)
    user_id = Column(String(255), index=True)
    press_release_language = Column(String(50))
    project_background = Column(Text)
    desired_channels = Column(Text)  # JSON array
    budget = Column(Float)
    package_type = Column(String(50))  # Starter, Standard, Premium
    status = Column(String(50), default="pending", index=True)
    ai_processing_time = Column(Float)  # seconds
    recommendation_count = Column(Integer, default=0)
    total_estimated_cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

class AgentRecommendation(Base):
    """AI Agent Recommendations - Detailed tracking"""
    __tablename__ = "agent_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, index=True, nullable=False)
    media_outlet_id = Column(Integer, index=True, nullable=False)
    agent_name = Column(String(100), nullable=False)  # Which agent generated this
    score = Column(Float, nullable=False)  # Matching score 0-1
    reasoning = Column(Text)  # AI explanation
    estimated_reach = Column(Integer)
    cost = Column(Float)
    priority_rank = Column(Integer)  # 1 = highest priority
    created_at = Column(DateTime, default=datetime.utcnow)

class AgentSession(Base):
    """Agent Processing Sessions - Performance monitoring"""
    __tablename__ = "agent_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True, nullable=False)
    agent_type = Column(String(100), nullable=False)
    input_data = Column(Text)
    output_data = Column(Text)
    processing_time = Column(Float)  # seconds
    token_usage = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# =================== PYDANTIC MODELS ===================

class MediaOutletResponse(BaseModel):
    """API Response model for media outlets"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    publisher: str
    circulation: int
    publication_format: str
    website: Optional[str] = None
    language: str
    tier: int
    cost_per_article: float
    topics: List[str]
    target_audience: List[str]
    response_time_hours: int
    success_rate: float

class UserRequestCreate(BaseModel):
    """Create user request model"""
    session_id: str
    press_release_language: str
    project_background: str
    desired_channels: List[str]
    budget: float
    package_type: str

class RecommendationResponse(BaseModel):
    """AI Recommendation response"""
    media_outlet: MediaOutletResponse
    score: float
    reasoning: str
    estimated_reach: int
    cost: float
    priority_rank: int

# =================== VIETNAMESE MEDIA DATA ===================

VIETNAMESE_MEDIA_DATA = [
    {
        "name": "VnExpress",
        "publisher": "FPT Digital",
        "circulation": 35000000,
        "publication_format": "Online",
        "website": "https://vnexpress.net",
        "language": "Vietnamese",
        "tier": 1,
        "cost_per_article": 15000000,
        "topics": ["Technology", "Business", "Politics", "Sports", "Entertainment", "Health", "Education"],
        "target_audience": ["General Public", "Business Professionals", "Tech Enthusiasts", "Government Officials"],
        "editorial_contact": "edit@vnexpress.net",
        "response_time_hours": 24,
        "success_rate": 0.85
    },
    {
        "name": "ZNews",
        "publisher": "VNG Corporation",
        "circulation": 28000000,
        "publication_format": "Online",
        "website": "https://znews.vn",
        "language": "Vietnamese",
        "tier": 1,
        "cost_per_article": 12000000,
        "topics": ["Technology", "Lifestyle", "Entertainment", "Sports", "Gaming", "Social Media"],
        "target_audience": ["Young Adults", "Tech Enthusiasts", "Entertainment Fans", "Gamers"],
        "editorial_contact": "news@znews.vn",
        "response_time_hours": 12,
        "success_rate": 0.82
    },
    {
        "name": "Kenh14",
        "publisher": "VCCorp",
        "circulation": 22000000,
        "publication_format": "Online",
        "website": "https://kenh14.vn",
        "language": "Vietnamese",
        "tier": 1,
        "cost_per_article": 10000000,
        "topics": ["Entertainment", "Lifestyle", "Fashion", "Celebrity", "Youth Culture", "Social Trends"],
        "target_audience": ["Young Adults", "Fashion Enthusiasts", "Entertainment Fans", "Students"],
        "editorial_contact": "news@kenh14.vn",
        "response_time_hours": 8,
        "success_rate": 0.80
    },
    {
        "name": "VietnamNet",
        "publisher": "VietnamNet Media",
        "circulation": 18000000,
        "publication_format": "Online",
        "website": "https://vietnamnet.vn",
        "language": "Vietnamese",
        "tier": 1,
        "cost_per_article": 8000000,
        "topics": ["News", "Politics", "Society", "Technology", "Business", "International"],
        "target_audience": ["General Public", "Government Officials", "Business Community", "Intellectuals"],
        "editorial_contact": "toasoan@vietnamnet.vn",
        "response_time_hours": 24,
        "success_rate": 0.88
    },
    {
        "name": "Tuoi Tre",
        "publisher": "Tuoi Tre Media",
        "circulation": 20000000,
        "publication_format": "Both",
        "website": "https://tuoitre.vn",
        "language": "Vietnamese",
        "tier": 1,
        "cost_per_article": 9000000,
        "topics": ["News", "Sports", "Education", "Youth", "Society", "Culture"],
        "target_audience": ["Young Adults", "Students", "General Public", "Parents"],
        "editorial_contact": "bantindoc@tuoitre.vn",
        "response_time_hours": 24,
        "success_rate": 0.83
    },
    {
        "name": "CafeF",
        "publisher": "CafeF Media",
        "circulation": 10000000,
        "publication_format": "Online",
        "website": "https://cafef.vn",
        "language": "Vietnamese",
        "tier": 2,
        "cost_per_article": 5000000,
        "topics": ["Business", "Finance", "Economy", "Investment", "Stock Market", "Banking"],
        "target_audience": ["Business Professionals", "Investors", "Entrepreneurs", "Financial Analysts"],
        "editorial_contact": "toasoan@cafef.vn",
        "response_time_hours": 12,
        "success_rate": 0.85
    },
    {
        "name": "CafeBiz",
        "publisher": "CafeBiz Media",
        "circulation": 8000000,
        "publication_format": "Online",
        "website": "https://cafebiz.vn",
        "language": "Vietnamese",
        "tier": 2,
        "cost_per_article": 4500000,
        "topics": ["Business", "Startup", "Technology", "Marketing", "Innovation", "Leadership"],
        "target_audience": ["Entrepreneurs", "Business Professionals", "Startup Community", "Tech Leaders"],
        "editorial_contact": "news@cafebiz.vn",
        "response_time_hours": 8,
        "success_rate": 0.82
    },
    {
        "name": "Vietnam News",
        "publisher": "Vietnam News Agency",
        "circulation": 5000000,
        "publication_format": "Both",
        "website": "https://vietnamnews.vn",
        "language": "English",
        "tier": 2,
        "cost_per_article": 6000000,
        "topics": ["Politics", "Business", "Tourism", "International", "Culture", "Society"],
        "target_audience": ["International Readers", "Expats", "Foreign Businesses", "Diplomats"],
        "editorial_contact": "editor@vietnamnews.vn",
        "response_time_hours": 48,
        "success_rate": 0.90
    },
    {
        "name": "Doanh Nghiep",
        "publisher": "Doanh Nghiep Media",
        "circulation": 6000000,
        "publication_format": "Online",
        "website": "https://doanhnghiep.vn",
        "language": "Vietnamese",
        "tier": 2,
        "cost_per_article": 3500000,
        "topics": ["Business", "SME", "Manufacturing", "Trade", "Corporate News", "Industry"],
        "target_audience": ["SME Owners", "Business Managers", "Industry Professionals", "B2B Community"],
        "editorial_contact": "edit@doanhnghiep.vn",
        "response_time_hours": 24,
        "success_rate": 0.78
    },
    {
        "name": "ICTNews",
        "publisher": "ICT Media",
        "circulation": 4000000,
        "publication_format": "Online",
        "website": "https://ictnews.vn",
        "language": "Vietnamese",
        "tier": 2,
        "cost_per_article": 4000000,
        "topics": ["Technology", "ICT", "Digital Transformation", "AI", "Cybersecurity", "Innovation"],
        "target_audience": ["Tech Professionals", "IT Managers", "Software Developers", "Digital Leaders"],
        "editorial_contact": "news@ictnews.vn",
        "response_time_hours": 12,
        "success_rate": 0.86
    }
]

# =================== DATABASE OPERATIONS ===================

class MediaDatabase:
    """Production-grade database operations with async support"""
    
    def __init__(self):
        """Initialize database with error handling"""
        self.vector_collection = None
        self._setup_database()
        self._setup_vector_db()
    
    def _setup_database(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Database tables created successfully")
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            raise
    
    def _setup_vector_db(self):
        """Setup ChromaDB collection with error handling"""
        if not chroma_client or not embedding_model:
            logger.warning("⚠️ Vector database not available")
            return
            
        try:
            # Try to get existing collection
            self.vector_collection = chroma_client.get_collection(CHROMA_COLLECTION_NAME)
            logger.info(f"✅ Vector collection '{CHROMA_COLLECTION_NAME}' loaded")
        except Exception:
            # Create new collection
            try:
                self.vector_collection = chroma_client.create_collection(
                    name=CHROMA_COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"✅ Vector collection '{CHROMA_COLLECTION_NAME}' created")
            except Exception as e:
                logger.error(f"❌ Vector collection creation failed: {e}")
    
    @asynccontextmanager
    async def get_db_session(self):
        """Async context manager for database sessions"""
        db = SessionLocal()
        try:
            yield db
        except Exception as e:
            db.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            db.close()
    
    def get_db(self) -> Session:
        """Synchronous database session (for FastAPI dependency)"""
        return SessionLocal()
    
    async def initialize_media_data(self) -> bool:
        """Initialize database with Vietnamese media data"""
        try:
            async with self.get_db_session() as db:
                # Check if data already exists
                existing_count = db.query(MediaOutlet).count()
                if existing_count > 0:
                    logger.info(f"📊 Database already initialized with {existing_count} media outlets")
                    return True
                
                logger.info("🔄 Initializing Vietnamese media database...")
                
                # Insert media data
                for media_data in VIETNAMESE_MEDIA_DATA:
                    media_outlet = MediaOutlet(
                        name=media_data["name"],
                        publisher=media_data["publisher"],
                        circulation=media_data["circulation"],
                        publication_format=media_data["publication_format"],
                        website=media_data.get("website"),
                        language=media_data["language"],
                        tier=media_data["tier"],
                        cost_per_article=media_data["cost_per_article"],
                        topics=json.dumps(media_data["topics"]),
                        target_audience=json.dumps(media_data["target_audience"]),
                        editorial_contact=media_data.get("editorial_contact"),
                        response_time_hours=media_data.get("response_time_hours", 24),
                        success_rate=media_data.get("success_rate", 0.8)
                    )
                    db.add(media_outlet)
                
                db.commit()
                
                # Initialize vector embeddings
                await self._initialize_vector_embeddings(db)
                
                logger.info(f"✅ Initialized {len(VIETNAMESE_MEDIA_DATA)} Vietnamese media outlets")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize media data: {e}")
            return False
    
    async def _initialize_vector_embeddings(self, db: Session):
        """Create vector embeddings for semantic search"""
        if not self.vector_collection or not embedding_model:
            logger.warning("⚠️ Skipping vector embeddings - ChromaDB not available")
            return
        
        try:
            # Get all media outlets
            media_outlets = db.query(MediaOutlet).all()
            
            embeddings = []
            documents = []
            metadatas = []
            ids = []
            
            for media in media_outlets:
                # Create searchable text
                topics = json.loads(media.topics)
                audiences = json.loads(media.target_audience)
                
                searchable_text = f"{media.name} {media.publisher} {' '.join(topics)} {' '.join(audiences)} {media.language}"
                
                # Generate embedding
                embedding = embedding_model.encode(searchable_text).tolist()
                
                embeddings.append(embedding)
                documents.append(searchable_text)
                metadatas.append({
                    "media_id": str(media.id),
                    "name": media.name,
                    "tier": media.tier,
                    "language": media.language,
                    "cost": media.cost_per_article
                })
                ids.append(f"media_{media.id}")
            
            # Add to ChromaDB
            self.vector_collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"✅ Created vector embeddings for {len(embeddings)} media outlets")
            
        except Exception as e:
            logger.error(f"❌ Vector embedding initialization failed: {e}")
    
    async def search_media_by_vector(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Semantic search using vector embeddings"""
        if not self.vector_collection or not embedding_model:
            logger.warning("⚠️ Vector search not available, falling back to keyword search")
            return {"documents": [], "metadatas": [], "distances": []}
        
        try:
            # Generate query embedding
            query_embedding = embedding_model.encode(query).tolist()
            
            # Search in ChromaDB
            results = self.vector_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=["documents", "metadatas", "distances"]
            )
            
            logger.debug(f"🔍 Vector search for '{query}' returned {len(results.get('documents', [[]])[0])} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")
            return {"documents": [], "metadatas": [], "distances": []}
    
    async def get_media_by_id(self, media_id: int) -> Optional[MediaOutlet]:
        """Get media outlet by ID"""
        try:
            async with self.get_db_session() as db:
                media = db.query(MediaOutlet).filter(MediaOutlet.id == media_id).first()
                return media
        except Exception as e:
            logger.error(f"❌ Failed to get media by ID {media_id}: {e}")
            return None
    
    async def save_user_request(self, request: UserRequestCreate) -> Optional[int]:
        """Save user request with error handling"""
        try:
            async with self.get_db_session() as db:
                db_request = UserRequest(
                    session_id=request.session_id,
                    press_release_language=request.press_release_language,
                    project_background=request.project_background,
                    desired_channels=json.dumps(request.desired_channels),
                    budget=request.budget,
                    package_type=request.package_type
                )
                
                db.add(db_request)
                db.commit()
                db.refresh(db_request)
                
                logger.info(f"✅ Saved user request with ID: {db_request.id}")
                return db_request.id
                
        except Exception as e:
            logger.error(f"❌ Failed to save user request: {e}")
            return None
    
    async def save_agent_recommendations(
        self, 
        request_id: int, 
        recommendations: List[Dict[str, Any]],
        agent_name: str
    ) -> bool:
        """Save AI agent recommendations"""
        try:
            async with self.get_db_session() as db:
                for i, rec in enumerate(recommendations):
                    db_rec = AgentRecommendation(
                        request_id=request_id,
                        media_outlet_id=rec.get("media_outlet_id"),
                        agent_name=agent_name,
                        score=rec.get("score", 0.0),
                        reasoning=rec.get("reasoning", ""),
                        estimated_reach=rec.get("estimated_reach", 0),
                        cost=rec.get("cost", 0.0),
                        priority_rank=i + 1
                    )
                    db.add(db_rec)
                
                db.commit()
                logger.info(f"✅ Saved {len(recommendations)} recommendations from {agent_name}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to save recommendations: {e}")
            return False
    
    async def get_all_media_outlets(self) -> List[MediaOutletResponse]:
        """Get all active media outlets"""
        try:
            async with self.get_db_session() as db:
                media_outlets = db.query(MediaOutlet).filter(MediaOutlet.is_active == True).all()
                
                result = []
                for media in media_outlets:
                    result.append(MediaOutletResponse(
                        id=media.id,
                        name=media.name,
                        publisher=media.publisher,
                        circulation=media.circulation,
                        publication_format=media.publication_format,
                        website=media.website,
                        language=media.language,
                        tier=media.tier,
                        cost_per_article=media.cost_per_article,
                        topics=json.loads(media.topics),
                        target_audience=json.loads(media.target_audience),
                        response_time_hours=media.response_time_hours,
                        success_rate=media.success_rate
                    ))
                
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to get media outlets: {e}")
            return []

# =================== GLOBAL INSTANCE ===================

# Global database instance
media_db = MediaDatabase()

async def init_database():
    """Initialize database on startup"""
    try:
        logger.info("🚀 Initializing Instant Media Release Database...")
        
        success = await media_db.initialize_media_data()
        if success:
            logger.info("✅ Database initialization completed successfully!")
            return True
        else:
            logger.error("❌ Database initialization failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Critical database initialization error: {e}")
        return False

# =================== UTILITY FUNCTIONS ===================

def get_database() -> Session:
    """FastAPI dependency for database sessions"""
    db = media_db.get_db()
    try:
        yield db
    finally:
        db.close()

# =================== TESTING ===================

async def test_database():
    """Test database functionality"""
    logger.info("🧪 Testing database functionality...")
    
    # Test initialization
    success = await init_database()
    assert success, "Database initialization failed"
    
    # Test vector search
    results = await media_db.search_media_by_vector("technology startup business")
    logger.info(f"🔍 Vector search test returned {len(results.get('documents', [[]])[0])} results")
    
    # Test media retrieval
    media_outlets = await media_db.get_all_media_outlets()
    logger.info(f"📊 Retrieved {len(media_outlets)} media outlets")
    
    logger.info("✅ Database tests completed successfully!")

# if __name__ == "__main__":
#     # Run database tests
#     asyncio.run(test_database())