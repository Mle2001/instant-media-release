"""
Instant Media Release - Enhanced Database with 100 Vietnamese Media Outlets
Production-grade database with ChromaDB vector search integration
Updated with comprehensive media landscape data
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
from pydantic import BaseModel, ConfigDict
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

# =================== ENHANCED DATABASE MODELS ===================

class MediaOutlet(Base):
    """Enhanced Vietnamese Media Outlets with comprehensive analytics"""
    __tablename__ = "media_outlets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    website = Column(String(500), nullable=False)
    category = Column(String(100), nullable=False, index=True)  # MAINSTREAM, BUSINESS, etc.
    tier = Column(Integer, nullable=False, index=True)  # 1=Tier-1, 2=Tier-2, 3=Local
    
    # Traffic Analytics
    total_visits_3months = Column(Integer, nullable=True)  # Total visits in 3 months
    monthly_visits = Column(Integer, nullable=True)  # Average monthly visits
    visit_duration = Column(String(20), nullable=True)  # Average visit duration (mm:ss format)
    access_from_vietnam = Column(Float, nullable=True)  # % of traffic from Vietnam
    
    # Demographics
    male_audience = Column(Float, nullable=True)  # % male audience
    female_audience = Column(Float, nullable=True)  # % female audience
    
    # Geographic Distribution
    southern_audience = Column(Float, nullable=True)  # % Southern Vietnam
    northern_audience = Column(Float, nullable=True)  # % Northern Vietnam  
    central_audience = Column(Float, nullable=True)  # % Central Vietnam
    
    # Age Demographics
    age_18_24 = Column(Float, nullable=True)  # % 18-24 years old
    age_25_34 = Column(Float, nullable=True)  # % 25-34 years old
    age_35_44 = Column(Float, nullable=True)  # % 35-44 years old
    age_45_54 = Column(Float, nullable=True)  # % 45-54 years old
    age_55_64 = Column(Float, nullable=True)  # % 55-64 years old
    age_65_plus = Column(Float, nullable=True)  # % 65+ years old
    
    # Content Categories
    top_categories = Column(Text, nullable=False)  # JSON array of top 3 categories
    
    # Legacy Fields (maintained for compatibility)
    publisher = Column(String(255), nullable=True)
    circulation = Column(Integer, nullable=True)  # Estimated from monthly visits
    publication_format = Column(String(50), default="Online")
    language = Column(String(50), default="Vietnamese")
    cost_per_article = Column(Float, nullable=False)  # VND - estimated based on tier
    topics = Column(Text, nullable=False)  # JSON array - derived from categories
    target_audience = Column(Text, nullable=False)  # JSON array - derived from demographics
    editorial_contact = Column(String(500), nullable=True)
    submission_guidelines = Column(Text, nullable=True)
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
    """Enhanced API Response model for media outlets"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    website: str
    category: str
    tier: int
    monthly_visits: Optional[int] = None
    visit_duration: Optional[str] = None
    access_from_vietnam: Optional[float] = None
    male_audience: Optional[float] = None
    female_audience: Optional[float] = None
    top_categories: List[str] = []
    cost_per_article: float
    topics: List[str] = []
    target_audience: List[str] = []
    response_time_hours: int
    success_rate: float
    language: str = "Vietnamese"  # Fix: Add missing language field
    circulation: Optional[int] = None  # Add for compatibility
    publisher: Optional[str] = None   # Add for compatibility

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

# =================== COMPREHENSIVE VIETNAMESE MEDIA DATA ===================

def parse_number(value):
    """Parse number from string with commas"""
    if not value or value == "N/A":
        return None
    try:
        return int(str(value).replace(",", ""))
    except:
        return None

def parse_percentage(value):
    """Parse percentage from string"""
    if not value or value == "N/A":
        return None
    try:
        return float(str(value).replace("%", ""))
    except:
        return None

def estimate_cost_by_tier_and_visits(tier, monthly_visits):
    """Estimate cost per article based on tier and traffic"""
    base_costs = {1: 12000000, 2: 6000000, 3: 3000000}  # Base cost by tier
    
    if monthly_visits:
        # Higher traffic = higher cost
        traffic_multiplier = min(2.0, 1 + (monthly_visits / 50000000))
        return int(base_costs.get(tier, 3000000) * traffic_multiplier)
    return base_costs.get(tier, 3000000)

# Comprehensive 100 Media Outlets Data
VIETNAMESE_MEDIA_DATA = [
    # =================== MAINSTREAM MEDIA (A) ===================
    {
        "name": "VnExpress",
        "website": "https://vnexpress.net/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 654000000,
        "monthly_visits": 218660000,
        "visit_duration": "9:00",
        "male_audience": 61.08,
        "female_audience": 38.92,
        "age_18_24": 10,
        "age_25_34": 35,
        "age_35_44": 25,
        "age_45_54": 15,
        "age_55_64": 10,
        "age_65_plus": 5,
        "access_from_vietnam": 86.0,
        "top_categories": ["News & Media", "Tech", "Lifestyle"],
        "cost_per_article": 15000000
    },
    {
        "name": "24H",
        "website": "https://www.24h.com.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 259500000,
        "monthly_visits": 86500000,
        "visit_duration": "12:04",
        "male_audience": 67.81,
        "female_audience": 32.19,
        "age_18_24": 15,
        "age_25_34": 35,
        "age_35_44": 20,
        "age_45_54": 15,
        "age_55_64": 10,
        "age_65_plus": 5,
        "access_from_vietnam": 97.76,
        "top_categories": ["News & Media", "Sports", "Entertainment"],
        "cost_per_article": 12000000
    },
    {
        "name": "Dân trí",
        "website": "https://dantri.com.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 182000000,
        "monthly_visits": 60000000,
        "visit_duration": "13:37",
        "male_audience": 65.38,
        "female_audience": 34.62,
        "age_18_24": 10,
        "age_25_34": 30,
        "age_35_44": 25,
        "age_45_54": 20,
        "age_55_64": 10,
        "age_65_plus": 5,
        "access_from_vietnam": 96.70,
        "top_categories": ["News & Media", "Education", "Society"],
        "cost_per_article": 10000000
    },
    {
        "name": "Tuổi trẻ",
        "website": "https://tuoitre.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 145900000,
        "monthly_visits": 48600000,
        "visit_duration": "6:43",
        "male_audience": 62.76,
        "female_audience": 37.24,
        "age_18_24": 10,
        "age_25_34": 35,
        "age_35_44": 25,
        "age_45_54": 15,
        "age_55_64": 10,
        "age_65_plus": 5,
        "access_from_vietnam": 89.0,
        "top_categories": ["News & Media", "Society", "Law & Government"],
        "cost_per_article": 9000000
    },
    {
        "name": "Thanh niên",
        "website": "https://thanhnien.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 81900000,
        "monthly_visits": 27300000,
        "visit_duration": "7:20",
        "male_audience": 63.17,
        "female_audience": 36.83,
        "age_18_24": 10,
        "age_25_34": 35,
        "age_35_44": 25,
        "age_45_54": 15,
        "age_55_64": 10,
        "age_65_plus": 5,
        "access_from_vietnam": 94.0,
        "top_categories": ["News & Media", "Law & Government", "Business"],
        "cost_per_article": 8000000
    },
    {
        "name": "Soha",
        "website": "https://soha.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 73400000,
        "monthly_visits": 24700000,
        "visit_duration": "6:03",
        "male_audience": 60.37,
        "female_audience": 39.63,
        "age_18_24": 15,
        "age_25_34": 35,
        "age_35_44": 20,
        "age_45_54": 15,
        "age_55_64": 10,
        "age_65_plus": 5,
        "access_from_vietnam": 92.66,
        "top_categories": ["News & Media", "Lifestyle", "Entertainment"],
        "cost_per_article": 7500000
    },
    {
        "name": "Vietnamnet",
        "website": "https://vietnamnet.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 72300000,
        "monthly_visits": 26100000,
        "visit_duration": "5:41",
        "male_audience": 64.89,
        "female_audience": 35.11,
        "age_18_24": 5,
        "age_25_34": 15,
        "age_35_44": 20,
        "age_45_54": 25,
        "age_55_64": 25,
        "age_65_plus": 10,
        "access_from_vietnam": 91.0,
        "top_categories": ["News & Media", "Tech", "Business"],
        "cost_per_article": 8000000
    },
    {
        "name": "Lao động",
        "website": "https://laodong.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 70000000,
        "monthly_visits": 27800000,
        "visit_duration": "6:47",
        "male_audience": 60.0,
        "female_audience": 40.0,
        "age_18_24": 5,
        "age_25_34": 20,
        "age_35_44": 25,
        "age_45_54": 25,
        "age_55_64": 15,
        "age_65_plus": 10,
        "access_from_vietnam": 95.04,
        "top_categories": ["News & Media", "Labor", "Policy"],
        "cost_per_article": 7000000
    },
    {
        "name": "ZNews",
        "website": "https://znews.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 49600000,
        "monthly_visits": 16530000,
        "visit_duration": "7:00",
        "male_audience": 65.93,
        "female_audience": 34.07,
        "age_18_24": 10,
        "age_25_34": 35,
        "age_35_44": 25,
        "age_45_54": 15,
        "age_55_64": 10,
        "age_65_plus": 5,
        "access_from_vietnam": 94.0,
        "top_categories": ["News & Media", "Lifestyle", "Entertainment"],
        "cost_per_article": 6000000
    },
    {
        "name": "Tiền phong",
        "website": "https://tienphong.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 42400000,
        "monthly_visits": 14100000,
        "visit_duration": "11:49",
        "male_audience": 63.39,
        "female_audience": 36.61,
        "age_18_24": 5,
        "age_25_34": 15,
        "age_35_44": 20,
        "age_45_54": 25,
        "age_55_64": 25,
        "age_65_plus": 10,
        "access_from_vietnam": 95.0,
        "top_categories": ["News & Media", "Politics", "Business"],
        "cost_per_article": 5500000
    },
    {
        "name": "Người lao động",
        "website": "https://nld.com.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 34200000,
        "monthly_visits": 11400000,
        "visit_duration": "6:18",
        "male_audience": 60.0,
        "female_audience": 40.0,
        "age_18_24": 10,
        "age_25_34": 30,
        "age_35_44": 25,
        "age_45_54": 20,
        "age_55_64": 10,
        "age_65_plus": 5,
        "access_from_vietnam": 93.79,
        "top_categories": ["News & Media", "Employment", "Society"],
        "cost_per_article": 5000000
    },
    {
        "name": "VTV News",
        "website": "https://vtv.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 20100000,
        "monthly_visits": 6700000,
        "visit_duration": "6:51",
        "male_audience": 59.42,
        "female_audience": 40.58,
        "age_18_24": 10,
        "age_25_34": 35,
        "age_35_44": 25,
        "age_45_54": 15,
        "age_55_64": 10,
        "age_65_plus": 5,
        "access_from_vietnam": 95.0,
        "top_categories": ["Broadcasting", "News & Media", "Education"],
        "cost_per_article": 4000000
    },
    {
        "name": "VTC News",
        "website": "https://vtcnews.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 18300000,
        "monthly_visits": 6100000,
        "visit_duration": "5:23",
        "male_audience": 64.34,
        "female_audience": 35.66,
        "age_18_24": 5,
        "age_25_34": 15,
        "age_35_44": 20,
        "age_45_54": 25,
        "age_55_64": 25,
        "age_65_plus": 10,
        "access_from_vietnam": 93.0,
        "top_categories": ["News & Media", "Broadcasting", "Entertainment"],
        "cost_per_article": 3800000
    },
    {
        "name": "Thể thao & Văn hoá",
        "website": "https://thethaovanhoa.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 16500000,
        "monthly_visits": 5500000,
        "visit_duration": "4:38",
        "male_audience": 64.27,
        "female_audience": 35.73,
        "age_18_24": 5,
        "age_25_34": 15,
        "age_35_44": 20,
        "age_45_54": 25,
        "age_55_64": 25,
        "age_65_plus": 10,
        "access_from_vietnam": 95.0,
        "top_categories": ["News & Media", "Sports", "Entertainment"],
        "cost_per_article": 3500000
    },
    {
        "name": "Pháp luật TP.HCM",
        "website": "https://plo.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 15900000,
        "monthly_visits": 5300000,
        "visit_duration": "6:17",
        "male_audience": 61.0,
        "female_audience": 39.0,
        "age_18_24": 10,
        "age_25_34": 25,
        "age_35_44": 25,
        "age_45_54": 20,
        "age_55_64": 10,
        "age_65_plus": 10,
        "access_from_vietnam": 93.20,
        "top_categories": ["News & Media", "Law", "Local News"],
        "cost_per_article": 3200000
    },
    {
        "name": "Báo tin tức",
        "website": "https://baotintuc.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 15000000,
        "monthly_visits": 5000000,
        "visit_duration": "7:31",
        "male_audience": 67.09,
        "female_audience": 32.91,
        "age_18_24": 5,
        "age_25_34": 20,
        "age_35_44": 25,
        "age_45_54": 25,
        "age_55_64": 15,
        "age_65_plus": 10,
        "access_from_vietnam": 97.13,
        "top_categories": ["News & Media", "Government", "Society"],
        "cost_per_article": 3000000
    },
    {
        "name": "Công an Nhân dân",
        "website": "https://cand.com.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 13260000,
        "monthly_visits": 4421000,
        "visit_duration": "9:14",
        "male_audience": 63.20,
        "female_audience": 36.80,
        "age_18_24": 5,
        "age_25_34": 15,
        "age_35_44": 20,
        "age_45_54": 25,
        "age_55_64": 25,
        "age_65_plus": 10,
        "access_from_vietnam": 95.69,
        "top_categories": ["News & Media", "Law & Government", "Crime"],
        "cost_per_article": 2800000
    },
    {
        "name": "Nhân dân",
        "website": "https://nhandan.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 10200000,
        "monthly_visits": 3400000,
        "visit_duration": "28:57",
        "male_audience": 56.50,
        "female_audience": 43.50,
        "age_18_24": 5,
        "age_25_34": 15,
        "age_35_44": 20,
        "age_45_54": 25,
        "age_55_64": 25,
        "age_65_plus": 10,
        "access_from_vietnam": 93.87,
        "top_categories": ["News & Media", "Politics", "Government"],
        "cost_per_article": 2500000
    },
    {
        "name": "VOV",
        "website": "https://vov.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 8800000,
        "monthly_visits": 2930000,
        "visit_duration": "7:01",
        "male_audience": 60.0,
        "female_audience": 40.0,
        "age_18_24": 10,
        "age_25_34": 30,
        "age_35_44": 25,
        "age_45_54": 20,
        "age_55_64": 10,
        "age_65_plus": 5,
        "access_from_vietnam": 95.0,
        "top_categories": ["News & Media", "Radio", "Politics"],
        "cost_per_article": 2200000
    },
    {
        "name": "Vietnam Plus",
        "website": "https://www.vietnamplus.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 8400000,
        "monthly_visits": 2800000,
        "visit_duration": "14:30",
        "male_audience": 60.0,
        "female_audience": 40.0,
        "age_18_24": 10,
        "age_25_34": 30,
        "age_35_44": 25,
        "age_45_54": 20,
        "age_55_64": 10,
        "age_65_plus": 5,
        "access_from_vietnam": 95.0,
        "top_categories": ["News & Media", "Government", "Business"],
        "cost_per_article": 2000000
    },
    {
        "name": "Công an TP.HCM",
        "website": "https://congan.com.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 4599000,
        "monthly_visits": 1500000,
        "visit_duration": "2:39",
        "male_audience": 63.0,
        "female_audience": 37.0,
        "age_18_24": 5,
        "age_25_34": 15,
        "age_35_44": 20,
        "age_45_54": 25,
        "age_55_64": 25,
        "age_65_plus": 10,
        "access_from_vietnam": 97.48,
        "top_categories": ["Law & Government", "Crime", "Public Safety"],
        "cost_per_article": 1800000
    },
    {
        "name": "Pháp luật Việt Nam",
        "website": "https://baophapluat.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 4500000,
        "monthly_visits": 1500000,
        "visit_duration": "10:43",
        "male_audience": 61.14,
        "female_audience": 38.86,
        "age_18_24": 5,
        "age_25_34": 15,
        "age_35_44": 20,
        "age_45_54": 25,
        "age_55_64": 25,
        "age_65_plus": 10,
        "access_from_vietnam": 94.10,
        "top_categories": ["News & Media", "Legal", "Government"],
        "cost_per_article": 1800000
    },
    {
        "name": "Sài Gòn giải phóng",
        "website": "https://www.sggp.org.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 4500000,
        "monthly_visits": 1500000,
        "visit_duration": "29:17",
        "male_audience": 66.30,
        "female_audience": 33.70,
        "age_18_24": 5,
        "age_25_34": 15,
        "age_35_44": 20,
        "age_45_54": 25,
        "age_55_64": 25,
        "age_65_plus": 10,
        "access_from_vietnam": 92.61,
        "top_categories": ["News & Media", "Politics", "Local News"],
        "cost_per_article": 1800000
    },
    {
        "name": "VOH",
        "website": "https://voh.com.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 4300000,
        "monthly_visits": 1430000,
        "visit_duration": "6:46",
        "male_audience": 57.28,
        "female_audience": 42.72,
        "age_18_24": 15,
        "age_25_34": 35,
        "age_35_44": 25,
        "age_45_54": 15,
        "age_55_64": 5,
        "age_65_plus": 5,
        "access_from_vietnam": 93.0,
        "top_categories": ["Broadcasting", "Radio", "Entertainment"],
        "cost_per_article": 1700000
    },
    {
        "name": "Hà Nội mới",
        "website": "https://hanoimoi.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 3000000,
        "monthly_visits": 1200000,
        "visit_duration": "5:21",
        "male_audience": 59.82,
        "female_audience": 40.18,
        "age_18_24": 5,
        "age_25_34": 15,
        "age_35_44": 20,
        "age_45_54": 25,
        "age_55_64": 25,
        "age_65_plus": 10,
        "access_from_vietnam": 96.58,
        "top_categories": ["Local News", "Government", "Society"],
        "cost_per_article": 1500000
    },
    {
        "name": "Thế giới và Việt Nam",
        "website": "https://baoquocte.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 2000000,
        "monthly_visits": 670000,
        "visit_duration": "5:21",
        "male_audience": 60.0,
        "female_audience": 40.0,
        "age_18_24": 5,
        "age_25_34": 20,
        "age_35_44": 25,
        "age_45_54": 25,
        "age_55_64": 15,
        "age_65_plus": 10,
        "access_from_vietnam": 95.0,
        "top_categories": ["News & Media", "Government", "International Relations"],
        "cost_per_article": 1200000
    },
    {
        "name": "Việt Nam News",
        "website": "https://vietnamnews.vn/",
        "category": "MAINSTREAM",
        "tier": 1,
        "total_visits_3months": 1050000,
        "monthly_visits": 350000,
        "visit_duration": "5:16",
        "male_audience": 55.0,
        "female_audience": 45.0,
        "age_18_24": 10,
        "age_25_34": 25,
        "age_35_44": 25,
        "age_45_54": 20,
        "age_55_64": 15,
        "age_65_plus": 5,
        "access_from_vietnam": 90.0,
        "top_categories": ["News & Media", "Business", "International News"],
        "cost_per_article": 1000000,
        "language": "English"
    },
    {
        "name": "Lao động thủ đô",
        "website": "https://laodongthudo.vn/",
        "category": "MAINSTREAM",
        "tier": 2,
        "total_visits_3months": 900000,
        "monthly_visits": 309700,
        "visit_duration": "6:05",
        "male_audience": 63.47,
        "female_audience": 36.53,
        "age_18_24": 5,
        "age_25_34": 15,
        "age_35_44": 20,
        "age_45_54": 25,
        "age_55_64": 25,
        "age_65_plus": 10,
        "access_from_vietnam": 95.12,
        "top_categories": ["News & Media", "Government", "Labor"],
        "cost_per_article": 800000
    },
    {
        "name": "Đời sống và Phát luật",
        "website": "https://www.doisongphapluat.com/",
        "category": "MAINSTREAM",
        "tier": 2,
        "total_visits_3months": 12800,
        "monthly_visits": 4000,
        "visit_duration": "4:58",
        "male_audience": 62.0,
        "female_audience": 38.0,
        "age_18_24": 10,
        "age_25_34": 30,
        "age_35_44": 25,
        "age_45_54": 20,
        "age_55_64": 10,
        "age_65_plus": 5,
        "access_from_vietnam": 90.73,
        "top_categories": ["News & Media", "Legal", "Lifestyle"],
        "cost_per_article": 500000
    },
    {
        "name": "Tuổi trẻ Thủ đô",
        "website": "https://tuoitrethudo.com.vn/",
        "category": "MAINSTREAM",
        "tier": 2,
        "total_visits_3months": 5400,
        "monthly_visits": 1800,
        "visit_duration": "1:11",
        "male_audience": 55.0,
        "female_audience": 45.0,
        "age_18_24": 15,
        "age_25_34": 30,
        "age_35_44": 25,
        "age_45_54": 15,
        "age_55_64": 10,
        "age_65_plus": 5,
        "access_from_vietnam": 95.0,
        "top_categories": ["News & Media", "Youth Affairs", "Government"],
        "cost_per_article": 400000
    },

    # =================== BUSINESS MEDIA (B) ===================
    {
        "name": "CafeF",
        "website": "https://cafef.vn/",
        "category": "BUSINESS",
        "tier": 1,
        "total_visits_3months": 84240000,
        "monthly_visits": 28080000,
        "visit_duration": "6:45",
        "male_audience": 64.79,
        "female_audience": 35.21,
        "age_18_24": 10,
        "age_25_34": 40,
        "age_35_44": 25,
        "age_45_54": 15,
        "age_55_64": 5,
        "age_65_plus": 5,
        "access_from_vietnam": 97.26,
        "top_categories": ["Finance", "Investing", "News & Media"],
        "cost_per_article": 8000000
    },
    {
        "name": "CafeBiz",
        "website": "https://cafebiz.vn/",
        "category": "BUSINESS",
        "tier": 1,
        "total_visits_3months": 12990000,
        "monthly_visits": 4331000,
        "visit_duration": "4:45",
        "male_audience": 60.76,
        "female_audience": 39.24,
        "age_18_24": 15,
        "age_25_34": 35,
        "age_35_44": 25,
        "age_45_54": 15,
        "age_55_64": 5,
        "age_65_plus": 5,
        "access_from_vietnam": 96.10,
        "top_categories": ["News & Media", "Tech", "Investing"],
        "cost_per_article": 5000000
    },
    {
        "name": "VnEconomy",
        "website": "https://vneconomy.vn/",
        "category": "BUSINESS", 
        "tier": 1,
        "total_visits_3months": 10140000,
        "monthly_visits": 3381000,
        "visit_duration": "1:18",
        "male_audience": 59.97,
        "female_audience": 40.03,
        "access_from_vietnam": 95.51,
        "top_categories": ["News & Media", "Investing", "Government"],
        "cost_per_article": 4500000
    },
    {
        "name": "Kinh tế và Đô thị",
        "website": "https://kinhtedothi.vn/",
        "category": "BUSINESS",
        "tier": 1,
        "total_visits_3months": 8625000,
        "monthly_visits": 2875000,
        "visit_duration": "1:33",
        "access_from_vietnam": 97.0,
        "top_categories": ["News & Media", "Government", "Economy"],
        "cost_per_article": 4000000
    },
    {
        "name": "Công Thương",
        "website": "https://congthuong.vn/",
        "category": "BUSINESS",
        "tier": 1,
        "total_visits_3months": 6023000,
        "monthly_visits": 2007000,
        "visit_duration": "1:29",
        "male_audience": 64.52,
        "female_audience": 35.48,
        "age_18_24": 10,
        "age_25_34": 30,
        "age_35_44": 25,
        "age_45_54": 20,
        "age_55_64": 10,
        "age_65_plus": 5,
        "access_from_vietnam": 97.26,
        "top_categories": ["News & Media", "Government", "Investing"],
        "cost_per_article": 3500000
    },
    {
        "name": "Đầu tư",
        "website": "https://baodautu.vn/",
        "category": "BUSINESS",
        "tier": 1,
        "total_visits_3months": 4224000,
        "monthly_visits": 1408000,
        "visit_duration": "1:22",
        "male_audience": 60.0,
        "female_audience": 40.0,
        "age_18_24": 10,
        "age_25_34": 35,
        "age_35_44": 25,
        "age_45_54": 20,
        "age_55_64": 5,
        "age_65_plus": 5,
        "access_from_vietnam": 96.24,
        "top_categories": ["News & Media", "Business", "Economy"],
        "cost_per_article": 3000000
    },
    {
        "name": "Vietstock",
        "website": "https://vietstock.vn/",
        "category": "BUSINESS",
        "tier": 1,
        "total_visits_3months": 4000000,
        "monthly_visits": 1330000,
        "visit_duration": "4:45",
        "male_audience": 65.10,
        "female_audience": 34.90,
        "access_from_vietnam": 97.79,
        "top_categories": ["Finance", "Investing", "News & Media"],
        "cost_per_article": 2800000
    },
    {
        "name": "BNews",
        "website": "https://bnews.vn/",
        "category": "BUSINESS",
        "tier": 1,
        "total_visits_3months": 2516000,
        "monthly_visits": 838000,
        "visit_duration": "2:48",
        "male_audience": 65.45,
        "female_audience": 34.55,
        "access_from_vietnam": 98.84,
        "top_categories": ["News & Media", "Investing", "Social Media"],
        "cost_per_article": 2500000
    },
    {
        "name": "VietnamBiz",
        "website": "https://vietnambiz.vn/",
        "category": "BUSINESS",
        "tier": 1,
        "total_visits_3months": 2300000,
        "monthly_visits": 770000,
        "visit_duration": "1:53",
        "male_audience": 57.09,
        "female_audience": 42.91,
        "access_from_vietnam": 94.84,
        "top_categories": ["News & Media", "Finance", "Economy"],
        "cost_per_article": 2200000
    },
    {
        "name": "Kinh tế Sài Gòn",
        "website": "https://thesaigontimes.vn/",
        "category": "BUSINESS",
        "tier": 1,
        "total_visits_3months": 1636000,
        "monthly_visits": 545000,
        "visit_duration": "1:16",
        "access_from_vietnam": 92.50,
        "top_categories": ["News & Media", "Business", "Economy"],
        "cost_per_article": 2000000
    },
    {
        "name": "Diễn đàn Doanh nghiệp",
        "website": "https://diendandoanhnghiep.vn/",
        "category": "BUSINESS",
        "tier": 1,
        "total_visits_3months": 1246000,
        "monthly_visits": 415000,
        "visit_duration": "0:43",
        "access_from_vietnam": 95.04,
        "top_categories": ["News & Media", "Business", "Economy"],
        "cost_per_article": 1800000
    },
    {
        "name": "Forbes Vietnam",
        "website": "https://forbes.vn/",
        "category": "BUSINESS",
        "tier": 1,
        "total_visits_3months": 258000,
        "monthly_visits": 86000,
        "visit_duration": "1:30",
        "access_from_vietnam": 89.42,
        "top_categories": ["News & Media", "Tech", "Investing"],
        "cost_per_article": 1500000
    },
    {
        "name": "Vietnam Investment Review",
        "website": "https://vir.com.vn/",
        "category": "BUSINESS",
        "tier": 1,
        "total_visits_3months": 178200,
        "monthly_visits": 59400,
        "visit_duration": "1:40",
        "top_categories": ["News & Media", "Business", "Economy"],
        "cost_per_article": 1200000,
        "language": "English"
    },
    {
        "name": "Nhịp cầu đầu tư",
        "website": "https://nhipcaudautu.vn/",
        "category": "BUSINESS",
        "tier": 1,
        "total_visits_3months": 177000,
        "monthly_visits": 59000,
        "visit_duration": "18:42",
        "access_from_vietnam": 92.14,
        "top_categories": ["News & Media", "Business", "Economy"],
        "cost_per_article": 1200000
    },
    {
        "name": "Thời báo Tài chính",
        "website": "https://thoibaotaichinhvietnam.vn/",
        "category": "BUSINESS",
        "tier": 2,
        "total_visits_3months": 570800,
        "monthly_visits": 190300,
        "visit_duration": "2:49",
        "top_categories": ["News & Media", "Finance", "Government"],
        "cost_per_article": 1000000
    },
    {
        "name": "Tin nhanh chứng khoán",
        "website": "https://www.tinnhanhchungkhoan.vn/",
        "category": "BUSINESS",
        "tier": 2,
        "total_visits_3months": 537800,
        "monthly_visits": 179300,
        "visit_duration": "1:33",
        "male_audience": 66.99,
        "female_audience": 33.01,
        "access_from_vietnam": 97.26,
        "top_categories": ["News & Media", "Investing", "Tech"],
        "cost_per_article": 900000
    },
    {
        "name": "Thời báo Ngân Hàng",
        "website": "https://thoibaonganhang.vn/",
        "category": "BUSINESS",
        "tier": 2,
        "total_visits_3months": 459900,
        "monthly_visits": 138600,
        "visit_duration": "0:55",
        "top_categories": ["News & Media", "Finance", "Banking"],
        "cost_per_article": 800000
    },
    {
        "name": "Doanh nhân Sài Gòn",
        "website": "https://doanhnhansaigon.vn/",
        "category": "BUSINESS",
        "tier": 2,
        "total_visits_3months": 365000,
        "monthly_visits": 121900,
        "visit_duration": "1:03",
        "male_audience": 58.26,
        "female_audience": 41.74,
        "age_18_24": 10,
        "age_25_34": 20,
        "age_35_44": 25,
        "age_45_54": 25,
        "age_55_64": 15,
        "age_65_plus": 5,
        "access_from_vietnam": 92.19,
        "top_categories": ["News & Media", "Investing", "Developer Software"],
        "cost_per_article": 700000
    },
    {
        "name": "Tạp chí Tài chính",
        "website": "https://tapchitaichinh.vn/",
        "category": "BUSINESS",
        "tier": 2,
        "total_visits_3months": 319100,
        "monthly_visits": 106400,
        "visit_duration": "8:47",
        "top_categories": ["News & Media", "Finance", "Government"],
        "cost_per_article": 650000
    },
    {
        "name": "Việt Nam mới",
        "website": "https://vietnammoi.vn/",
        "category": "BUSINESS",
        "tier": 2,
        "total_visits_3months": 249100,
        "monthly_visits": 83000,
        "visit_duration": "1:23",
        "male_audience": 55.90,
        "female_audience": 44.10,
        "access_from_vietnam": 98.03,
        "top_categories": ["News & Media", "Social Media", "Real Estate"],
        "cost_per_article": 600000
    },
    {
        "name": "TheLEADER",
        "website": "https://theleader.vn/",
        "category": "BUSINESS",
        "tier": 2,
        "total_visits_3months": 178000,
        "monthly_visits": 59000,
        "top_categories": ["News & Media", "Business", "Economy"],
        "cost_per_article": 550000
    },
    {
        "name": "Doanh nhân Plus",
        "website": "https://doanhnhanplus.vn/",
        "category": "BUSINESS",
        "tier": 2,
        "total_visits_3months": 107600,
        "monthly_visits": 35870,
        "visit_duration": "0:52",
        "access_from_vietnam": 99.11,
        "top_categories": ["News & Media", "Business", "Economy"],
        "cost_per_article": 500000
    },
    {
        "name": "BizHub",
        "website": "http://bizhub.vn/",
        "category": "BUSINESS",
        "tier": 3,
        "total_visits_3months": 53000,
        "monthly_visits": 17900,
        "visit_duration": "2:14",
        "access_from_vietnam": 52.85,
        "top_categories": ["News & Media", "Business", "Economy"],
        "cost_per_article": 400000
    },
    {
        "name": "Vietnam Logistics Review",
        "website": "https://vlr.vn/",
        "category": "BUSINESS",
        "tier": 3,
        "total_visits_3months": 24200,
        "monthly_visits": 8070,
        "visit_duration": "1:18",
        "access_from_vietnam": 40.49,
        "top_categories": ["News & Media", "Logistics", "Economy"],
        "cost_per_article": 350000
    },
    {
        "name": "VCCI",
        "website": "https://vccinews.com/",
        "category": "BUSINESS",
        "tier": 3,
        "total_visits_3months": 9400,
        "monthly_visits": 3130,
        "visit_duration": "2:04",
        "top_categories": ["News & Media", "Business", "Economy"],
        "cost_per_article": 300000
    },

    # =================== TECHNOLOGY MEDIA (C) ===================
    {
        "name": "Tinh tế",
        "website": "https://tinhte.vn/",
        "category": "TECHNOLOGY",
        "tier": 1,
        "total_visits_3months": 11200000,
        "monthly_visits": 3730000,
        "visit_duration": "1:24",
        "top_categories": ["Computers Electronics and Technology", "Tech Reviews", "Mobile"],
        "cost_per_article": 4000000
    },
    {
        "name": "GenK",
        "website": "https://genk.vn/",
        "category": "TECHNOLOGY",
        "tier": 1,
        "total_visits_3months": 5900000,
        "monthly_visits": 1970000,
        "top_categories": ["Computers Electronics and Technology", "Gaming", "Tech News"],
        "cost_per_article": 3500000
    },
    {
        "name": "Techrum",
        "website": "https://www.techrum.vn/forums/",
        "category": "TECHNOLOGY",
        "tier": 2,
        "total_visits_3months": 195600,
        "monthly_visits": 65200,
        "visit_duration": "0:46",
        "top_categories": ["Social Media Networks", "Tech Forums", "Community"],
        "cost_per_article": 1000000
    },
    {
        "name": "Nghe nhìn Việt Nam",
        "website": "https://nghenhinvietnam.vn/",
        "category": "TECHNOLOGY",
        "tier": 2,
        "total_visits_3months": 101600,
        "monthly_visits": 33900,
        "visit_duration": "0:18",
        "top_categories": ["Audio Video", "Electronics", "Technology"],
        "cost_per_article": 800000
    },
    {
        "name": "Công nghệ Việt",
        "website": "https://congngheviet.com/",
        "category": "TECHNOLOGY",
        "tier": 3,
        "total_visits_3months": 19300,
        "top_categories": ["Vietnamese Technology", "Innovation", "Startups"],
        "cost_per_article": 600000
    },
    {
        "name": "Techsignin",
        "website": "https://www.techsignin.com/",
        "category": "TECHNOLOGY",
        "tier": 3,
        "top_categories": ["Technology News", "Digital Trends", "Innovation"],
        "cost_per_article": 500000
    },
    {
        "name": "Điện tử và Ứng dụng",
        "website": "https://dientuungdung.vn/",
        "category": "TECHNOLOGY",
        "tier": 3,
        "total_visits_3months": 49000,
        "monthly_visits": 16300,
        "visit_duration": "9:27",
        "top_categories": ["Electronics", "Applications", "Technology"],
        "cost_per_article": 550000
    },
    {
        "name": "Thế giới số",
        "website": "https://tgs.vn/",
        "category": "TECHNOLOGY",
        "tier": 3,
        "total_visits_3months": 12000,
        "monthly_visits": 4000,
        "visit_duration": "0:04",
        "top_categories": ["Consumer Electronics", "Digital World", "Tech Reviews"],
        "cost_per_article": 450000
    },

    # =================== EDUCATION MEDIA (D) ===================
    {
        "name": "Giáo dục Thời đại",
        "website": "https://giaoducthoidai.vn/",
        "category": "EDUCATION",
        "tier": 1,
        "total_visits_3months": 2700000,
        "monthly_visits": 900000,
        "visit_duration": "3:14",
        "male_audience": 65.34,
        "female_audience": 34.66,
        "access_from_vietnam": 95.87,
        "top_categories": ["News & Media", "Education", "Tech"],
        "cost_per_article": 2500000
    },
    {
        "name": "Hoa học trò",
        "website": "https://hoahoctro.tienphong.vn/",
        "category": "EDUCATION",
        "tier": 1,
        "total_visits_3months": 2100000,
        "monthly_visits": 700000,
        "visit_duration": "2:24",
        "male_audience": 51.70,
        "female_audience": 48.30,
        "top_categories": ["News & Media", "Education", "Youth"],
        "cost_per_article": 2000000
    },
    {
        "name": "Giáo dục Thủ đô",
        "website": "https://giaoducthudo.giaoducthoidai.vn/",
        "category": "EDUCATION",
        "tier": 2,
        "top_categories": ["Education", "Local News", "Government"],
        "cost_per_article": 1000000
    },
    {
        "name": "Mực tím",
        "website": "https://muctim.tuoitre.vn/",
        "category": "EDUCATION",
        "tier": 2,
        "top_categories": ["Education", "Youth", "Student Life"],
        "cost_per_article": 800000
    },
    {
        "name": "Giáo dục TP. Hồ Chí Minh",
        "website": "https://www.giaoduc.edu.vn/",
        "category": "EDUCATION",
        "tier": 2,
        "total_visits_3months": 38800,
        "monthly_visits": 12900,
        "visit_duration": "0:53",
        "top_categories": ["Education", "Local Government", "Schools"],
        "cost_per_article": 600000
    },

    # =================== WOMAN & FAMILY MEDIA (E) ===================
    {
        "name": "Eva",
        "website": "https://eva.vn/",
        "category": "WOMAN_FAMILY",
        "tier": 1,
        "total_visits_3months": 9100000,
        "monthly_visits": 3030000,
        "visit_duration": "4:02",
        "top_categories": ["News & Media", "Lifestyle", "Women"],
        "cost_per_article": 3000000
    },
    {
        "name": "aFamily",
        "website": "https://afamily.vn/",
        "category": "WOMAN_FAMILY",
        "tier": 1,
        "total_visits_3months": 5400000,
        "monthly_visits": 1800000,
        "visit_duration": "1:56",
        "male_audience": 56.14,
        "female_audience": 43.86,
        "access_from_vietnam": 92.22,
        "top_categories": ["News & Media", "Family", "Parenting"],
        "cost_per_article": 2500000
    },
    {
        "name": "Phụ nữ Việt Nam",
        "website": "https://phunuvietnam.vn/",
        "category": "WOMAN_FAMILY",
        "tier": 2,
        "male_audience": 60.94,
        "female_audience": 39.06,
        "top_categories": ["News & Media", "Women", "Social Issues"],
        "cost_per_article": 1500000
    },
    {
        "name": "Web Trẻ thơ",
        "website": "https://www.webtretho.com/",
        "category": "WOMAN_FAMILY",
        "tier": 2,
        "top_categories": ["Parenting", "Children", "Family"],
        "cost_per_article": 1200000
    },
    {
        "name": "Phụ nữ thủ đô",
        "website": "https://baophunuthudo.vn/",
        "category": "WOMAN_FAMILY",
        "tier": 2,
        "top_categories": ["Women", "Local News", "Social Issues"],
        "cost_per_article": 1000000
    },
    {
        "name": "Phụ nữ TP.HCM",
        "website": "https://www.phunuonline.com.vn/",
        "category": "WOMAN_FAMILY",
        "tier": 2,
        "total_visits_3months": 613700,
        "monthly_visits": 204600,
        "visit_duration": "2:10",
        "top_categories": ["Women", "Local News", "Lifestyle"],
        "cost_per_article": 900000
    },
    {
        "name": "Gia đình Việt Nam",
        "website": "https://giadinhonline.vn/",
        "category": "WOMAN_FAMILY",
        "tier": 2,
        "total_visits_3months": 311600,
        "monthly_visits": 103900,
        "visit_duration": "0:43",
        "top_categories": ["Family", "Parenting", "Lifestyle"],
        "cost_per_article": 700000
    },

    # =================== TOURISM MEDIA (F) ===================
    {
        "name": "Tạp chí Du lịch TP.HCM",
        "website": "https://tcdulichtphcm.vn/",
        "category": "TOURISM",
        "tier": 2,
        "total_visits_3months": 131100,
        "monthly_visits": 43700,
        "visit_duration": "4:40",
        "top_categories": ["Tourism", "Travel", "Local Guide"],
        "cost_per_article": 800000
    },

    # =================== YOUTH & ENTERTAINMENT MEDIA (G) ===================
    {
        "name": "Kênh 14",
        "website": "https://kenh14.vn/",
        "category": "YOUTH_ENTERTAINMENT",
        "tier": 1,
        "male_audience": 52.05,
        "female_audience": 47.95,
        "top_categories": ["News & Media", "Entertainment", "Youth"],
        "cost_per_article": 5000000
    },
    {
        "name": "SaoStar",
        "website": "https://www.saostar.vn/",
        "category": "YOUTH_ENTERTAINMENT",
        "tier": 1,
        "top_categories": ["Celebrity News", "Entertainment", "Lifestyle"],
        "cost_per_article": 4000000
    },
    {
        "name": "Ngôi sao (VnExpress)",
        "website": "https://ngoisao.vnexpress.net/",
        "category": "YOUTH_ENTERTAINMENT",
        "tier": 1,
        "total_visits_3months": 1540000,
        "monthly_visits": 510000,
        "visit_duration": "9:52",
        "top_categories": ["Celebrity News", "Entertainment", "Showbiz"],
        "cost_per_article": 3000000
    },
    {
        "name": "Ngôi sao (.net)",
        "website": "https://ngoisao.net.vn/",
        "category": "YOUTH_ENTERTAINMENT",
        "tier": 2,
        "top_categories": ["Celebrity News", "Entertainment", "Gossip"],
        "cost_per_article": 1500000
    },
    {
        "name": "Tiin",
        "website": "https://tiin.vn/",
        "category": "YOUTH_ENTERTAINMENT",
        "tier": 2,
        "top_categories": ["Youth News", "Social Media", "Trends"],
        "cost_per_article": 1200000
    },
    {
        "name": "Top List",
        "website": "https://toplist.vn/",
        "category": "YOUTH_ENTERTAINMENT",
        "tier": 2,
        "total_visits_3months": 427300,
        "monthly_visits": 142400,
        "visit_duration": "1:56",
        "top_categories": ["Entertainment", "Rankings", "Reviews"],
        "cost_per_article": 1000000
    },
    {
        "name": "Yeah1",
        "website": "https://yeah1.com/",
        "category": "YOUTH_ENTERTAINMENT",
        "tier": 2,
        "total_visits_3months": 133100,
        "monthly_visits": 44400,
        "visit_duration": "0:52",
        "male_audience": 59.64,
        "female_audience": 40.36,
        "access_from_vietnam": 91.0,
        "top_categories": ["Entertainment", "Social Media", "Digital Content"],
        "cost_per_article": 800000
    },
    {
        "name": "Bestie",
        "website": "https://www.bestie.vn/",
        "category": "YOUTH_ENTERTAINMENT",
        "tier": 3,
        "top_categories": ["Youth Lifestyle", "Trends", "Social"],
        "cost_per_article": 600000
    },
    {
        "name": "YAN News",
        "website": "https://www.yan.vn/",
        "category": "YOUTH_ENTERTAINMENT",
        "tier": 3,
        "total_visits_3months": 83600,
        "monthly_visits": 27900,
        "visit_duration": "1:47",
        "top_categories": ["Youth News", "Entertainment", "Lifestyle"],
        "cost_per_article": 500000
    },

    # =================== AGRICULTURE MEDIA (H) ===================
    {
        "name": "Dân Việt",
        "website": "https://danviet.vn/",
        "category": "AGRICULTURE",
        "tier": 1,
        "top_categories": ["Agriculture", "Rural News", "Farming"],
        "cost_per_article": 2000000
    },
    {
        "name": "Nông nghiệp & Môi trường",
        "website": "https://nongnghiepmoitruong.vn/",
        "category": "AGRICULTURE",
        "tier": 1,
        "top_categories": ["Agriculture", "Environment", "Sustainability"],
        "cost_per_article": 1800000
    },
    {
        "name": "Chăn nuôi Việt Nam",
        "website": "https://nhachannuoi.vn/",
        "category": "AGRICULTURE",
        "tier": 3,
        "top_categories": ["Livestock", "Animal Husbandry", "Farming"],
        "cost_per_article": 800000
    },
    {
        "name": "Người nuôi tôm",
        "website": "https://nguoinuoitom.vn/",
        "category": "AGRICULTURE",
        "tier": 3,
        "top_categories": ["Aquaculture", "Shrimp Farming", "Seafood"],
        "cost_per_article": 600000
    },
    {
        "name": "Nông thôn Việt",
        "website": "https://nongthonviet.com.vn/",
        "category": "AGRICULTURE",
        "tier": 3,
        "top_categories": ["Rural Development", "Agriculture", "Community"],
        "cost_per_article": 700000
    },
    {
        "name": "Tép Bạc",
        "website": "https://tepbac.com/",
        "category": "AGRICULTURE",
        "tier": 3,
        "top_categories": ["Aquaculture", "Shrimp", "Seafood Industry"],
        "cost_per_article": 500000
    },
    {
        "name": "Thủy sản Việt Nam",
        "website": "https://thuysanvietnam.com.vn/",
        "category": "AGRICULTURE",
        "tier": 3,
        "top_categories": ["Aquaculture", "Seafood", "Marine Industry"],
        "cost_per_article": 650000
    },

    # =================== HEALTH MEDIA (I) ===================
    {
        "name": "Sức khỏe và Đời sống",
        "website": "https://suckhoedoisong.vn/",
        "category": "HEALTH",
        "tier": 1,
        "total_visits_3months": 14700000,
        "monthly_visits": 4900000,
        "visit_duration": "0:20",
        "top_categories": ["Health", "Medicine", "Wellness"],
        "cost_per_article": 4500000
    },
    {
        "name": "Alo Bác sĩ",
        "website": "https://alobacsi.com/",
        "category": "HEALTH",
        "tier": 3,
        "total_visits_3months": 155700,
        "monthly_visits": 51900,
        "visit_duration": "11:12",
        "top_categories": ["Health Consultation", "Medical Advice", "Wellness"],
        "cost_per_article": 800000
    },

    # =================== AUTOMOTIVE MEDIA (J) ===================
    {
        "name": "Giao thông",
        "website": "https://www.baogiaothong.vn/",
        "category": "AUTOMOTIVE",
        "tier": 1,
        "total_visits_3months": 12930000,
        "monthly_visits": 4311000,
        "visit_duration": "0:51",
        "male_audience": 69.62,
        "female_audience": 30.38,
        "age_18_24": 15.88,
        "age_25_34": 17.93,
        "age_35_44": 7.60,
        "age_45_54": 17.90,
        "age_55_64": 25.18,
        "age_65_plus": 15.51,
        "access_from_vietnam": 97.97,
        "top_categories": ["Transportation", "Traffic", "Automotive"],
        "cost_per_article": 4000000
    },
    {
        "name": "AutoPro",
        "website": "https://autopro.com.vn/",
        "category": "AUTOMOTIVE",
        "tier": 1,
        "total_visits_3months": 4048000,
        "monthly_visits": 1349000,
        "visit_duration": "8:10",
        "access_from_vietnam": 97.59,
        "top_categories": ["Automotive", "Car Reviews", "Industry News"],
        "cost_per_article": 3000000
    },
    {
        "name": "Ô tô Sài Gòn",
        "website": "https://www.otosaigon.com/",
        "category": "AUTOMOTIVE",
        "tier": 1,
        "total_visits_3months": 2900000,
        "monthly_visits": 972900,
        "visit_duration": "3:31",
        "male_audience": 72.78,
        "female_audience": 27.22,
        "age_18_24": 18.24,
        "age_25_34": 26.74,
        "age_35_44": 8.57,
        "age_45_54": 18.45,
        "age_55_64": 19.74,
        "age_65_plus": 8.27,
        "access_from_vietnam": 97.31,
        "top_categories": ["Automotive", "Car Sales", "Local Market"],
        "cost_per_article": 2500000
    },
    {
        "name": "Xe hay",
        "website": "https://xehay.vn/",
        "category": "AUTOMOTIVE",
        "tier": 2,
        "total_visits_3months": 762600,
        "monthly_visits": 254200,
        "visit_duration": "0:18",
        "male_audience": 73.76,
        "female_audience": 26.24,
        "age_18_24": 17.81,
        "age_25_34": 22.26,
        "age_35_44": 8.08,
        "age_45_54": 18.80,
        "age_55_64": 21.77,
        "age_65_plus": 11.29,
        "access_from_vietnam": 95.52,
        "top_categories": ["Automotive", "Car Reviews", "News"],
        "cost_per_article": 1500000
    },
    {
        "name": "Tin Xe",
        "website": "https://tinxe.vn/",
        "category": "AUTOMOTIVE",
        "tier": 2,
        "total_visits_3months": 306490,
        "monthly_visits": 102000,
        "visit_duration": "0:53",
        "male_audience": 74.15,
        "female_audience": 25.85,
        "age_18_24": 24.94,
        "age_25_34": 21.53,
        "age_35_44": 7.79,
        "age_45_54": 17.53,
        "age_55_64": 18.83,
        "age_65_plus": 9.38,
        "access_from_vietnam": 97.19,
        "top_categories": ["Automotive", "Car News", "Market"],
        "cost_per_article": 1200000
    },
    {
        "name": "AutoDaily",
        "website": "https://autodaily.vn/",
        "category": "AUTOMOTIVE",
        "tier": 2,
        "total_visits_3months": 212300,
        "monthly_visits": 70800,
        "visit_duration": "0:19",
        "top_categories": ["Automotive", "Daily News", "Industry"],
        "cost_per_article": 1000000
    }
]

# Process and standardize the data
def standardize_media_data():
    """Standardize and enrich media data with better error handling"""
    for media in VIETNAMESE_MEDIA_DATA:
        try:
            # Set defaults for missing fields
            if 'publisher' not in media:
                media['publisher'] = f"{media['name']} Media"
            
            if 'circulation' not in media:
                media['circulation'] = media.get('monthly_visits', 1000000)
            
            if 'publication_format' not in media:
                media['publication_format'] = "Online"
            
            if 'language' not in media:
                media['language'] = "Vietnamese"
            
            # Estimate cost if not provided
            if 'cost_per_article' not in media:
                media['cost_per_article'] = estimate_cost_by_tier_and_visits(
                    media['tier'], 
                    media.get('monthly_visits')
                )
            
            # Convert top_categories to topics for compatibility
            if 'topics' not in media:
                media['topics'] = media.get('top_categories', [])
            
            # Ensure topics is a list
            if isinstance(media['topics'], str):
                try:
                    media['topics'] = json.loads(media['topics'])
                except:
                    media['topics'] = [media['topics']]
            elif not isinstance(media['topics'], list):
                media['topics'] = []
            
            # Generate target_audience from demographics with safety checks
            if 'target_audience' not in media:
                audiences = []
                
                # Gender-based audiences
                male_aud = media.get('male_audience', 50)
                female_aud = media.get('female_audience', 50)
                
                if male_aud and male_aud > 60:
                    audiences.append("Male-dominant audience")
                elif female_aud and female_aud > 60:
                    audiences.append("Female-dominant audience")
                else:
                    audiences.append("General audience")
                
                # Age-based audiences
                if media.get('age_18_24', 0) and media['age_18_24'] > 20:
                    audiences.append("Young adults")
                if media.get('age_25_34', 0) and media['age_25_34'] > 30:
                    audiences.append("Millennials")
                if media.get('age_45_54', 0) and media['age_45_54'] > 20:
                    audiences.append("Middle-aged professionals")
                
                # Category-based audiences
                category = media.get('category', '').upper()
                if category == 'BUSINESS':
                    audiences.extend(["Business professionals", "Investors", "Entrepreneurs"])
                elif category == 'TECHNOLOGY':
                    audiences.extend(["Tech enthusiasts", "IT professionals", "Early adopters"])
                elif category == 'YOUTH_ENTERTAINMENT':
                    audiences.extend(["Young adults", "Entertainment fans", "Social media users"])
                elif category == 'WOMAN_FAMILY':
                    audiences.extend(["Women", "Families", "Parents"])
                else:
                    audiences.append("General public")
                
                media['target_audience'] = list(set(audiences))
            
            # Ensure target_audience is a list
            if isinstance(media['target_audience'], str):
                try:
                    media['target_audience'] = json.loads(media['target_audience'])
                except:
                    media['target_audience'] = [media['target_audience']]
            elif not isinstance(media['target_audience'], list):
                media['target_audience'] = []
            
            # Set response time and success rate defaults
            if 'response_time_hours' not in media:
                media['response_time_hours'] = 24 if media.get('tier', 2) == 1 else 48
            
            if 'success_rate' not in media:
                media['success_rate'] = 0.85 if media.get('tier', 2) == 1 else 0.75
            
            # Ensure numeric fields are properly typed
            numeric_fields = ['tier', 'monthly_visits', 'cost_per_article', 'response_time_hours']
            for field in numeric_fields:
                if field in media and media[field] is not None:
                    try:
                        media[field] = int(media[field])
                    except (ValueError, TypeError):
                        # Set defaults for invalid numeric values
                        if field == 'tier':
                            media[field] = 2
                        elif field == 'monthly_visits':
                            media[field] = 1000000
                        elif field == 'cost_per_article':
                            media[field] = 1000000
                        elif field == 'response_time_hours':
                            media[field] = 24
            
            # Ensure float fields are properly typed
            float_fields = ['success_rate', 'male_audience', 'female_audience', 'access_from_vietnam']
            for field in float_fields:
                if field in media and media[field] is not None:
                    try:
                        media[field] = float(media[field])
                    except (ValueError, TypeError):
                        if field == 'success_rate':
                            media[field] = 0.8
                        else:
                            media[field] = None
            
        except Exception as e:
            logger.error(f"❌ Error standardizing media data for {media.get('name', 'Unknown')}: {e}")
            # Continue processing other media outlets
            continue

def validate_media_data_structure():
    """Validate the integrity of media data after standardization"""
    logger.info("🔍 Validating media data structure...")
    
    issues = []
    
    for i, media in enumerate(VIETNAMESE_MEDIA_DATA):
        try:
            # Required fields check
            required_fields = ['name', 'website', 'category', 'tier', 'top_categories', 'cost_per_article']
            for field in required_fields:
                if field not in media or not media[field]:
                    issues.append(f"Media {i+1} ({media.get('name', 'Unknown')}): Missing {field}")
            
            # Type validation
            if media.get('tier') not in [1, 2, 3]:
                issues.append(f"Media {i+1} ({media.get('name', 'Unknown')}): Invalid tier {media.get('tier')}")
            
            if not isinstance(media.get('cost_per_article', 0), (int, float)) or media.get('cost_per_article', 0) <= 0:
                issues.append(f"Media {i+1} ({media.get('name', 'Unknown')}): Invalid cost {media.get('cost_per_article')}")
            
            # List validation
            if not isinstance(media.get('topics', []), list):
                issues.append(f"Media {i+1} ({media.get('name', 'Unknown')}): topics should be list")
            
            if not isinstance(media.get('target_audience', []), list):
                issues.append(f"Media {i+1} ({media.get('name', 'Unknown')}): target_audience should be list")
                
        except Exception as e:
            issues.append(f"Media {i+1}: Validation error - {e}")
    
    if issues:
        logger.warning(f"⚠️ Found {len(issues)} data validation issues:")
        for issue in issues[:5]:  # Show first 5 issues
            logger.warning(f"   • {issue}")
        if len(issues) > 5:
            logger.warning(f"   • ... and {len(issues) - 5} more issues")
    else:
        logger.info(f"✅ All {len(VIETNAMESE_MEDIA_DATA)} media outlets validated successfully")
    
    return len(issues) == 0

# Update the standardization call
standardize_media_data()
validate_media_data_structure()

# =================== DATABASE OPERATIONS ===================

class MediaDatabase:
    """Enhanced production-grade database operations with async support"""
    
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
        """Setup ChromaDB collection with enhanced error handling"""
        if not chroma_client or not embedding_model:
            logger.warning("⚠️ Vector database not available - ChromaDB or embedding model missing")
            return
            
        try:
            # Try to get existing collection first
            try:
                self.vector_collection = chroma_client.get_collection(CHROMA_COLLECTION_NAME)
                logger.info(f"✅ Vector collection '{CHROMA_COLLECTION_NAME}' loaded")
                
                # Test the collection
                try:
                    count = self.vector_collection.count()
                    logger.info(f"📊 Collection has {count} documents")
                except Exception as count_error:
                    logger.warning(f"Could not get collection count: {count_error}")
                    
            except Exception as get_error:
                logger.info(f"Collection doesn't exist, creating new one: {get_error}")
                # Create new collection
                try:
                    self.vector_collection = chroma_client.create_collection(
                        name=CHROMA_COLLECTION_NAME,
                        metadata={"hnsw:space": "cosine"}
                    )
                    logger.info(f"✅ Vector collection '{CHROMA_COLLECTION_NAME}' created")
                except Exception as create_error:
                    logger.error(f"❌ Vector collection creation failed: {create_error}")
                    self.vector_collection = None
                    
        except Exception as e:
            logger.error(f"❌ Vector database setup failed: {e}")
            self.vector_collection = None
    
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
        """Initialize database with comprehensive Vietnamese media data"""
        try:
            async with self.get_db_session() as db:
                # Check if data already exists
                existing_count = db.query(MediaOutlet).count()
                if existing_count > 0:
                    logger.info(f"📊 Database already initialized with {existing_count} media outlets")
                    return True
                
                logger.info("🔄 Initializing comprehensive Vietnamese media database...")
                
                # Insert comprehensive media data
                for media_data in VIETNAMESE_MEDIA_DATA:
                    media_outlet = MediaOutlet(
                        name=media_data["name"],
                        website=media_data["website"],
                        category=media_data["category"],
                        tier=media_data["tier"],
                        total_visits_3months=media_data.get("total_visits_3months"),
                        monthly_visits=media_data.get("monthly_visits"),
                        visit_duration=media_data.get("visit_duration"),
                        access_from_vietnam=media_data.get("access_from_vietnam"),
                        male_audience=media_data.get("male_audience"),
                        female_audience=media_data.get("female_audience"),
                        southern_audience=media_data.get("southern_audience"),
                        northern_audience=media_data.get("northern_audience"),
                        central_audience=media_data.get("central_audience"),
                        age_18_24=media_data.get("age_18_24"),
                        age_25_34=media_data.get("age_25_34"),
                        age_35_44=media_data.get("age_35_44"),
                        age_45_54=media_data.get("age_45_54"),
                        age_55_64=media_data.get("age_55_64"),
                        age_65_plus=media_data.get("age_65_plus"),
                        top_categories=json.dumps(media_data["top_categories"]),
                        # Legacy fields for compatibility
                        publisher=media_data["publisher"],
                        circulation=media_data["circulation"],
                        publication_format=media_data["publication_format"],
                        language=media_data["language"],
                        cost_per_article=media_data["cost_per_article"],
                        topics=json.dumps(media_data["topics"]),
                        target_audience=json.dumps(media_data["target_audience"]),
                        response_time_hours=media_data["response_time_hours"],
                        success_rate=media_data["success_rate"]
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
                # Create enhanced searchable text
                top_categories = json.loads(media.top_categories) if media.top_categories else []
                topics = json.loads(media.topics) if media.topics else []
                audiences = json.loads(media.target_audience) if media.target_audience else []
                
                searchable_text = f"{media.name} {media.category} {' '.join(top_categories)} {' '.join(topics)} {' '.join(audiences)} {media.language}"
                
                # Generate embedding
                embedding = embedding_model.encode(searchable_text).tolist()
                
                embeddings.append(embedding)
                documents.append(searchable_text)
                metadatas.append({
                    "media_id": str(media.id),
                    "name": media.name,
                    "category": media.category,
                    "tier": media.tier,
                    "language": media.language,
                    "cost": media.cost_per_article,
                    "monthly_visits": media.monthly_visits or 0
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
        """Enhanced semantic search using vector embeddings"""
        if not self.vector_collection or not embedding_model:
            logger.warning("⚠️ Vector search not available, falling back to keyword search")
            return {"documents": [], "metadatas": [], "distances": []}
        
        try:
            # Generate query embedding
            query_embedding = embedding_model.encode(query).tolist()
            
            # Search in ChromaDB with enhanced error handling
            try:
                results = self.vector_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    include=["documents", "metadatas", "distances"]
                )
            except Exception as chroma_error:
                logger.error(f"ChromaDB query failed: {chroma_error}")
                # Try alternative query format
                try:
                    results = self.vector_collection.query(
                        query_texts=[query],  # Use text query instead
                        n_results=limit,
                        include=["documents", "metadatas", "distances"]
                    )
                except Exception as fallback_error:
                    logger.error(f"ChromaDB fallback query failed: {fallback_error}")
                    return {"documents": [], "metadatas": [], "distances": []}
            
            logger.debug(f"🔍 Vector search for '{query}' returned {len(results.get('documents', [[]])[0])} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Vector search failed: {e}")
            return {"documents": [], "metadatas": [], "distances": []}
    
    async def search_media_by_category(self, category: str, limit: int = 20) -> List[MediaOutletResponse]:
        """Search media outlets by category"""
        try:
            async with self.get_db_session() as db:
                media_outlets = db.query(MediaOutlet)\
                    .filter(MediaOutlet.category == category.upper())\
                    .filter(MediaOutlet.is_active == True)\
                    .order_by(MediaOutlet.monthly_visits.desc())\
                    .limit(limit)\
                    .all()
                
                result = []
                for media in media_outlets:
                    # Fix: Safe parsing of JSON fields with fallbacks
                    try:
                        top_categories = json.loads(media.top_categories) if media.top_categories else []
                    except (json.JSONDecodeError, TypeError):
                        top_categories = []
                    
                    try:
                        topics = json.loads(media.topics) if media.topics else []
                    except (json.JSONDecodeError, TypeError):
                        topics = []
                    
                    try:
                        target_audience = json.loads(media.target_audience) if media.target_audience else []
                    except (json.JSONDecodeError, TypeError):
                        target_audience = []
                    
                    result.append(MediaOutletResponse(
                        id=media.id,
                        name=media.name,
                        website=media.website,
                        category=media.category,
                        tier=media.tier,
                        monthly_visits=media.monthly_visits,
                        visit_duration=media.visit_duration,
                        access_from_vietnam=media.access_from_vietnam,
                        male_audience=media.male_audience,
                        female_audience=media.female_audience,
                        top_categories=top_categories,
                        cost_per_article=media.cost_per_article,
                        topics=topics,
                        target_audience=target_audience,
                        response_time_hours=media.response_time_hours,
                        success_rate=media.success_rate,
                        language=media.language or "Vietnamese",  # Fix: Safe language access
                        circulation=media.circulation,
                        publisher=media.publisher
                    ))
                
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to search by category: {e}")
            return []
    
    async def get_media_by_id(self, media_id: int) -> Optional[MediaOutlet]:
        """Get media outlet by ID"""
        try:
            async with self.get_db_session() as db:
                media = db.query(MediaOutlet).filter(MediaOutlet.id == media_id).first()
                return media
        except Exception as e:
            logger.error(f"❌ Failed to get media by ID {media_id}: {e}")
            return None
    
    async def get_top_media_by_traffic(self, limit: int = 20) -> List[MediaOutletResponse]:
        """Get top media outlets by traffic"""
        try:
            async with self.get_db_session() as db:
                media_outlets = db.query(MediaOutlet)\
                    .filter(MediaOutlet.is_active == True)\
                    .order_by(MediaOutlet.monthly_visits.desc())\
                    .limit(limit)\
                    .all()
                
                result = []
                for media in media_outlets:
                    # Fix: Safe parsing with error handling
                    try:
                        top_categories = json.loads(media.top_categories) if media.top_categories else []
                    except:
                        top_categories = []
                    
                    try:
                        topics = json.loads(media.topics) if media.topics else []
                    except:
                        topics = []
                    
                    try:
                        target_audience = json.loads(media.target_audience) if media.target_audience else []
                    except:
                        target_audience = []
                    
                    result.append(MediaOutletResponse(
                        id=media.id,
                        name=media.name,
                        website=media.website,
                        category=media.category,
                        tier=media.tier,
                        monthly_visits=media.monthly_visits,
                        visit_duration=media.visit_duration,
                        access_from_vietnam=media.access_from_vietnam,
                        male_audience=media.male_audience,
                        female_audience=media.female_audience,
                        top_categories=top_categories,
                        cost_per_article=media.cost_per_article,
                        topics=topics,
                        target_audience=target_audience,
                        response_time_hours=media.response_time_hours,
                        success_rate=media.success_rate,
                        language=media.language or "Vietnamese",
                        circulation=media.circulation,
                        publisher=media.publisher
                    ))
                
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to get top media: {e}")
            return []
    
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
        """Get all active media outlets with enhanced data"""
        try:
            async with self.get_db_session() as db:
                media_outlets = db.query(MediaOutlet)\
                    .filter(MediaOutlet.is_active == True)\
                    .order_by(MediaOutlet.monthly_visits.desc())\
                    .all()
                
                result = []
                for media in media_outlets:
                    # Fix: Comprehensive safe parsing
                    try:
                        top_categories = json.loads(media.top_categories) if media.top_categories else []
                        if not isinstance(top_categories, list):
                            top_categories = []
                    except:
                        top_categories = []
                    
                    try:
                        topics = json.loads(media.topics) if media.topics else []
                        if not isinstance(topics, list):
                            topics = []
                    except:
                        topics = []
                    
                    try:
                        target_audience = json.loads(media.target_audience) if media.target_audience else []
                        if not isinstance(target_audience, list):
                            target_audience = []
                    except:
                        target_audience = []
                    
                    result.append(MediaOutletResponse(
                        id=media.id,
                        name=media.name,
                        website=media.website,
                        category=media.category,
                        tier=media.tier,
                        monthly_visits=media.monthly_visits or 0,
                        visit_duration=media.visit_duration,
                        access_from_vietnam=media.access_from_vietnam,
                        male_audience=media.male_audience,
                        female_audience=media.female_audience,
                        top_categories=top_categories,
                        cost_per_article=media.cost_per_article or 1000000,
                        topics=topics,
                        target_audience=target_audience,
                        response_time_hours=media.response_time_hours or 24,
                        success_rate=media.success_rate or 0.8,
                        language=media.language or "Vietnamese",
                        circulation=media.circulation,
                        publisher=media.publisher
                    ))
                
                return result
                
        except Exception as e:
            logger.error(f"❌ Failed to get media outlets: {e}")
            return []
    
    async def get_media_statistics(self) -> Dict[str, Any]:
        """Get comprehensive media database statistics"""
        try:
            async with self.get_db_session() as db:
                from sqlalchemy import func
                
                total_outlets = db.query(MediaOutlet).filter(MediaOutlet.is_active == True).count()
                
                # Category breakdown
                categories = db.query(MediaOutlet.category, func.count(MediaOutlet.id))\
                    .filter(MediaOutlet.is_active == True)\
                    .group_by(MediaOutlet.category)\
                    .all()
                
                # Tier breakdown
                tiers = db.query(MediaOutlet.tier, func.count(MediaOutlet.id))\
                    .filter(MediaOutlet.is_active == True)\
                    .group_by(MediaOutlet.tier)\
                    .all()
                
                # Top traffic outlets
                top_traffic = db.query(MediaOutlet.name, MediaOutlet.monthly_visits)\
                    .filter(MediaOutlet.is_active == True)\
                    .filter(MediaOutlet.monthly_visits.isnot(None))\
                    .order_by(MediaOutlet.monthly_visits.desc())\
                    .limit(10)\
                    .all()
                
                # Average cost by tier
                avg_costs = db.query(MediaOutlet.tier, func.avg(MediaOutlet.cost_per_article))\
                    .filter(MediaOutlet.is_active == True)\
                    .group_by(MediaOutlet.tier)\
                    .all()
                
                return {
                    "total_outlets": total_outlets,
                    "categories": {cat: count for cat, count in categories},
                    "tiers": {tier: count for tier, count in tiers},
                    "top_traffic": [{"name": name, "monthly_visits": visits} for name, visits in top_traffic],
                    "average_costs_by_tier": {tier: float(avg_cost) for tier, avg_cost in avg_costs},
                    "total_monthly_visits": sum([visits for _, visits in top_traffic if visits])
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get media statistics: {e}")
            return {
                "total_outlets": 0,
                "categories": {},
                "tiers": {},
                "top_traffic": [],
                "average_costs_by_tier": {},
                "total_monthly_visits": 0
            }
    
    async def search_media_advanced(
        self, 
        query: str = None,
        category: str = None,
        tier: int = None,
        min_visits: int = None,
        max_cost: float = None,
        language: str = None,
        limit: int = 20
    ) -> List[MediaOutletResponse]:
        """Advanced media search with multiple filters"""
        try:
            async with self.get_db_session() as db:
                from sqlalchemy import or_
                
                # Start with base query
                query_obj = db.query(MediaOutlet).filter(MediaOutlet.is_active == True)
                
                # Apply filters
                if category:
                    query_obj = query_obj.filter(MediaOutlet.category == category.upper())
                
                if tier:
                    query_obj = query_obj.filter(MediaOutlet.tier == tier)
                
                if min_visits:
                    query_obj = query_obj.filter(MediaOutlet.monthly_visits >= min_visits)
                
                if max_cost:
                    query_obj = query_obj.filter(MediaOutlet.cost_per_article <= max_cost)
                
                if language:
                    query_obj = query_obj.filter(MediaOutlet.language == language)
                
                # Text search if query provided
                if query:
                    query_obj = query_obj.filter(
                        or_(
                            MediaOutlet.name.contains(query),
                            MediaOutlet.topics.contains(query),
                            MediaOutlet.target_audience.contains(query)
                        )
                    )
                
                # Order by monthly visits and limit
                media_outlets = query_obj.order_by(MediaOutlet.monthly_visits.desc()).limit(limit).all()
                
                result = []
                for media in media_outlets:
                    # Fix: Safe JSON parsing for all fields
                    try:
                        top_categories = json.loads(media.top_categories) if media.top_categories else []
                    except:
                        top_categories = []
                    
                    try:
                        topics = json.loads(media.topics) if media.topics else []
                    except:
                        topics = []
                    
                    try:
                        target_audience = json.loads(media.target_audience) if media.target_audience else []
                    except:
                        target_audience = []
                    
                    result.append(MediaOutletResponse(
                        id=media.id,
                        name=media.name,
                        website=media.website,
                        category=media.category,
                        tier=media.tier,
                        monthly_visits=media.monthly_visits,
                        visit_duration=media.visit_duration,
                        access_from_vietnam=media.access_from_vietnam,
                        male_audience=media.male_audience,
                        female_audience=media.female_audience,
                        top_categories=top_categories,
                        cost_per_article=media.cost_per_article,
                        topics=topics,
                        target_audience=target_audience,
                        response_time_hours=media.response_time_hours,
                        success_rate=media.success_rate,
                        language=media.language or "Vietnamese",
                        circulation=media.circulation,
                        publisher=media.publisher
                    ))
                
                return result
                
        except Exception as e:
            logger.error(f"❌ Advanced search failed: {e}")
            return []

# =================== GLOBAL INSTANCE ===================

# Global database instance
media_db = MediaDatabase()

async def init_database():
    """Initialize database on startup"""
    try:
        logger.info("🚀 Initializing Enhanced Instant Media Release Database...")
        
        success = await media_db.initialize_media_data()
        if success:
            # Get statistics
            stats = await media_db.get_media_statistics()
            logger.info(f"✅ Database initialization completed successfully!")
            logger.info(f"📊 Database Statistics:")
            logger.info(f"   • Total outlets: {stats.get('total_outlets', 0)}")
            logger.info(f"   • Categories: {', '.join(stats.get('categories', {}).keys())}")
            logger.info(f"   • Tier distribution: {stats.get('tiers', {})}")
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

async def get_media_categories() -> List[str]:
    """Get all available media categories"""
    try:
        async with media_db.get_db_session() as db:
            categories = db.query(MediaOutlet.category.distinct())\
                .filter(MediaOutlet.is_active == True)\
                .all()
            return [cat[0] for cat in categories]
    except Exception as e:
        logger.error(f"❌ Failed to get categories: {e}")
        return []

async def get_recommended_media_for_budget(budget: float, limit: int = 10) -> List[MediaOutletResponse]:
    """Get media recommendations within budget"""
    try:
        # Simple budget-based recommendation
        max_cost_per_article = budget * 0.3  # 30% of budget for single article
        
        return await media_db.search_media_advanced(
            max_cost=max_cost_per_article,
            limit=limit
        )
    except Exception as e:
        logger.error(f"❌ Budget-based recommendation failed: {e}")
        return []

def format_duration(duration_str: str) -> str:
    """Format duration string for display"""
    if not duration_str:
        return "N/A"
    
    try:
        # Handle various duration formats
        if ":" in duration_str:
            parts = duration_str.split(":")
            if len(parts) == 2:
                return f"{parts[0]}m {parts[1]}s"
            elif len(parts) == 3:
                hours, minutes, seconds = parts
                if int(hours) > 0:
                    return f"{hours}h {minutes}m {seconds}s"
                else:
                    return f"{minutes}m {seconds}s"
        return duration_str
    except:
        return duration_str

def calculate_audience_fit_score(media: MediaOutletResponse, target_demographics: Dict) -> float:
    """Calculate how well media outlet fits target demographics"""
    score = 0.0
    factors = 0
    
    # Gender match
    if target_demographics.get("gender_preference"):
        pref = target_demographics["gender_preference"]
        if pref == "male" and media.male_audience and media.male_audience > 60:
            score += 0.3
        elif pref == "female" and media.female_audience and media.female_audience > 60:
            score += 0.3
        elif pref == "balanced":
            if media.male_audience and media.female_audience:
                balance = abs(media.male_audience - media.female_audience)
                score += 0.3 * (1 - balance / 50)  # Closer to 50/50 = higher score
        factors += 1
    
    # Category match
    if target_demographics.get("interests"):
        target_interests = set(target_demographics["interests"])
        media_categories = set(media.top_categories)
        overlap = len(target_interests.intersection(media_categories))
        if overlap > 0:
            score += 0.4 * (overlap / len(target_interests))
        factors += 1
    
    # Traffic/reach consideration
    if media.monthly_visits:
        # Normalize traffic (higher traffic = higher score, but with diminishing returns)
        traffic_score = min(1.0, media.monthly_visits / 50000000)  # 50M visits = max score
        score += 0.3 * traffic_score
        factors += 1
    
    return score / max(factors, 1)

# =================== TESTING FUNCTIONS ===================

async def test_database():
    """Comprehensive test of the enhanced database functionality"""
    logger.info("🧪 Testing Enhanced Database Functionality...")
    
    try:
        # Test initialization
        success = await init_database()
        assert success, "Database initialization failed"
        
        # Test statistics
        stats = await media_db.get_media_statistics()
        logger.info(f"📊 Database contains {stats.get('total_outlets', 0)} outlets")
        assert stats.get('total_outlets', 0) >= 100, "Expected at least 100 outlets"
        
        # Test vector search
        results = await media_db.search_media_by_vector("technology startup business fintech")
        logger.info(f"🔍 Vector search returned {len(results.get('documents', [[]])[0])} results")
        
        # Test category search
        business_media = await media_db.search_media_by_category("BUSINESS", limit=10)
        logger.info(f"💼 Found {len(business_media)} business media outlets")
        
        # Test advanced search
        premium_media = await media_db.search_media_advanced(
            tier=1,
            min_visits=1000000,
            max_cost=10000000,
            limit=5
        )
        logger.info(f"⭐ Found {len(premium_media)} premium media outlets")
        
        # Test top traffic
        top_media = await media_db.get_top_media_by_traffic(limit=5)
        logger.info(f"🚀 Top 5 media by traffic:")
        for media in top_media[:5]:
            visits = media.monthly_visits or 0
            logger.info(f"   • {media.name}: {visits:,} monthly visits")
        
        # Test categories
        categories = await get_media_categories()
        logger.info(f"📂 Available categories: {', '.join(categories)}")
        
        logger.info("✅ Enhanced database tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

# =================== DATA VALIDATION ===================

def validate_media_data():
    """Validate the integrity of media data"""
    logger.info("🔍 Validating media data integrity...")
    
    issues = []
    
    for i, media in enumerate(VIETNAMESE_MEDIA_DATA):
        # Required fields check
        required_fields = ['name', 'website', 'category', 'tier', 'top_categories', 'cost_per_article']
        for field in required_fields:
            if field not in media or not media[field]:
                issues.append(f"Media {i+1} ({media.get('name', 'Unknown')}): Missing {field}")
        
        # Tier validation
        if media.get('tier') not in [1, 2, 3]:
            issues.append(f"Media {i+1} ({media.get('name', 'Unknown')}): Invalid tier {media.get('tier')}")
        
        # Cost validation
        if media.get('cost_per_article', 0) <= 0:
            issues.append(f"Media {i+1} ({media.get('name', 'Unknown')}): Invalid cost {media.get('cost_per_article')}")
        
        # URL validation
        if not media.get('website', '').startswith('http'):
            issues.append(f"Media {i+1} ({media.get('name', 'Unknown')}): Invalid website URL")
    
    if issues:
        logger.warning(f"⚠️ Found {len(issues)} data validation issues:")
        for issue in issues[:10]:  # Show first 10 issues
            logger.warning(f"   • {issue}")
        if len(issues) > 10:
            logger.warning(f"   • ... and {len(issues) - 10} more issues")
    else:
        logger.info(f"✅ All {len(VIETNAMESE_MEDIA_DATA)} media outlets validated successfully")
    
    return len(issues) == 0

# =================== EXPORT FUNCTIONALITY ===================

async def export_media_data_to_json(filepath: str = "media_data_export.json"):
    """Export media data to JSON file"""
    try:
        media_outlets = await media_db.get_all_media_outlets()
        
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_outlets": len(media_outlets),
            "data": [outlet.model_dump() for outlet in media_outlets]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Exported {len(media_outlets)} media outlets to {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Export failed: {e}")
        return False

# Run validation on import
if __name__ == "__main__":
    validate_media_data()
    # Uncomment to run full tests
    # import asyncio
    # asyncio.run(test_database())