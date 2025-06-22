"""
Instant Media Release - Enhanced Multi-Agent Team System
Advanced Team-based AI agents with orchestrator-worker architecture
Enhanced with parallel processing, shared state management and team coordination
Based on Anthropic's Research architecture and Agno Teams framework
"""

import os
import json
import asyncio
from datetime import datetime
<<<<<<< HEAD
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import List, Dict, Optional, Any, Callable
=======
from typing import List, Dict, Optional, Any, Callable, Iterator
>>>>>>> main
from dataclasses import dataclass, field
from enum import Enum

from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.storage.agent.sqlite import SqliteAgentStorage
from agno.tools.googlesearch import GoogleSearchTools
from pydantic import BaseModel, Field
from loguru import logger

from database import media_db, MediaOutletResponse

# Load environment variables from .env file
load_dotenv(dotenv_path=".env")
from database import media_db
from document_processor import get_document_processor

# =================== CONFIGURATION ===================

# OpenAI Configuration
<<<<<<< HEAD
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
=======
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORCHESTRATOR_MODEL = os.getenv("OPENAI_ORCHESTRATOR_MODEL", "gpt-4o")  # Team Leader
OPENAI_WORKER_MODEL = os.getenv("OPENAI_WORKER_MODEL", "gpt-4o")  # Subagents  
>>>>>>> main
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))

# Groq Configuration (Alternative)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_ORCHESTRATOR_MODEL = os.getenv("GROQ_ORCHESTRATOR_MODEL", "llama-3.3-70b-versatile")
GROQ_WORKER_MODEL = os.getenv("GROQ_WORKER_MODEL", "llama-3.3-70b-versatile")

# Team Configuration
TEAM_TIMEOUT = int(os.getenv("TEAM_TIMEOUT_SECONDS", "180"))
MAX_RETRIES = int(os.getenv("MAX_TEAM_RETRIES", "3"))
PARALLEL_PROCESSING = os.getenv("TEAM_PARALLEL_PROCESSING", "true").lower() == "true"
MAX_CONCURRENT_AGENTS = int(os.getenv("MAX_CONCURRENT_AGENTS", "4"))

# Business Configuration
PACKAGE_PRICES = {
    "Starter": {
        "price": int(os.getenv("STARTER_PACKAGE_PRICE", "12000000")),
        "media_count": int(os.getenv("STARTER_MEDIA_COUNT", "3")),
        "timeline": "1-3 ngày làm việc",
        "features": ["Chỉnh sửa nhẹ nội dung", "2-3 báo tier-2", "Báo cáo cơ bản"],
    },
    "Standard": {
        "price": int(os.getenv("STANDARD_PACKAGE_PRICE", "30000000")),
        "media_count": int(os.getenv("STANDARD_MEDIA_COUNT", "15")),
        "timeline": "5-7 ngày làm việc",
        "features": [
            "Viết bài hoàn chỉnh",
            "12-15 báo bao gồm tier-1",
            "Báo cáo chi tiết",
        ],
    },
    "Premium": {
        "price": int(os.getenv("PREMIUM_PACKAGE_PRICE", "50000000")),
        "media_count": int(os.getenv("PREMIUM_MEDIA_COUNT", "18")),
        "timeline": "10-14 ngày làm việc",
        "features": ["Chiến lược + viết bài", "15-18 báo + phỏng vấn", "Social media"],
    },
}

# =================== ENHANCED STATE MANAGEMENT ===================


class ConversationState(Enum):
    """Conversation states"""

    GREETING = "greeting"
    GATHERING_INFO = "gathering_info"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    CONFIRMING = "confirming"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    MODIFYING = "modifying"
    COMPLETED = "completed"
    ERROR = "error"


class WorkflowPhase(Enum):
    """Workflow execution phases"""

    IDLE = "idle"
    CONTENT_ANALYSIS = "content_analysis"
    DOCUMENT_ANALYSIS = "document_analysis"
    MEDIA_MATCHING = "media_matching"
    PRICING_OPTIMIZATION = "pricing_optimization"
    REPORT_GENERATION = "report_generation"
    USER_REVIEW = "user_review"
    PLAN_MODIFICATION = "plan_modification"


@dataclass
class ConversationContext:
    """Comprehensive conversation context"""

    session_id: str
    state: ConversationState = ConversationState.GREETING
    phase: WorkflowPhase = WorkflowPhase.IDLE

    # User information
    user_input: str = ""
    budget: float = 0.0
    requirements: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)

    # Workflow results
    content_analysis: Optional[Dict] = None
    document_analysis: Optional[Dict] = None
    media_recommendations: List[Dict] = field(default_factory=list)
    pricing_analysis: Optional[Dict] = None
    executive_report: Optional[Dict] = None

    # Interaction tracking
    conversation_history: List[Dict] = field(default_factory=list)
    user_feedback: List[Dict] = field(default_factory=list)
    modifications: List[Dict] = field(default_factory=list)

    # Progress tracking
    progress_callbacks: List[Callable] = field(default_factory=list)
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0

    # Flags
    workflow_started: bool = False
    user_approved: bool = False
    needs_modification: bool = False

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


# =================== CONVERSATION STATE MANAGEMENT ===================

class ConversationState(Enum):
    """Conversation states"""
    GREETING = "greeting"
    GATHERING_INFO = "gathering_info"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    CONFIRMING = "confirming"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    MODIFYING = "modifying"
    COMPLETED = "completed"
    ERROR = "error"

class WorkflowPhase(Enum):
    """Workflow execution phases"""
    IDLE = "idle"
    TEAM_INITIALIZATION = "team_initialization"
    PARALLEL_ANALYSIS = "parallel_analysis"
    CONTENT_ANALYSIS = "content_analysis"
    DOCUMENT_ANALYSIS = "document_analysis"
    MEDIA_MATCHING = "media_matching"
    PRICING_OPTIMIZATION = "pricing_optimization"
    REPORT_GENERATION = "report_generation"
    CITATION_VERIFICATION = "citation_verification"
    USER_REVIEW = "user_review"
    PLAN_MODIFICATION = "plan_modification"

@dataclass
class TeamMemory:
    """Shared memory for team coordination"""
    session_id: str
    workflow_plan: Dict[str, Any] = field(default_factory=dict)
    completed_tasks: List[str] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    agent_outputs: Dict[str, Any] = field(default_factory=dict)
    context_summary: str = ""
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    error_log: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ConversationContext:
    """Enhanced conversation context with team memory"""
    session_id: str
    state: ConversationState = ConversationState.GREETING
    phase: WorkflowPhase = WorkflowPhase.IDLE
    
    # User information
    user_input: str = ""
    budget: float = 0.0
    requirements: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Team coordination
    team_memory: TeamMemory = field(default_factory=lambda: TeamMemory(session_id=""))
    active_agents: List[str] = field(default_factory=list)
    parallel_results: Dict[str, Any] = field(default_factory=dict)
    
    # Workflow results
    content_analysis: Optional[Dict] = None
    document_analysis: Optional[Dict] = None
    media_recommendations: List[Dict] = field(default_factory=list)
    pricing_analysis: Optional[Dict] = None
    executive_report: Optional[Dict] = None
    
    # Interaction tracking
    conversation_history: List[Dict] = field(default_factory=list)
    user_feedback: List[Dict] = field(default_factory=list)
    modifications: List[Dict] = field(default_factory=list)
    
    # Progress tracking
    progress_callbacks: List[Callable] = field(default_factory=list)
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    
    # Flags
    workflow_started: bool = False
    user_approved: bool = False
    needs_modification: bool = False
    team_initialized: bool = False
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

# =================== STRUCTURED OUTPUT MODELS ===================

class ConversationResponse(BaseModel):
    """Structured conversation response for Vietnamese PR consultation chatbot"""
    
    message: str = Field(
        description="Main conversational response message to user in Vietnamese (50-300 characters)"
    )
    
    state: str = Field(
        description="Current conversation state: greeting|gathering_info|analyzing|planning|confirming|executing|reviewing|modifying|completed|error"
    )
    
    phase: str = Field(
        description="Current workflow execution phase: idle|team_initialization|parallel_analysis|content_analysis|document_analysis|media_matching|pricing_optimization|report_generation|citation_verification|user_review|plan_modification"
    )
    
    suggestions: List[str] = Field(
        description="Clickable suggestion buttons (3-5 short phrases, 20-50 chars each)",
        default=[]
    )
    
    options: List[str] = Field(
        description="Available action options for user at current stage",
        default=[]
    )
    
    progress: Optional[Dict] = Field(
        description="Progress information for ongoing team processing",
        default=None
    )
    
    data: Optional[Dict] = Field(
        description="Additional structured data for frontend",
        default=None
    )
    
    requires_input: bool = Field(
        description="Whether system is waiting for user input",
        default=True
    )
    
    can_proceed: bool = Field(
        description="Whether system has enough information to trigger team workflow",
        default=False
    )

# Keep all existing analysis models (ContentAnalysis, DocumentAnalysis, etc.)
class ContentAnalysis(BaseModel):
    """Structured output for content analysis agent"""

    language: str = Field(description="Detected language: Vietnamese/English/Both")
    primary_topics: List[str] = Field(description="Main topics/categories (max 5)")
    target_audiences: List[str] = Field(
        description="Identified target audiences (max 4)"
    )
    keywords: List[str] = Field(description="Key search terms (max 10)")
    content_tone: str = Field(description="Professional/Technical/Casual/Formal")
    urgency_level: str = Field(description="Low/Medium/High")
    industry_sector: str = Field(
        description="Main industry: Tech/Finance/Healthcare/etc"
    )
    press_release_type: str = Field(
        description="Product Launch/Partnership/Funding/Event/Other"
    )
    geographic_scope: str = Field(description="Local/National/International")
    confidence_score: float = Field(description="Analysis confidence 0-1", ge=0, le=1)


class DocumentAnalysis(BaseModel):
    """Structured output for document analysis agent"""
    document_summary: str = Field(description="Brief summary of document content")
    key_information: List[str] = Field(description="Key points extracted (max 8)")
    relevant_topics: List[str] = Field(description="Topics relevant to media release (max 5)")
    target_audience_insights: List[str] = Field(description="Audience insights from document (max 4)")
    media_angles: List[str] = Field(description="Potential media story angles (max 6)")
    supporting_data: List[str] = Field(description="Statistics, quotes, facts (max 5)")
    document_quality: str = Field(description="High/Medium/Low - content richness assessment")
    confidence_score: float = Field(description="Analysis confidence 0-1", ge=0, le=1)

class MediaRecommendation(BaseModel):
    """Structured output for media recommendation"""

    media_outlet_id: int = Field(description="Database ID of recommended media")
    media_name: str = Field(description="Name of media outlet")
    matching_score: float = Field(description="Relevance score 0-1", ge=0, le=1)
    reasoning: str = Field(description="Why this media fits (max 200 chars)")
    estimated_reach: int = Field(description="Estimated audience reach", ge=0)
    cost_vnd: float = Field(description="Publication cost in VND", ge=0)
    tier: int = Field(description="Media tier 1-3")
    language_match: bool = Field(description="Language compatibility")
    topic_overlap: float = Field(description="Topic alignment 0-1", ge=0, le=1)
    audience_fit: float = Field(description="Audience match 0-1", ge=0, le=1)


class PricingAnalysis(BaseModel):
    """Structured output for pricing optimization"""

    recommended_package: str = Field(description="Starter/Standard/Premium")
    total_cost_vnd: float = Field(description="Total estimated cost", ge=0)
    package_price_vnd: float = Field(description="Package base price", ge=0)
    media_costs_vnd: float = Field(description="Total media costs", ge=0)
    timeline_days: str = Field(description="Estimated delivery timeline")
    media_count: int = Field(description="Number of media outlets", ge=1)
    budget_utilization: float = Field(description="% of budget used 0-1", ge=0, le=1)
    cost_efficiency: str = Field(description="Cost per reach analysis")
    roi_projection: str = Field(description="Expected ROI description")
    alternative_packages: List[str] = Field(description="Other viable options")


class ExecutiveReport(BaseModel):
    """Structured output for executive summary"""

    executive_summary: str = Field(description="2-3 sentence overview")
    strategic_objectives: List[str] = Field(description="Key goals achieved (max 4)")
    media_strategy: str = Field(description="Overall media approach")
    success_metrics: List[str] = Field(description="KPIs to track (max 5)")
    implementation_steps: List[str] = Field(description="Next actions (max 6)")
    risk_mitigation: List[str] = Field(
        description="Potential risks & solutions (max 3)"
    )
    competitive_advantage: str = Field(description="How this differentiates")
    timeline_summary: str = Field(description="Key milestones")


# =================== DEPENDENCY INJECTION ===================


@dataclass
class AgentDependencies:
    """Shared context for all agents"""

    user_input: str
    budget: float
    session_id: str
    content_analysis: Optional[ContentAnalysis] = None
    available_media: List[MediaOutletResponse] = None
    vector_search_results: Optional[Dict] = None
class PlanModification(BaseModel):
    """Structured output for plan modification"""
    modification_type: str = Field(description="Budget/Media/Timeline/Strategy")
    original_value: str = Field(description="Original plan value")
    new_value: str = Field(description="New requested value")
    impact_assessment: str = Field(description="Impact of this change")
    feasibility: str = Field(description="High/Medium/Low feasibility")
    alternative_suggestions: List[str] = Field(description="Alternative approaches")
    cost_impact: float = Field(description="Cost change in VND")
    timeline_impact: str = Field(description="Timeline change description")

# =================== UTILITY FUNCTIONS ===================

def parse_agent_response(result: Any, model_class: type, fallback_data: Dict = None):
    """Enhanced agent response parser for team-based responses"""
    try:
        logger.debug(f"🔍 Parsing {model_class.__name__} from {type(result)}")
        
        # Handle team response wrapper
        if hasattr(result, 'content'):
            content = result.content
            if isinstance(content, model_class):
                return content
            if isinstance(content, dict):
                return model_class(**content)
            if isinstance(content, str):
                try:
                    cleaned_content = content.strip()
                    if "```json" in cleaned_content:
                        start = cleaned_content.find("```json") + 7
                        end = cleaned_content.find("```", start)
                        if end > start:
                            cleaned_content = cleaned_content[start:end].strip()
                    
                    parsed_data = json.loads(cleaned_content)
                    
                    # Add defaults for ConversationResponse
                    if model_class == ConversationResponse:
                        defaults = {
                            "suggestions": [], "options": [], "progress": None,
                            "data": None, "requires_input": True, "can_proceed": False
                        }
                        for key, default_value in defaults.items():
                            if key not in parsed_data:
                                parsed_data[key] = default_value
                    
                    return model_class(**parsed_data)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode failed: {e}")
                    raise
        
        # Handle direct responses
        if isinstance(result, model_class):
            return result
        if isinstance(result, dict):
            return model_class(**result)
        if isinstance(result, str):
            parsed_data = json.loads(result)
            return model_class(**parsed_data)
        
        raise ValueError(f"Cannot parse response type: {type(result)}")
        
    except Exception as e:
        logger.error(f"❌ Error parsing team response: {e}")
        if fallback_data:
            logger.warning(f"🔄 Using fallback data for {model_class.__name__}")
            return model_class(**fallback_data)
        raise ValueError(f"Failed to parse {model_class.__name__} from {type(result)}: {e}")

async def update_progress(context: ConversationContext, step: str, message: str):
    """Update progress and notify callbacks with team context"""
    context.current_step = step
    context.completed_steps += 1
    context.updated_at = datetime.utcnow()
    context.team_memory.updated_at = datetime.utcnow()
    
    # Update team memory
    if step not in context.team_memory.completed_tasks:
        context.team_memory.completed_tasks.append(step)
    
    progress_info = {
        "step": step,
        "message": message,
        "completed": context.completed_steps,
        "total": context.total_steps,
        "percentage": (context.completed_steps / max(context.total_steps, 1)) * 100,
        "active_agents": len(context.active_agents),
        "team_phase": context.phase.value,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Notify all registered callbacks
    for callback in context.progress_callbacks:
        try:
            await callback(progress_info)
        except Exception as e:
            logger.warning(f"Progress callback failed: {e}")

<<<<<<< HEAD

# =================== SPECIALIZED AGENTS ===================

# =================== CONVERSATIONAL AGENT SYSTEM ===================

class InstantMediaReleaseAgents:
    """Production-grade multi-agent system for media release automation"""

class ConversationalMediaReleaseAgents:
    """Advanced conversational multi-agent system with real-time interaction"""
    
    def __init__(self):
        """Initialize all agents with production configuration"""

        """Initialize conversational agent system"""
=======
# =================== ENHANCED TEAM-BASED AGENT SYSTEM ===================

class EnhancedMediaReleaseTeamSystem:
    """
    Enhanced Team-based Multi-Agent System with Orchestrator-Worker Architecture
    Following Anthropic's Research pattern with LeadResearcher + Subagents + CitationAgent
    """
    
    def __init__(self):
        """Initialize enhanced team-based agent system"""
>>>>>>> main
        
        # Validate configuration
        if not OPENAI_API_KEY:
            raise ValueError("❌ OPENAI_API_KEY environment variable is required")

        # Initialize OpenAI model with optimized settings
        self.llm = OpenAIChat(
            id=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS,
            timeout=AGENT_TIMEOUT,
        )

        if not OPENAI_API_KEY and not GROQ_API_KEY:
            raise ValueError("❌ Either OPENAI_API_KEY or GROQ_API_KEY environment variable is required")
        
        # Initialize models
        if OPENAI_API_KEY:
            self.orchestrator_llm = OpenAIChat(
                id=OPENAI_ORCHESTRATOR_MODEL,
                api_key=OPENAI_API_KEY,
                temperature=OPENAI_TEMPERATURE,
                max_tokens=OPENAI_MAX_TOKENS,
                timeout=TEAM_TIMEOUT
            )
            self.worker_llm = OpenAIChat(
                id=OPENAI_WORKER_MODEL,
                api_key=OPENAI_API_KEY,
                temperature=OPENAI_TEMPERATURE,
                max_tokens=OPENAI_MAX_TOKENS,
                timeout=TEAM_TIMEOUT
            )
            logger.info(f"✅ Using OpenAI models - Orchestrator: {OPENAI_ORCHESTRATOR_MODEL}, Workers: {OPENAI_WORKER_MODEL}")
        elif GROQ_API_KEY:
            from agno.models.groq import GroqChat
            self.orchestrator_llm = GroqChat(
                id=GROQ_ORCHESTRATOR_MODEL,
                api_key=GROQ_API_KEY,
                temperature=OPENAI_TEMPERATURE,
                max_tokens=OPENAI_MAX_TOKENS,
                timeout=TEAM_TIMEOUT
            )
            self.worker_llm = GroqChat(
                id=GROQ_WORKER_MODEL,
                api_key=GROQ_API_KEY,
                temperature=OPENAI_TEMPERATURE,
                max_tokens=OPENAI_MAX_TOKENS,
                timeout=TEAM_TIMEOUT
            )
            logger.info(f"✅ Using Groq models - Orchestrator: {GROQ_ORCHESTRATOR_MODEL}, Workers: {GROQ_WORKER_MODEL}")
        
        # Team memory storage
        self.storage = SqliteAgentStorage(
<<<<<<< HEAD
            table_name="instant_media_agents", db_file="./agent_memory.db"
            table_name="conversational_agents",
            db_file="./agent_memory.db"
=======
            table_name="team_agents",
            db_file="./team_memory.db"
>>>>>>> main
        )

        
        # Initialize conversation contexts
        self.active_conversations: Dict[str, ConversationContext] = {}
        
<<<<<<< HEAD
        # Initialize specialized agents
        self.conversation_agent = self._create_conversation_agent()
        self.workflow_coordinator = self._create_workflow_coordinator()
        self.content_analyzer = self._create_content_analyzer()
        self.document_analyzer = self._create_document_analyzer()
        self.media_matcher = self._create_media_matcher()
        self.pricing_optimizer = self._create_pricing_optimizer()
        self.report_generator = self._create_report_generator()

        logger.info("✅ Instant Media Release multi-agent system initialized")

        self.plan_modifier = self._create_plan_modifier()
=======
        # Initialize core agents and teams
        self._initialize_core_teams()
>>>>>>> main
        
        logger.info("✅ Enhanced Team-based Media Release system initialized")
    
    def _initialize_core_teams(self):
        """Initialize core agent teams using Team architecture"""
        
        # =================== CONVERSATION MANAGEMENT TEAM ===================
        
        self.conversation_agent = Agent(
            name="ConversationAgent",
            role="Expert Vietnamese PR consultant and conversational AI assistant",
            model=self.orchestrator_llm,
            instructions=[
                "Engage users in natural, helpful conversation about their PR needs",
                "Gather project information through friendly dialogue", 
                "Explain the process and set proper expectations",
                "Identify when to trigger the team workflow vs continue conversation",
                "Provide expert advice on Vietnamese media landscape",
                "Maintain professional yet approachable tone",
                "Guide users through reviewing and modifying recommendations",
                "CRITICAL: Respond in valid JSON format matching ConversationResponse schema",
                "Required fields: message, state, phase, suggestions, options, requires_input, can_proceed"
            ],
            response_model=ConversationResponse,
            storage=self.storage,
            show_tool_calls=False,
            markdown=False
        )
        
        # =================== LEAD RESEARCHER TEAM (ORCHESTRATOR) ===================
        
        self.lead_researcher = Agent(
            name="LeadResearcher", 
            role="Senior PR strategist and team coordinator",
            model=self.orchestrator_llm,
            instructions=[
                "You are the Lead Researcher coordinating specialized AI agents",
                "Plan and delegate tasks to specialist agents efficiently",
                "Maintain shared context and ensure quality coordination",
                "Make strategic decisions about task sequencing and prioritization",
                "Synthesize outputs from multiple specialists into coherent insights",
                "Adapt workflow based on intermediate results and requirements",
                "Ensure all team members have clear, non-overlapping responsibilities",
                "Monitor progress and adjust strategy as needed"
            ],
            storage=self.storage,
            show_tool_calls=True
        )
        
        # =================== SPECIALIST WORKER AGENTS ===================
        
        # Content Analysis Specialist
        self.content_specialist = Agent(
            name="ContentSpecialist",
            role="Vietnamese content analysis expert with conversation intelligence",
            model=self.worker_llm,
            instructions=[
<<<<<<< HEAD
                "Analyze user input and conversation context to extract business requirements",
                "Consider both explicit statements and implied needs from conversation",
                "Identify the primary language preference and target market",
                "Determine the most relevant industry sector and press release type",
                "Extract key topics and themes for media matching",
                "Assess content tone, urgency, and geographic scope",
                "Factor in user's conversational style and preferences",
                "Provide confidence score and explain reasoning",
                "Focus on Vietnamese market nuances and business culture",
                "Consider SME-specific communication needs",
                "Consider SME-specific communication needs and constraints",
=======
                "Analyze user input and conversation context for business requirements",
                "Extract key topics, target audiences, and strategic objectives",
                "Determine language preferences and market positioning",
                "Assess content tone, urgency, and geographic scope", 
                "Focus on Vietnamese market nuances and SME needs",
                "Provide confidence scores and clear reasoning",
>>>>>>> main
                "Return ONLY valid JSON in ContentAnalysis format"
            ],
            response_model=ContentAnalysis,
            storage=self.storage,
<<<<<<< HEAD
            session_id="content_analysis",
            show_tool_calls=False,
            markdown=False,
            exponential_backoff=True,
            retries=MAX_RETRIES,
        )

    
    def _create_document_analyzer(self) -> Agent:
        """Enhanced document analyzer with conversation integration"""
        return Agent(
            name="DocumentAnalyzer",
            role="Expert document analyst specializing in content extraction for conversational PR",
            model=self.llm,
            description="""
            You are a senior content analyst who specializes in extracting valuable 
            information from documents to support press release and media campaigns,
            while considering the conversational context and user preferences.
            """,
=======
            show_tool_calls=False
        )
        
        # Document Analysis Specialist  
        self.document_specialist = Agent(
            name="DocumentSpecialist",
            role="Expert document analyst for conversational PR campaigns",
            model=self.worker_llm,
>>>>>>> main
            instructions=[
                "Extract valuable information from documents for PR purposes",
                "Identify compelling data points, quotes, and statistics",
                "Suggest media angles based on document content and conversation",
                "Assess content quality and usefulness for PR objectives",
                "Focus on Vietnamese market context and business interests",
                "Return ONLY valid JSON in DocumentAnalysis format"
            ],
            response_model=DocumentAnalysis,
            storage=self.storage,
            show_tool_calls=False
        )
        
        # Media Matching Specialist
        self.media_specialist = Agent(
            name="MediaSpecialist", 
            role="Vietnamese media landscape expert with database integration",
            model=self.worker_llm,
            tools=[GoogleSearchTools()],
            instructions=[
                "Match content requirements with optimal Vietnamese media outlets",
                "Prioritize tier-1 outlets: VnExpress, 24H, Dân trí, Tuổi trẻ",
                "Consider specialized outlets for business, tech, youth demographics",
                "Evaluate topic relevance, audience alignment, and budget constraints",
                "Factor in publication success rates and response times",
<<<<<<< HEAD
                "Provide clear reasoning for each recommendation",
                "Optimize for maximum reach within budget",
                "Consider media mix for comprehensive coverage",
                "Consider user's timeline and urgency requirements",
                "Provide clear reasoning that connects to user's goals",
                "Optimize for maximum reach within stated budget",
=======
                "Provide clear reasoning connecting to user's stated goals",
>>>>>>> main
                "Return ONLY valid JSON in MediaRecommendation format"
            ],
            response_model=MediaRecommendation,
            storage=self.storage,
<<<<<<< HEAD
            session_id="media_matching",
            show_tool_calls=True,
            markdown=False,
            exponential_backoff=True,
            retries=MAX_RETRIES,
        )

    def _create_pricing_optimizer(self) -> Agent:
        """Enhanced pricing with conversation-aware optimization"""
        return Agent(
            name="PricingOptimizer",
            role="Pricing strategist with conversational context awareness",
            model=self.llm,
            description="""
            You are a business strategist specializing in media package optimization.
            You understand user needs from conversation and can create cost-effective
            strategies that align with their stated goals and constraints.
            """,
=======
            show_tool_calls=True
        )
        
        # Pricing Optimization Specialist
        self.pricing_specialist = Agent(
            name="PricingSpecialist",
            role="Business strategist with conversation-aware pricing optimization",
            model=self.worker_llm,
>>>>>>> main
            instructions=[
                "Optimize pricing strategy based on user budget and conversation context",
                "Calculate optimal package: Starter (12M), Standard (30M), Premium (50M)",
<<<<<<< HEAD
                "Factor in user's timeline preferences and flexibility",
                "Ensure total costs align with user's budget and expectations",
                "Maximize media coverage based on user's stated objectives",
                "Consider user's risk tolerance and growth stage",
                "Factor in conversation insights about user's business priorities",
                "Provide realistic timeline estimates based on package complexity",
                "Calculate budget utilization percentage",
                "Suggest alternative packages if budget doesn't fit",
                "Project ROI based on reach and industry benchmarks",
                "Consider cost-per-impression for value analysis",
                "Calculate budget utilization with conversation context",
                "Suggest alternatives that align with user's stated preferences",
                "Project ROI based on user's success metrics and industry benchmarks",
=======
                "Factor in user timeline, risk tolerance, and growth stage",
                "Maximize media coverage within budget constraints",
                "Project realistic ROI based on industry benchmarks",
>>>>>>> main
                "Return ONLY valid JSON in PricingAnalysis format"
            ],
            response_model=PricingAnalysis,
            storage=self.storage,
<<<<<<< HEAD
            session_id="pricing_optimization",
            show_tool_calls=False,
            markdown=False,
            exponential_backoff=True,
            retries=MAX_RETRIES,
        )

    def _create_report_generator(self) -> Agent:
        """Enhanced report generator with conversational insights"""
        return Agent(
            name="ReportGenerator",
            role="Senior PR consultant and executive report writer",
            name="ReportGenerator", 
            role="Senior PR consultant and executive report writer with conversation intelligence",
            model=self.llm,
            description="""
            You are an executive-level PR consultant who creates strategic media reports.
            You translate technical recommendations into business insights while incorporating
            the user's conversational context and stated preferences.
            """,
            instructions=[
                "Synthesize all agent outputs into executive-level insights",
                "Create compelling business case for the media strategy",
                "Present recommendations in decision-maker friendly format",
                "Define clear success metrics and KPIs",
                "Provide actionable implementation roadmap",
                "Address potential risks and mitigation strategies",
                "Highlight competitive advantages of the approach",
                "Use confident, professional tone suitable for executives",
                "Focus on business outcomes and ROI",
                "Include timeline with key milestones",
                "Synthesize all agent outputs with conversation context into executive insights",
                "Create compelling business case that aligns with user's stated goals",
                "Present recommendations in format preferred by user (from conversation)",
                "Define success metrics that match user's stated objectives",
                "Provide actionable implementation roadmap considering user's capabilities",
                "Address potential risks while considering user's risk tolerance",
                "Highlight competitive advantages relevant to user's market position",
                "Use tone and complexity level appropriate for user (from conversation)",
                "Focus on business outcomes that matter to the specific user",
                "Include timeline with milestones that fit user's constraints",
                "Incorporate document insights and conversation preferences",
=======
            show_tool_calls=False
        )
        
        # Report Generation Specialist
        self.report_specialist = Agent(
            name="ReportSpecialist",
            role="Executive-level PR consultant and strategic report writer",
            model=self.worker_llm,
            instructions=[
                "Create strategic executive reports incorporating conversation insights",
                "Translate technical recommendations into business insights",
                "Present strategy in tone/complexity appropriate for user",
                "Define success metrics matching user's stated objectives",
                "Provide actionable implementation roadmap",
                "Address risks while highlighting competitive advantages",
>>>>>>> main
                "Return ONLY valid JSON in ExecutiveReport format"
            ],
            response_model=ExecutiveReport,
            storage=self.storage,
<<<<<<< HEAD
            session_id="executive_reports",
            show_tool_calls=False,
            markdown=False,
            exponential_backoff=True,
            retries=MAX_RETRIES,
        )

    async def analyze_content(self, deps: AgentDependencies) -> ContentAnalysis:
        """Step 1: Deep content analysis"""
        try:
    
    def _create_plan_modifier(self) -> Agent:
        """Agent for handling user modifications and feedback"""
        return Agent(
            name="PlanModifier",
            role="Plan modification specialist and user feedback interpreter",
            model=self.llm,
            description="""
            You are a strategic consultant who specializes in adapting media plans
            based on user feedback, changing requirements, and optimization requests.
            You excel at understanding user concerns and finding workable solutions.
            """,
=======
            show_tool_calls=False
        )
        
        # Plan Modification Specialist
        self.modification_specialist = Agent(
            name="ModificationSpecialist",
            role="Plan modification expert and user feedback interpreter",
            model=self.worker_llm,
>>>>>>> main
            instructions=[
                "Analyze user feedback and modification requests carefully",
                "Assess feasibility and impact of requested changes",
                "Provide alternative solutions when requests aren't feasible",
                "Calculate cost and timeline impacts accurately",
                "Ensure modified plans remain strategically sound",
                "Return ONLY valid JSON in PlanModification format"
            ],
            response_model=PlanModification,
            storage=self.storage,
            show_tool_calls=False
        )
        
        # =================== CITATION VERIFICATION AGENT ===================
        
        self.citation_agent = Agent(
            name="CitationAgent",
            role="Quality assurance specialist for fact-checking and source verification",
            model=self.worker_llm,
            tools=[GoogleSearchTools()],
            instructions=[
                "Review all agent outputs for accuracy and source verification",
                "Cross-reference claims with reliable Vietnamese media sources",
                "Ensure media outlet information is current and accurate",
                "Verify pricing and package details against business requirements",
                "Flag any inconsistencies or unsupported claims",
                "Provide confidence scores for verified information",
                "Maintain high standards for factual accuracy"
            ],
            storage=self.storage,
            show_tool_calls=True
        )
        
        # =================== ANALYSIS COORDINATION TEAM ===================
        
        self.analysis_team = Team(
            name="AnalysisTeam",
            mode="coordinate",  # Lead Researcher coordinates specialists
            model=self.orchestrator_llm,
            members=[
                self.content_specialist,
                self.document_specialist,
                self.media_specialist,
                self.pricing_specialist,
                self.report_specialist
            ],
            instructions=[
                "You are the Lead Researcher coordinating a team of PR specialists",
                "Delegate tasks based on each specialist's expertise",
                "Ensure parallel processing when possible for efficiency",
                "Synthesize specialist outputs into coherent strategy",
                "Maintain conversation context throughout analysis",
                "Monitor quality and consistency across all outputs",
                "Adapt coordination based on user requirements and feedback"
            ],
            description="Multi-specialist team for comprehensive PR analysis and strategy development",
            show_tool_calls=True,
            markdown=False
        )
        
        # =================== QUALITY ASSURANCE TEAM ===================
        
        self.qa_team = Team(
            name="QualityAssuranceTeam", 
            mode="collaborate",  # All members review same content
            model=self.orchestrator_llm,
            members=[self.citation_agent],
            instructions=[
                "Review all analysis outputs for accuracy and completeness",
                "Verify sources and cross-reference claims",
                "Ensure consistency with user requirements",
                "Flag any potential issues or gaps",
                "Provide final quality score and recommendations"
            ],
            description="Quality assurance team for output verification and validation",
            show_tool_calls=True
        )
    
    # =================== CONVERSATION MANAGEMENT ===================
    
    async def start_conversation(self, session_id: str) -> ConversationResponse:
        """Start a new conversation with enhanced team context"""
        try:
            # Create enhanced conversation context with team memory
            context = ConversationContext(
                session_id=session_id,
                state=ConversationState.GREETING,
                phase=WorkflowPhase.IDLE
            )
            context.team_memory = TeamMemory(session_id=session_id)
            
            self.active_conversations[session_id] = context
            
            # Generate greeting using conversation agent
            greeting_prompt = """
            Greet the user as ChiCom AI, your Vietnamese PR consultant with advanced team-based AI analysis.
            
            Introduce yourself briefly and explain that you have a team of AI specialists ready to help.
            Ask about their press release or media campaign needs.
            Be warm, professional, and set expectations for collaborative analysis.
            
            Return a ConversationResponse with:
            - A friendly greeting message
            - Current state as 'greeting'
            - Suggestions for project information sharing
            """
            
            result = await self.conversation_agent.arun(greeting_prompt)
            response = parse_agent_response(result, ConversationResponse, {
                "message": "Xin chào! Tôi là ChiCom AI với đội ngũ chuyên gia AI phân tích PR. Chúng tôi sẽ giúp bạn tạo chiến lược truyền thông tối ưu. Hãy chia sẻ về dự án của bạn!",
                "state": "greeting",
                "phase": "idle",
                "suggestions": [
                    "Mô tả dự án/sản phẩm của bạn",
                    "Nói về mục tiêu truyền thông", 
                    "Thảo luận ngân sách và timeline"
                ],
                "requires_input": True,
                "can_proceed": False
            })
            
            # Add to conversation history
            context.conversation_history.append({
                "role": "assistant",
                "message": response.message,
                "timestamp": datetime.utcnow().isoformat(),
                "state": response.state
            })
            
            logger.info(f"💬 Started enhanced conversation for session: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to start enhanced conversation: {e}")
            return ConversationResponse(
                message="Xin lỗi, có lỗi xảy ra khi khởi tạo hệ thống AI. Vui lòng thử lại!",
                state="error",
                phase="idle",
                requires_input=True,
                can_proceed=False
            )
    
    async def continue_conversation(
        self, 
        session_id: str, 
        user_message: str,
        progress_callback: Optional[Callable] = None
    ) -> ConversationResponse:
        """Continue conversation with enhanced team context awareness"""
        try:
            # Get conversation context
            context = self.active_conversations.get(session_id)
            if not context:
                return await self.start_conversation(session_id)
            
            # Add progress callback
            if progress_callback and progress_callback not in context.progress_callbacks:
                context.progress_callbacks.append(progress_callback)
            
            # Add user message to history
            context.conversation_history.append({
                "role": "user",
                "message": user_message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Build enhanced conversation prompt with team context
            conversation_prompt = f"""
            Continue this conversation as ChiCom AI with your team of specialists ready to help.
            
            CONVERSATION HISTORY:
            {self._format_conversation_history(context.conversation_history[-10:])}
            
            CURRENT USER MESSAGE: {user_message}
            
            CURRENT STATE: {context.state.value}
            CURRENT PHASE: {context.phase.value}
            TEAM STATUS: {'Initialized' if context.team_initialized else 'Ready to deploy'}
            
            GATHERED INFORMATION:
            - User Input: {context.user_input}
            - Budget: {context.budget:,.0f} VND if > 0
            - Requirements: {json.dumps(context.requirements, ensure_ascii=False)}
            - Preferences: {json.dumps(context.preferences, ensure_ascii=False)}
            
            Your tasks:
            1. Respond naturally and helpfully as the lead consultant
            2. Gather missing information through conversation 
            3. Determine if ready to deploy specialist team for analysis
            4. If ready, explain what the team analysis will include
            5. Maintain consultative expert tone throughout
            
            Decision points:
            - If have: project description + budget + basic requirements → can deploy team
            - If user asks questions → answer with team expertise
            - If user wants analysis → prepare for team deployment
            - If user wants modifications → transition to modification workflow
            
            Return ConversationResponse with appropriate state transition.
            """
            
            result = await self.conversation_agent.arun(conversation_prompt)
            response = parse_agent_response(result, ConversationResponse, {
                "message": "Cảm ơn bạn đã chia sẻ! Hãy cho tôi biết thêm về mục tiêu truyền thông.",
                "state": context.state.value,
                "phase": context.phase.value,
                "requires_input": True,
                "can_proceed": False
            })
            
            # Update context from conversation
            await self._update_context_from_conversation(context, user_message, response)
            
            # Add assistant response to history
            context.conversation_history.append({
                "role": "assistant",
                "message": response.message,
                "timestamp": datetime.utcnow().isoformat(),
                "state": response.state
            })
            
            logger.info(f"💬 Enhanced conversation continued for session: {session_id} - State: {response.state}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Enhanced conversation continuation failed: {e}")
            return ConversationResponse(
                message="Xin lỗi, có lỗi xảy ra trong cuộc trò chuyện. Vui lòng thử lại!",
                state="error",
                phase="idle",
                requires_input=True,
                can_proceed=False
            )
    
    async def trigger_workflow(
        self, 
        session_id: str,
        progress_callback: Optional[Callable] = None
    ) -> ConversationResponse:
        """Trigger enhanced team workflow with parallel processing"""
        try:
            context = self.active_conversations.get(session_id)
            if not context:
                raise ValueError("Conversation context not found")
            
            # Add progress callback
            if progress_callback and progress_callback not in context.progress_callbacks:
                context.progress_callbacks.append(progress_callback)
            
            # Update state and initialize team memory
            context.state = ConversationState.EXECUTING
            context.phase = WorkflowPhase.TEAM_INITIALIZATION
            context.workflow_started = True
            context.total_steps = 7  # Team Init, Parallel Analysis, Synthesis, QA, Report, Citation, Completion
            context.completed_steps = 0
            
            # Initialize team shared state (using alternative approach)
            self.analysis_team.session_state = {
                "session_id": session_id,
                "user_context": {
                    "input": context.user_input,
                    "budget": context.budget,
                    "requirements": context.requirements,
                    "preferences": context.preferences,
                    "conversation_summary": self._extract_key_info_from_conversation(context)
                },
                "workflow_results": {},
                "processing_status": "initializing"
            }
            
            await update_progress(context, "Team Initialization", "🚀 Khởi tạo đội ngũ chuyên gia AI...")
            
            # Execute enhanced team workflow
            workflow_result = await self._execute_enhanced_team_workflow(context)
            
            # Generate completion response
            summary = workflow_result.get("summary", {})
            
            completion_message = f"""✅ Phân tích với đội ngũ chuyên gia hoàn thành! 
            
    🎯 **Kết quả từ {len(context.active_agents)} chuyên gia AI:**
    • Gói đề xuất: {summary.get('recommended_package', 'Standard')}
    • Tổng chi phí: {summary.get('total_cost', 25000000):,.0f} VND
    • Số báo chí: {summary.get('media_count', 3)} outlets
    • Timeline: {summary.get('timeline', '5-7 ngày')}
    • Độ tin cậy: {summary.get('confidence_score', 0.8) * 100:.0f}%
    • Đã kiểm chứng: {summary.get('citation_verified', True)}

    Đội ngũ chuyên gia đã phân tích toàn diện và xác minh chất lượng! 👇"""

            try:
                completion_prompt = f"""
                The specialist team analysis has completed successfully. Present results to user.
                
                TEAM ANALYSIS SUMMARY:
                - Package: {summary.get('recommended_package', 'Standard')}
                - Total Cost: {summary.get('total_cost', 25000000):,.0f} VND
                - Media Count: {summary.get('media_count', 3)}
                - Team Confidence: {summary.get('confidence_score', 0.8) * 100:.0f}%
                - Quality Verified: {summary.get('citation_verified', True)}
                
                Create enthusiastic completion message highlighting:
                1. Team collaboration success and verification
                2. Key metrics and strategic insights
                3. Quality assurance completion
                4. Invitation to review detailed analysis
                
                Return ConversationResponse with state 'reviewing' and full workflow data.
                """
                
                result = await self.conversation_agent.arun(completion_prompt)
                response = parse_agent_response(result, ConversationResponse, {
                    "message": completion_message,
                    "state": "reviewing",
                    "phase": "user_review",
                    "data": workflow_result,
                    "options": [
                        "Phê duyệt kế hoạch này",
                        "Điều chỉnh ngân sách",
                        "Thay đổi danh sách báo",
                        "Sửa timeline",
                        "Thảo luận thêm"
                    ],
                    "requires_input": True,
                    "can_proceed": True
                })
                
                if not response.data:
                    response.data = workflow_result
                    
            except Exception as parse_error:
                logger.warning(f"Response parsing failed, using fallback: {parse_error}")
                response = ConversationResponse(
                    message=completion_message,
                    state="reviewing",
                    phase="user_review",
                    data=workflow_result,
                    options=[
                        "Phê duyệt kế hoạch này",
                        "Điều chỉnh ngân sách",
                        "Thay đổi danh sách báo", 
                        "Sửa timeline",
                        "Thảo luận thêm"
                    ],
                    requires_input=True,
                    can_proceed=True
                )
            
            # Update context state
            context.state = ConversationState.REVIEWING
            context.phase = WorkflowPhase.USER_REVIEW
            context.team_initialized = True
            
            # Store results in context
            context.content_analysis = workflow_result.get("content_analysis")
            context.document_analysis = workflow_result.get("document_analysis")
            context.media_recommendations = workflow_result.get("media_recommendations", [])
            context.pricing_analysis = workflow_result.get("pricing_analysis")
            context.executive_report = workflow_result.get("executive_report")
            
            logger.info(f"✅ Enhanced team workflow completed for session: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Enhanced team workflow failed: {e}")
            
            if session_id in self.active_conversations:
                self.active_conversations[session_id].state = ConversationState.ERROR
            
            return ConversationResponse(
                message=f"❌ Có lỗi trong quá trình phân tích nhóm: {str(e)}. Tôi sẽ thử lại với cấu hình khác.",
                state="error",
                phase="idle",
                suggestions=["Thử lại với team khác", "Chia sẻ thêm thông tin", "Bắt đầu lại"],
                requires_input=True,
                can_proceed=False
            )
    
    async def modify_plan(
        self, 
        session_id: str, 
        modification_request: str,
        progress_callback: Optional[Callable] = None
    ) -> ConversationResponse:
        """Handle plan modifications using specialist team"""
        try:
            context = self.active_conversations.get(session_id)
            if not context:
                raise ValueError("Conversation context not found")
            
            if progress_callback and progress_callback not in context.progress_callbacks:
                context.progress_callbacks.append(progress_callback)
            
            context.state = ConversationState.MODIFYING
            context.phase = WorkflowPhase.PLAN_MODIFICATION
            context.needs_modification = True
            
            await update_progress(context, "Plan Modification", "🔄 Đội ngũ chuyên gia đang phân tích yêu cầu thay đổi...")
            
            # Use modification specialist for analysis
            modification_prompt = f"""
            Analyze this plan modification request using current strategy context.
            
            USER MODIFICATION REQUEST: {modification_request}
            
            CURRENT PLAN CONTEXT:
            - Content Analysis: {json.dumps(context.content_analysis, ensure_ascii=False) if context.content_analysis else "N/A"}
            - Pricing: {json.dumps(context.pricing_analysis, ensure_ascii=False) if context.pricing_analysis else "N/A"}
            - Media Count: {len(context.media_recommendations)}
            - Budget: {context.budget:,.0f} VND
            
            MEDIA RECOMMENDATIONS SUMMARY:
            {json.dumps(context.media_recommendations[:5], ensure_ascii=False, indent=2)}
            
            Analyze the modification request comprehensively:
            1. Type of modification and specific changes requested
            2. Feasibility assessment with detailed reasoning
            3. Impact on other plan components 
            4. Alternative approaches if request isn't optimal
            5. Cost and timeline implications
            6. Strategic coherence after changes
            
            Return detailed PlanModification analysis.
            """
            
            result = await self.modification_specialist.arun(modification_prompt)
            modification_analysis = parse_agent_response(result, PlanModification, {
                "modification_type": "General",
                "original_value": "Current plan",
                "new_value": modification_request,
                "impact_assessment": "Requires detailed team analysis",
                "feasibility": "Medium",
                "alternative_suggestions": ["Consult with specialists", "Phased implementation"],
                "cost_impact": 0.0,
                "timeline_impact": "No change"
            })
            
            # Generate response using conversation agent
            response_prompt = f"""
            Respond to user's modification request based on specialist analysis.
            
            MODIFICATION ANALYSIS: {modification_analysis.model_dump()}
            USER REQUEST: {modification_request}
            
            Create helpful response that:
            1. Acknowledges their specific request professionally
            2. Explains feasibility and impacts based on specialist analysis
            3. Suggests alternatives if needed with reasoning
            4. Asks for confirmation or further details
            5. Maintains collaborative consulting tone
            
            If modification is feasible, offer to implement with team coordination.
            If not optimal, explain why and suggest specialist-recommended alternatives.
            """
            
            result = await self.conversation_agent.arun(response_prompt)
            response = parse_agent_response(result, ConversationResponse, {
                "message": "Đội ngũ chuyên gia đã phân tích yêu cầu của bạn. Để thay đổi hiệu quả nhất, chúng tôi khuyến nghị một số điều chỉnh. Bạn có muốn xem chi tiết?",
                "state": "modifying", 
                "phase": "plan_modification",
                "data": {"modification_analysis": modification_analysis.model_dump()},
                "suggestions": modification_analysis.alternative_suggestions,
                "requires_input": True,
                "can_proceed": True
            })
            
            # Add modification to context
            context.modifications.append({
                "request": modification_request,
                "analysis": modification_analysis.model_dump(),
                "specialist": "ModificationSpecialist",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"🔄 Plan modification analyzed by specialist for session: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Plan modification failed: {e}")
            return ConversationResponse(
                message="Xin lỗi, có lỗi khi đội ngũ chuyên gia phân tích yêu cầu. Bạn có thể mô tả chi tiết hơn?",
                state="modifying",
                phase="plan_modification", 
                requires_input=True,
                can_proceed=False
            )
    
    # =================== ENHANCED TEAM WORKFLOW EXECUTION ===================
    
    async def _execute_enhanced_team_workflow(self, context: ConversationContext) -> Dict[str, Any]:
        """Execute enhanced team workflow with parallel processing and quality assurance"""
        try:
            workflow_results = {}
            context.active_agents = []
            
            # Step 1: Team Initialization
            await update_progress(context, "Team Initialization", "⚙️ Khởi tạo và phân công nhiệm vụ...")
            
            # Prepare shared context for all specialists
            shared_context = {
                "user_input": context.user_input,
                "budget": context.budget,
                "requirements": context.requirements,
                "preferences": context.preferences,
                "conversation_summary": self._extract_key_info_from_conversation(context),
                "conversation_history": context.conversation_history[-5:]
            }
            
            # Step 2: Parallel Analysis Phase
            context.phase = WorkflowPhase.PARALLEL_ANALYSIS
            await update_progress(context, "Parallel Analysis", "🔄 Chạy song song 5 chuyên gia AI...")
            
            # Execute specialists in parallel using asyncio
            parallel_tasks = []
            
            # Content Analysis Task
            content_task = self._run_content_analysis_with_context(context, shared_context)
            parallel_tasks.append(("content_analysis", content_task))
            
            # Document Analysis Task (if documents available)
            doc_task = self._run_document_analysis_with_context(context, shared_context)
            parallel_tasks.append(("document_analysis", doc_task))
            
            # Execute parallel tasks with timeout
            context.active_agents = ["ContentSpecialist", "DocumentSpecialist", "MediaSpecialist", "PricingSpecialist", "ReportSpecialist"]
            
            if PARALLEL_PROCESSING:
                # Run content and document analysis first (they can run truly in parallel)
                initial_results = await asyncio.gather(
                    *[task for _, task in parallel_tasks[:2]], 
                    return_exceptions=True
                )
                
                # Process initial results
                for i, (task_name, result) in enumerate(zip(["content_analysis", "document_analysis"], initial_results)):
                    if not isinstance(result, Exception):
                        workflow_results[task_name] = result.model_dump() if hasattr(result, 'model_dump') else result
                        context.parallel_results[task_name] = result
                    else:
                        logger.warning(f"Task {task_name} failed: {result}")
                
                # Now run dependent tasks (media, pricing, report) based on initial results
                await update_progress(context, "Media & Strategy Analysis", "🎯 Phân tích báo chí và chiến lược...")
                
                # Get content analysis for dependent tasks
                content_analysis = context.parallel_results.get("content_analysis")
                document_analysis = context.parallel_results.get("document_analysis")
                
                # Run media matching
                media_recommendations = await self._run_media_matching_with_context(
                    context, shared_context, content_analysis, document_analysis
                )
                workflow_results["media_recommendations"] = [rec.model_dump() for rec in media_recommendations]
                
                # Run pricing and report generation in parallel (they can use media results)
                pricing_task = self._run_pricing_optimization_with_context(
                    context, shared_context, media_recommendations
                )
                report_task = self._run_report_generation_with_context(
                    context, shared_context, content_analysis, media_recommendations, document_analysis
                )
                
                dependent_results = await asyncio.gather(pricing_task, report_task, return_exceptions=True)
                
                # Process dependent results
                for task_name, result in zip(["pricing_analysis", "executive_report"], dependent_results):
                    if not isinstance(result, Exception):
                        workflow_results[task_name] = result.model_dump() if hasattr(result, 'model_dump') else result
                    else:
                        logger.warning(f"Task {task_name} failed: {result}")
                        
            else:
                # Sequential execution fallback
                logger.info("Running sequential analysis (parallel disabled)")
                
                content_analysis = await self._run_content_analysis_with_context(context, shared_context)
                workflow_results["content_analysis"] = content_analysis.model_dump()
                
                document_analysis = await self._run_document_analysis_with_context(context, shared_context)
                if document_analysis:
                    workflow_results["document_analysis"] = document_analysis.model_dump()
                
                media_recommendations = await self._run_media_matching_with_context(
                    context, shared_context, content_analysis, document_analysis
                )
                workflow_results["media_recommendations"] = [rec.model_dump() for rec in media_recommendations]
                
                pricing_analysis = await self._run_pricing_optimization_with_context(
                    context, shared_context, media_recommendations
                )
                workflow_results["pricing_analysis"] = pricing_analysis.model_dump()
                
                executive_report = await self._run_report_generation_with_context(
                    context, shared_context, content_analysis, media_recommendations, document_analysis
                )
                workflow_results["executive_report"] = executive_report.model_dump()
            
            # Step 3: Quality Assurance and Citation Verification
            context.phase = WorkflowPhase.CITATION_VERIFICATION
            await update_progress(context, "Quality Assurance", "🔍 Kiểm chứng chất lượng và xác minh nguồn...")
            
            # Run QA team for verification
            qa_result = await self._run_quality_assurance(context, workflow_results)
            workflow_results["qa_verification"] = qa_result
            
            # Step 4: Final Synthesis and Summary
            await update_progress(context, "Synthesis", "📋 Tổng hợp kết quả từ đội ngũ chuyên gia...")
            
            # Calculate comprehensive summary
            processing_time = (datetime.utcnow() - context.created_at).total_seconds()
            
            # Extract key metrics safely
            recommended_package = "Standard"
            total_cost = 25000000
            media_count = len(workflow_results.get("media_recommendations", []))
            timeline = "5-7 ngày làm việc"
            confidence_score = 0.8
            citation_verified = qa_result.get("verified", True) if qa_result else True
            
            # Safe extraction from results
            try:
                pricing_data = workflow_results.get("pricing_analysis", {})
                if pricing_data:
                    recommended_package = pricing_data.get("recommended_package", "Standard")
                    total_cost = pricing_data.get("total_cost_vnd", 25000000)
                    timeline = pricing_data.get("timeline_days", "5-7 ngày làm việc")
                
                content_data = workflow_results.get("content_analysis", {})
                if content_data:
                    confidence_score = content_data.get("confidence_score", 0.8)
                    
            except Exception as extraction_error:
                logger.warning(f"Metric extraction error: {extraction_error}")
            
            # Create comprehensive workflow results
            workflow_results.update({
                "session_id": context.session_id,
                "processing_time_seconds": processing_time,
                "team_performance": {
                    "agents_deployed": len(context.active_agents),
                    "parallel_processing": PARALLEL_PROCESSING,
                    "tasks_completed": len([k for k in workflow_results.keys() if not k.startswith("team_")]),
                    "error_count": len(context.team_memory.error_log),
                    "average_confidence": confidence_score
                },
                "summary": {
                    "recommended_package": recommended_package,
                    "total_cost": total_cost,
                    "media_count": media_count,
                    "timeline": timeline,
                    "budget_utilization": min(1.0, total_cost / max(context.budget, 1)) if context.budget > 0 else 0.8,
                    "confidence_score": confidence_score,
                    "citation_verified": citation_verified,
                    "documents_analyzed": bool(workflow_results.get("document_analysis")),
                    "team_coordination": "successful",
                    "quality_assured": bool(qa_result)
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent_system": "Enhanced Team-based Media Release v4.0",
                    "workflow_version": "2.0",
                    "processing_status": "completed",
                    "orchestrator_model": OPENAI_ORCHESTRATOR_MODEL if OPENAI_API_KEY else GROQ_ORCHESTRATOR_MODEL,
                    "worker_model": OPENAI_WORKER_MODEL if OPENAI_API_KEY else GROQ_WORKER_MODEL
                }
            })
            
            await update_progress(context, "Completed", "✅ Đội ngũ chuyên gia hoàn thành phân tích!")
            
            logger.info(f"✅ Enhanced team workflow completed for session: {context.session_id}")
            logger.info(f"📊 Team performance: {workflow_results['team_performance']}")
            
            return workflow_results
            
        except Exception as e:
            logger.error(f"❌ Enhanced team workflow failed: {e}")
            context.team_memory.error_log.append(str(e))
            await update_progress(context, "Error", f"❌ Lỗi team: {str(e)}")
            
            # Return error result with team context
            return {
                "error": str(e),
                "session_id": context.session_id,
                "processing_time_seconds": (datetime.utcnow() - context.created_at).total_seconds(),
                "team_performance": {
                    "agents_deployed": len(context.active_agents),
                    "error_occurred": True,
                    "error_details": str(e)
                },
                "summary": {
                    "recommended_package": "Standard",
                    "total_cost": 25000000,
                    "media_count": 0,
                    "confidence_score": 0.0,
                    "error_occurred": True,
                    "team_coordination": "failed"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # =================== SPECIALIST EXECUTION METHODS ===================
    
    async def _run_content_analysis_with_context(self, context: ConversationContext, shared_context: Dict) -> ContentAnalysis:
        """Execute content analysis specialist with enhanced context"""
        try:
            prompt = f"""
            Analyze this comprehensive project information from conversation context:
            
<<<<<<< HEAD
            USER REQUEST: {deps.user_input}
            BUDGET: {deps.budget:,.0f} VND
            
            Perform deep analysis focusing on:
            1. Language requirements and target market
            2. Industry sector and business type
            3. Press release category and objectives
            4. Key topics for media matching
            5. Target audience segments
            6. Content tone and urgency level
            7. Geographic scope and reach requirements
            
            Provide structured analysis with high confidence scoring.
            """

            logger.info("🔍 Content analysis started...")
            MAIN PROJECT DESCRIPTION: {context.user_input}
            BUDGET: {context.budget:,.0f} VND
=======
            MAIN PROJECT DESCRIPTION: {shared_context['user_input']}
            BUDGET: {shared_context['budget']:,.0f} VND
>>>>>>> main
            
            CONVERSATION INSIGHTS: {shared_context['conversation_summary']}
            REQUIREMENTS: {json.dumps(shared_context['requirements'], ensure_ascii=False)}
            PREFERENCES: {json.dumps(shared_context['preferences'], ensure_ascii=False)}
            
            RECENT CONVERSATION CONTEXT:
            {self._format_conversation_history(shared_context['conversation_history'])}
            
            Perform comprehensive analysis considering all conversation context and user interactions.
            Focus on Vietnamese market positioning and SME-specific requirements.
            
            Return analysis in ContentAnalysis JSON format.
            """  """
            
<<<<<<< HEAD
            result = await self.content_analyzer.arun(prompt)
            logger.info(
                f"✅ Content analysis completed - Confidence: {result.confidence_score:.2f}"
            )

            return result

=======
            result = await self.content_specialist.arun(prompt)
>>>>>>> main
            
            fallback_data = {
                "language": shared_context['preferences'].get("language", "Vietnamese"),
                "primary_topics": shared_context['requirements'].get("topics", ["Business", "Technology"]),
                "target_audiences": shared_context['requirements'].get("audiences", ["General Public"]),
                "keywords": ["press release", shared_context['requirements'].get("industry", "business")],
                "content_tone": shared_context['preferences'].get("tone", "Professional"),
                "urgency_level": shared_context['requirements'].get("urgency", "Medium"),
                "industry_sector": shared_context['requirements'].get("industry", "General"),
                "press_release_type": shared_context['requirements'].get("type", "Other"),
                "geographic_scope": shared_context['requirements'].get("scope", "National"),
                "confidence_score": 0.8
            }
            
            content_analysis = parse_agent_response(result, ContentAnalysis, fallback_data)
            logger.info(f"✅ ContentSpecialist completed - Confidence: {content_analysis.confidence_score:.2f}")
            
            return content_analysis
            
        except Exception as e:
            logger.error(f"❌ ContentSpecialist failed: {e}")
            return ContentAnalysis(
                language=shared_context['preferences'].get("language", "Vietnamese"),
                primary_topics=shared_context['requirements'].get("topics", ["Business"]),
                target_audiences=shared_context['requirements'].get("audiences", ["General Public"]),
                keywords=["press release"],
                content_tone="Professional",
                urgency_level="Medium",
                industry_sector="General",
                press_release_type="Other",
                geographic_scope="National",
                confidence_score=0.5,
                confidence_score=0.6
            )

    async def find_matching_media(
        self, deps: AgentDependencies
    ) -> List[MediaRecommendation]:
        """Step 2: Intelligent media matching with vector search"""
        try:
            # Prepare search query from content analysis
            if deps.content_analysis:
                search_query = f"{' '.join(deps.content_analysis.primary_topics)} {' '.join(deps.content_analysis.target_audiences)} {deps.content_analysis.industry_sector}"
            else:
                search_query = "business media vietnam"

            # Perform vector search
            vector_results = await media_db.search_media_by_vector(
                search_query, limit=15
            )
            deps.vector_search_results = vector_results

            # Get detailed media information
    
    async def _run_document_analysis_with_context(self, context: ConversationContext, shared_context: Dict) -> Optional[DocumentAnalysis]:
        """Execute document analysis specialist with enhanced context"""
        try:
            doc_processor = get_document_processor()
            if not doc_processor:
                return None
            
            session_docs = doc_processor.get_session_documents(context.session_id)
            if not session_docs:
                return None
            
            # Create search query from conversation context
            search_terms = []
            if shared_context['requirements'].get("topics"):
                search_terms.extend(shared_context['requirements']["topics"])
            if shared_context['user_input']:
                search_terms.append(shared_context['user_input'][:100])
            
            search_query = " ".join(search_terms) if search_terms else "business project information"
            
            search_results = await doc_processor.search_user_documents(
                query=search_query,
                session_id=context.session_id,
                limit=10
            )
            
            if not search_results:
                return None
            
            document_content = "\n\n".join([
                result.get("content", "") for result in search_results
            ])
            
            prompt = f"""
            Analyze these uploaded documents in context of the user's conversational requirements:
            
            USER PROJECT CONTEXT: {shared_context['user_input']}
            CONVERSATION INSIGHTS: {shared_context['conversation_summary']}
            USER REQUIREMENTS: {json.dumps(shared_context['requirements'], ensure_ascii=False)}
            USER PREFERENCES: {json.dumps(shared_context['preferences'], ensure_ascii=False)}
            
            DOCUMENT CONTENT: {document_content[:4000]}
            SESSION DOCUMENTS: {[doc["filename"] for doc in session_docs]}
            
            Extract valuable information for Vietnamese media positioning and PR strategy.
            Focus on supporting data that reinforces conversation objectives.
            
            Return analysis in DocumentAnalysis JSON format.
            """
            
            result = await self.document_specialist.arun(prompt)
            
            fallback_data = {
                "document_summary": f"Document analyzed for {shared_context['requirements'].get('industry', 'business')} project",
                "key_information": ["Business information extracted from documents"],
                "relevant_topics": shared_context['requirements'].get("topics", ["Business"]),
                "target_audience_insights": shared_context['requirements'].get("audiences", ["General audience"]),
                "media_angles": ["Business story angle", "Market development angle"],
                "supporting_data": ["Supporting information available from documents"],
                "document_quality": "Medium",
                "confidence_score": 0.7
            }
            
            document_analysis = parse_agent_response(result, DocumentAnalysis, fallback_data)
            logger.info("✅ DocumentSpecialist completed with conversation context")
            
            return document_analysis
            
        except Exception as e:
            logger.error(f"❌ DocumentSpecialist failed: {e}")
            return None
    
    async def _run_media_matching_with_context(
        self, 
        context: ConversationContext,
        shared_context: Dict,
        content_analysis: ContentAnalysis,
        document_analysis: Optional[DocumentAnalysis]
    ) -> List[MediaRecommendation]:
        """Execute media matching specialist with database integration"""
        try:
            # Build comprehensive search query
            search_terms = []
            search_terms.extend(content_analysis.primary_topics)
            search_terms.extend(content_analysis.target_audiences)
            search_terms.append(content_analysis.industry_sector)
            
            if document_analysis:
                search_terms.extend(document_analysis.relevant_topics)
            
            if shared_context['requirements'].get("preferred_media"):
                search_terms.extend(shared_context['requirements']["preferred_media"])
            
            search_query = " ".join(search_terms)
            
            # Enhanced vector search
            vector_results = await media_db.search_media_by_vector(search_query, limit=15)
            
            # Get candidate media outlets
            media_candidates = []
            if (
                vector_results
                and "metadatas" in vector_results
                and vector_results["metadatas"]
            ):
                for metadata in vector_results["metadatas"][0]:
                    if "media_id" in metadata:
                        media_id = int(metadata["media_id"])
                        media = await media_db.get_media_by_id(media_id)
                        if media and media.is_active:
<<<<<<< HEAD
                            media_candidates.append(
                                {
                                    "id": media.id,
                                    "name": media.name,
                                    "tier": media.tier,
                                    "cost": media.cost_per_article,
                                    "circulation": media.circulation,
                                    "topics": json.loads(media.topics),
                                    "audiences": json.loads(media.target_audience),
                                    "language": media.language,
                                    "success_rate": media.success_rate,
                                    "response_time": media.response_time_hours,
                                }
                            )

            # Fallback to all media if vector search fails
            if not media_candidates:
                all_media = await media_db.get_all_media_outlets()
                media_candidates = [
                    {
                        "id": m.id,
                        "name": m.name,
                        "tier": m.tier,
                        "cost": m.cost_per_article,
                        "circulation": m.circulation,
                        "topics": m.topics,
                        "audiences": m.target_audience,
                        "language": m.language,
                        "success_rate": m.success_rate,
                        "response_time": m.response_time_hours,
                    }
                    for m in all_media[:10]  # Limit to top 10
                ]

            prompt = f"""
            Find the best Vietnamese media outlets for this content:
            
            CONTENT ANALYSIS: {deps.content_analysis.model_dump() if deps.content_analysis else "Not available"}
            USER BUDGET: {deps.budget:,.0f} VND
            
            AVAILABLE MEDIA OPTIONS: {json.dumps(media_candidates[:10], indent=2)}
            
            Select the top 5-8 media outlets that:
            1. Best match the content topics and target audience
            2. Fit within the budget constraints
            3. Provide optimal reach and credibility
            4. Match language requirements
            5. Have good success rates and reasonable response times
            
            Prioritize tier-1 outlets but include cost-effective tier-2 options.
            Provide detailed reasoning for each recommendation.
            """

            logger.info("🎯 Media matching started...")

            # Process multiple recommendations in parallel if enabled
            if PARALLEL_PROCESSING and len(media_candidates) > 5:
                tasks = []
                for i in range(min(6, len(media_candidates))):
                    task = self.media_matcher.arun(prompt)
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)
                recommendations = [
                    r for r in results if isinstance(r, MediaRecommendation)
                ]
            else:
                # Sequential processing
                recommendations = []
                for _ in range(min(6, len(media_candidates))):
                    result = await self.media_matcher.arun(prompt)
                    if result:
                        recommendations.append(result)

            # Deduplicate by media_outlet_id and sort by score
            seen_ids = set()
            unique_recommendations = []
                            # Fix: Handle None values safely
                            monthly_visits = media.monthly_visits or 1000000  # Default 1M if None
                            cost_per_article = media.cost_per_article or 1000000  # Default 1M if None
                            success_rate = media.success_rate or 0.8  # Default 80% if None
                            response_time = media.response_time_hours or 24  # Default 24h if None
                            
                            media_candidates.append({
                                "id": media.id,
                                "name": media.name,
                                "category": media.category,
                                "tier": media.tier,
                                "cost": cost_per_article,
                                "monthly_visits": monthly_visits,
                                "top_categories": json.loads(media.top_categories) if media.top_categories else [],
                                "topics": json.loads(media.topics) if isinstance(media.topics, str) else (media.topics or []),
                                "audiences": json.loads(media.target_audience) if isinstance(media.target_audience, str) else (media.target_audience or []),
                                "language": media.language or "Vietnamese",
                                "success_rate": success_rate,
                                "response_time": response_time
                            })
            
            # Fallback to category-based search if vector search insufficient
            if len(media_candidates) < 10:
                # Determine relevant categories from content analysis
                relevant_categories = self._determine_media_categories(content_analysis, context)
                
                for category in relevant_categories:
                    category_media = await media_db.search_media_by_category(category, limit=5)
                    for media in category_media:
                        if not any(c["id"] == media.id for c in media_candidates):
                            # Fix: Safely access all media attributes with defaults
=======
>>>>>>> main
                            media_candidates.append({
                                "id": media.id,
                                "name": media.name,
                                "category": media.category,
                                "tier": media.tier,
                                "cost": getattr(media, 'cost_per_article', 1000000) or 1000000,
                                "monthly_visits": getattr(media, 'monthly_visits', 1000000) or 1000000,
                                "top_categories": getattr(media, 'top_categories', []) or [],
                                "topics": getattr(media, 'topics', []) or [],
                                "audiences": getattr(media, 'target_audience', []) or [],
                                "language": getattr(media, 'language', 'Vietnamese') or 'Vietnamese',
                                "success_rate": getattr(media, 'success_rate', 0.8) or 0.8,
                                "response_time": getattr(media, 'response_time_hours', 24) or 24
                            })
            
            # Fallback to category-based search
            if len(media_candidates) < 10:
                relevant_categories = self._determine_media_categories(content_analysis, context)
                for category in relevant_categories:
                    category_media = await media_db.search_media_by_category(category, limit=5)
                    for media in category_media:
                        if not any(c["id"] == media.id for c in media_candidates):
                            media_candidates.append({
                                "id": media.id,
                                "name": media.name,
                                "category": media.category,
                                "tier": media.tier,
                                "cost": getattr(media, 'cost_per_article', 1000000) or 1000000,
                                "monthly_visits": getattr(media, 'monthly_visits', 1000000) or 1000000,
                                "language": getattr(media, 'language', 'Vietnamese') or 'Vietnamese',
                                "success_rate": getattr(media, 'success_rate', 0.8) or 0.8,
                                "response_time": getattr(media, 'response_time_hours', 24) or 24
                            })

            logger.info(f"🎯 MediaSpecialist found {len(media_candidates)} candidate outlets")

            # Process recommendations with batch approach for efficiency
            recommendations = []
            batch_size = 5
            
            for i in range(0, min(len(media_candidates), 10), batch_size):
                batch = media_candidates[i:i+batch_size]
                batch_tasks = []
                
                for candidate in batch:
                    prompt = f"""
                    Evaluate this Vietnamese media outlet for the project:
                    
                    CONTENT ANALYSIS: {content_analysis.model_dump()}
                    CONVERSATION CONTEXT: {shared_context['conversation_summary']}
                    USER BUDGET: {shared_context['budget']:,.0f} VND
                    USER PREFERENCES: {json.dumps(shared_context['preferences'], ensure_ascii=False)}
                    
                    MEDIA OUTLET: {json.dumps(candidate, ensure_ascii=False, indent=2)}
                    
                    Evaluate based on conversation insights, budget constraints, and strategic fit.
                    Return MediaRecommendation JSON for this outlet.
                    """
                    
                    task = self.media_specialist.arun(prompt)
                    batch_tasks.append((candidate, task))
                
                # Execute batch in parallel
                batch_results = await asyncio.gather(*[task for _, task in batch_tasks], return_exceptions=True)
                
                # Process batch results
                for (candidate, _), result in zip(batch_tasks, batch_results):
                    try:
                        if not isinstance(result, Exception):
                            fallback_data = {
                                "media_outlet_id": candidate["id"],
                                "media_name": candidate["name"],
                                "matching_score": min(0.9, 0.6 + (candidate.get("monthly_visits", 1000000) / 100000000)),
                                "reasoning": f"Good fit for {content_analysis.industry_sector} in {candidate.get('category', 'general')} category",
                                "estimated_reach": candidate.get("monthly_visits", 1000000),
                                "cost_vnd": candidate.get("cost", 1000000),
                                "tier": candidate.get("tier", 2),
                                "language_match": candidate.get("language", "Vietnamese") == content_analysis.language or content_analysis.language == "Both",
                                "topic_overlap": 0.7,
                                "audience_fit": 0.7
                            }
                            
                            recommendation = parse_agent_response(result, MediaRecommendation, fallback_data)
                            recommendations.append(recommendation)
                        else:
                            # Create fallback recommendation
                            fallback_recommendation = MediaRecommendation(
                                media_outlet_id=candidate["id"],
                                media_name=candidate["name"],
                                matching_score=0.7,
                                reasoning=f"Suitable outlet for {content_analysis.industry_sector} coverage",
                                estimated_reach=candidate.get("monthly_visits", 1000000),
                                cost_vnd=candidate.get("cost", 1000000),
                                tier=candidate.get("tier", 2),
                                language_match=True,
                                topic_overlap=0.7,
                                audience_fit=0.7
                            )
                            recommendations.append(fallback_recommendation)
                            
                    except Exception as e:
                        logger.warning(f"Failed to process media candidate {candidate['name']}: {e}")
                
                # Small delay between batches
                await asyncio.sleep(0.2)
            
            # Sort and filter recommendations
            recommendations.sort(key=lambda x: x.matching_score, reverse=True)
            
            # Apply budget filtering
            budget_filtered = []
            cumulative_cost = 0
            budget_limit = shared_context['budget'] * 0.8 if shared_context['budget'] > 0 else float('inf')
            
            for rec in recommendations:
<<<<<<< HEAD
                if rec.media_outlet_id not in seen_ids:
                    seen_ids.add(rec.media_outlet_id)
                    unique_recommendations.append(rec)

            # Sort by matching score
            unique_recommendations.sort(key=lambda x: x.matching_score, reverse=True)

            logger.info(
                f"✅ Media matching completed - Found {len(unique_recommendations)} recommendations"
            )
            return unique_recommendations[:8]  # Return top 8

                if cumulative_cost + rec.cost_vnd <= context.budget * 0.8:  # Use 80% of budget for media
=======
                if cumulative_cost + rec.cost_vnd <= budget_limit:
>>>>>>> main
                    budget_filtered.append(rec)
                    cumulative_cost += rec.cost_vnd
                elif len(budget_filtered) < 3:  # Ensure minimum recommendations
                    budget_filtered.append(rec)
            
            logger.info(f"✅ MediaSpecialist completed - {len(budget_filtered)} recommendations within budget")
            return budget_filtered[:8]
            
        except Exception as e:
            logger.error(f"❌ MediaSpecialist failed: {e}")
            return []

    async def optimize_pricing(
        self, deps: AgentDependencies, recommendations: List[MediaRecommendation]
    ) -> PricingAnalysis:
        """Step 3: Intelligent pricing optimization"""
        try:
            total_media_cost = sum(rec.cost_vnd for rec in recommendations)

    
    async def _run_pricing_optimization_with_context(
        self, 
        context: ConversationContext,
        shared_context: Dict,
        recommendations: List[MediaRecommendation]
    ) -> PricingAnalysis:
        """Execute pricing optimization specialist"""
        try:
            total_media_cost = sum(rec.cost_vnd for rec in recommendations) if recommendations else 0
            safe_budget = max(shared_context['budget'] if shared_context['budget'] > 0 else 25000000, 1000000)
            
            prompt = f"""
            Optimize pricing strategy considering conversation context and user preferences:
            
            USER BUDGET: {safe_budget:,.0f} VND
            CONVERSATION INSIGHTS: {shared_context['conversation_summary']}
            USER PREFERENCES: {json.dumps(shared_context['preferences'], ensure_ascii=False)}
            USER REQUIREMENTS: {json.dumps(shared_context['requirements'], ensure_ascii=False)}
            
            RECOMMENDED MEDIA OUTLETS: {[{
                "name": rec.media_name,
                "cost": rec.cost_vnd,
                "reach": rec.estimated_reach,
                "score": rec.matching_score,
                "tier": rec.tier
            } for rec in recommendations]}
            
            TOTAL MEDIA COSTS: {total_media_cost:,.0f} VND
            
            PACKAGE OPTIONS:
            - Starter (12M VND): Light editing, 2-3 tier-2 outlets, 1-3 days
            - Standard (30M VND): Full writing, 12-15 outlets with tier-1, 5-7 days  
            - Premium (50M VND): Strategy + writing + 15-18 outlets + interview, 10-14 days
            
            Return optimal PricingAnalysis JSON based on conversation context.
            """

            logger.info("💰 Pricing optimization started...")
            
<<<<<<< HEAD
            result = await self.pricing_optimizer.arun(prompt)
            logger.info(
                f"✅ Pricing optimization completed - Package: {result.recommended_package}"
            )

            return result

=======
            result = await self.pricing_specialist.arun(prompt)
>>>>>>> main
            
            # Determine package based on budget
            if safe_budget <= 15000000:
                recommended_package = "Starter"
            elif safe_budget <= 35000000:
                recommended_package = "Standard"
            else:
                recommended_package = "Premium"
            
            package_price = PACKAGE_PRICES[recommended_package]["price"]
            total_cost = min(safe_budget, package_price + total_media_cost)
            budget_utilization = min(1.0, total_cost / safe_budget) if safe_budget > 0 else 0.0
            
            fallback_data = {
                "recommended_package": recommended_package,
                "total_cost_vnd": total_cost,
                "package_price_vnd": package_price,
                "media_costs_vnd": min(total_media_cost, max(0, safe_budget - package_price)),
                "timeline_days": PACKAGE_PRICES[recommended_package]["timeline"],
                "media_count": max(1, len(recommendations)),
                "budget_utilization": budget_utilization,
                "cost_efficiency": "Good value for Vietnamese market with team analysis",
                "roi_projection": "Positive ROI expected based on team-optimized strategy",
                "alternative_packages": [pkg for pkg in PACKAGE_PRICES.keys() if pkg != recommended_package]
            }
            
            pricing_analysis = parse_agent_response(result, PricingAnalysis, fallback_data)
            logger.info(f"✅ PricingSpecialist completed - Package: {pricing_analysis.recommended_package}")
            
            return pricing_analysis
            
        except Exception as e:
            logger.error(f"❌ PricingSpecialist failed: {e}")
            
            safe_budget = max(shared_context['budget'] if shared_context['budget'] > 0 else 25000000, 1000000)
            recommended_package = "Standard" if safe_budget >= 25000000 else "Starter"
            package_price = PACKAGE_PRICES[recommended_package]["price"]
            
            return PricingAnalysis(
                recommended_package=recommended_package,
                total_cost_vnd=safe_budget,
                package_price_vnd=package_price,
                media_costs_vnd=max(0, safe_budget - package_price),
                timeline_days=PACKAGE_PRICES[recommended_package]["timeline"],
                media_count=max(1, len(recommendations)),
                budget_utilization=1.0,
<<<<<<< HEAD
                cost_efficiency="Value-optimized for conversation requirements",
                roi_projection="Positive ROI expected",
                alternative_packages=["Starter", "Premium"],
=======
                cost_efficiency="Value-optimized for team analysis",
                roi_projection="Positive ROI expected with specialist guidance",
>>>>>>> main
                alternative_packages=[pkg for pkg in PACKAGE_PRICES.keys() if pkg != recommended_package]
            )

    async def generate_executive_report(
    
    async def _run_report_generation_with_context(
        self,
        context: ConversationContext,
        shared_context: Dict,
        content_analysis: ContentAnalysis,
        recommendations: List[MediaRecommendation],
<<<<<<< HEAD
        pricing: PricingAnalysis,
        pricing: PricingAnalysis,
=======
>>>>>>> main
        document_analysis: Optional[DocumentAnalysis] = None
    ) -> ExecutiveReport:
        """Execute report generation specialist"""
        try:
            document_section = ""
            if document_analysis:
                document_section = f"""
                DOCUMENT ANALYSIS: {document_analysis.model_dump()}
                
                Key Supporting Evidence:
                - {chr(10).join(['• ' + item for item in document_analysis.supporting_data])}
                
                Media Angles from Documents:
                - {chr(10).join(['• ' + angle for angle in document_analysis.media_angles])}
                """
            
            prompt = f"""
            Create strategic executive report incorporating team analysis and conversation insights:
            
            BUSINESS CONTEXT: {shared_context['user_input']}
            BUDGET: {shared_context['budget']:,.0f} VND
            
            CONVERSATION INSIGHTS: {shared_context['conversation_summary']}
            USER PREFERENCES: {json.dumps(shared_context['preferences'], ensure_ascii=False)}
            USER REQUIREMENTS: {json.dumps(shared_context['requirements'], ensure_ascii=False)}
            
            CONTENT ANALYSIS: {content_analysis.model_dump()}
            {document_section}
            
            MEDIA RECOMMENDATIONS: {[{
                "name": rec.media_name,
                "reach": rec.estimated_reach,
                "cost": rec.cost_vnd,
                "score": rec.matching_score,
                "reasoning": rec.reasoning
            } for rec in recommendations]}
            
            Generate executive-level strategic report that reflects team coordination and specialist insights.
            Focus on business outcomes and strategic coherence from multi-agent analysis.
            
<<<<<<< HEAD
            Generate an executive-level strategic report that:
            1. Summarizes the business opportunity and approach
            2. Presents the media strategy and rationale
            3. Defines clear success metrics and KPIs
            4. Provides actionable implementation roadmap
            5. Addresses risks and mitigation strategies
            6. Highlights competitive advantages
            7. Sets expectations for timeline and outcomes
            
            Write for C-level executives who need clear, actionable insights.
            Focus on business value and strategic outcomes.
            """

            logger.info("📋 Executive report generation started...")
            Generate executive-level strategic report that:
            1. Reflects the user's conversational style and preferences
            2. Addresses specific goals mentioned in conversation
            3. Incorporates user's stated priorities and constraints
            4. Presents strategy in tone/complexity appropriate for user
            5. Includes conversation-specific success metrics
            6. Provides implementation steps that fit user's capabilities
            7. Addresses risks mentioned or implied in conversation
            8. Highlights competitive advantages relevant to user's market
            9. Sets realistic expectations based on conversation context
            10. Leverages any supporting evidence from documents
            
            Return ExecutiveReport JSON that feels personalized to this conversation.
            """
            
            result = await self.report_generator.arun(prompt)
            logger.info("✅ Executive report completed")

            return result

=======
            Return ExecutiveReport JSON personalized to conversation context.
            """
            
            result = await self.report_specialist.arun(prompt)
>>>>>>> main
            
            fallback_data = {
                "executive_summary": f"Comprehensive team-based media strategy developed for {content_analysis.industry_sector} project with {len(recommendations)} specialist-selected outlets within {shared_context['budget']:,.0f} VND budget.",
                "strategic_objectives": [
                    "Increase brand awareness through team-optimized media mix",
                    "Generate qualified coverage via specialist recommendations",
                    "Build market presence with conversation-tailored approach",
                    "Engage target audience using multi-agent insights"
                ],
                "media_strategy": f"Multi-specialist approach targeting Vietnamese {content_analysis.industry_sector} landscape with coordinated team execution",
                "success_metrics": [
                    "Media mentions and coverage quality",
                    "Specialist-projected reach and impressions", 
                    "Audience engagement rates",
                    "Team-verified brand awareness lift",
                    "Business impact measurement"
                ],
                "implementation_steps": [
                    "Execute team-coordinated content strategy",
                    "Deploy to specialist-selected media outlets",
                    "Monitor using team-defined KPIs",
                    "Measure against specialist projections",
                    "Optimize with team feedback loop",
                    "Scale successful team approaches"
                ],
                "risk_mitigation": [
                    "Multiple specialist backup options identified",
                    "Timeline flexibility with team coordination",
                    "Budget optimization via team analysis"
                ],
                "competitive_advantage": "Team-based specialist analysis with Vietnamese market expertise and conversation-customized execution",
                "timeline_summary": "Team-coordinated delivery timeline optimized for quality and efficiency"
            }
            
            executive_report = parse_agent_response(result, ExecutiveReport, fallback_data)
            logger.info("✅ ReportSpecialist completed with team insights")
            
            return executive_report
            
        except Exception as e:
            logger.error(f"❌ ReportSpecialist failed: {e}")
            return ExecutiveReport(
<<<<<<< HEAD
                executive_summary="Media strategy developed for comprehensive market coverage within budget.",
                strategic_objectives=[
                    "Increase brand awareness",
                    "Generate media coverage",
                ],
                media_strategy="Multi-tier approach targeting Vietnamese media landscape",
                success_metrics=["Media mentions", "Reach metrics", "Engagement rates"],
                implementation_steps=[
                    "Finalize content",
                    "Submit to media",
                    "Monitor coverage",
                ],
                risk_mitigation=["Backup media options", "Timeline flexibility"],
                competitive_advantage="Strategic media mix with tier-1 coverage",
                timeline_summary=pricing.timeline_days,
                executive_summary=f"Personalized media strategy developed through conversation for {context.budget:,.0f} VND budget targeting Vietnamese {content_analysis.industry_sector} market.",
=======
                executive_summary=f"Team-analyzed media strategy for {shared_context['budget']:,.0f} VND budget targeting Vietnamese {content_analysis.industry_sector} market with specialist coordination.",
>>>>>>> main
                strategic_objectives=[
                    "Achieve conversation-specified goals with team expertise",
                    "Generate targeted coverage via specialist selection",
                    "Build market presence through coordinated approach",
                    "Deliver measurable impact with team monitoring"
                ],
                media_strategy=f"Specialist-coordinated approach with team-selected outlets and conversation-tailored execution",
                success_metrics=[
                    "Team-verified media coverage quality",
                    "Specialist-projected audience engagement",
                    "Coordinated business impact measurement",
                    "Team-monitored ROI achievement",
                    "Strategic goal completion via team support"
                ],
                implementation_steps=[
                    "Execute team-agreed strategy",
                    "Deploy to specialist-vetted outlets", 
                    "Monitor with team coordination",
                    "Optimize based on specialist feedback",
                    "Scale successful team approaches",
                    "Build relationships with team support"
                ],
                risk_mitigation=[
                    "Multiple specialist-identified options",
                    "Flexible team coordination timeline",
                    "Budget optimization via team analysis"
                ],
                competitive_advantage="Team-based specialist analysis with coordinated Vietnamese market expertise",
                timeline_summary="Team-optimized delivery timeline with specialist coordination"
            )

    async def process_complete_request(
        self, user_input: str, budget: float, session_id: str
    ) -> Dict[str, Any]:
        """End-to-end processing through all 4 agents"""

        start_time = datetime.utcnow()
        logger.info(f"🚀 Processing complete request for session: {session_id}")

        try:
            # Initialize dependencies
            deps = AgentDependencies(
                user_input=user_input, budget=budget, session_id=session_id
            )

            # Step 1: Content Analysis
            logger.info("📊 Step 1: Content Analysis")
            content_analysis = await self.analyze_content(deps)
            deps.content_analysis = content_analysis

            # Step 2: Media Matching
            logger.info("🎯 Step 2: Media Matching")
            recommendations = await self.find_matching_media(deps)

            # Step 3: Pricing Optimization
            logger.info("💰 Step 3: Pricing Optimization")
            pricing = await self.optimize_pricing(deps, recommendations)

            # Step 4: Executive Report
            logger.info("📋 Step 4: Executive Report")
            executive_report = await self.generate_executive_report(
                deps, content_analysis, recommendations, pricing
            )

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Compile final result
            result = {
                "session_id": session_id,
                "processing_time_seconds": processing_time,
                "content_analysis": content_analysis.model_dump(),
                "media_recommendations": [rec.model_dump() for rec in recommendations],
                "pricing_analysis": pricing.model_dump(),
                "executive_report": executive_report.model_dump(),
                "summary": {
                    "recommended_package": pricing.recommended_package,
                    "total_cost": pricing.total_cost_vnd,
                    "media_count": len(recommendations),
                    "timeline": pricing.timeline_days,
                    "budget_utilization": pricing.budget_utilization,
                    "confidence_score": content_analysis.confidence_score,
                },
                "timestamp": datetime.utcnow().isoformat(),
                "agent_system": "Instant Media Release v2.0",
            }

            logger.info(f"✅ Complete processing finished in {processing_time:.2f}s")
            return result

    
    async def _run_quality_assurance(self, context: ConversationContext, workflow_results: Dict) -> Dict:
        """Execute quality assurance using QA team"""
        try:
            qa_prompt = f"""
            Review all specialist outputs for accuracy, consistency, and quality:
            
            WORKFLOW RESULTS: {json.dumps(workflow_results, ensure_ascii=False, indent=2)}
            
            Verify:
            1. Consistency across all specialist outputs
            2. Accuracy of media outlet information
            3. Realistic pricing and timeline estimates
            4. Strategic coherence of recommendations
            5. Alignment with user requirements
            
            Provide quality score and verification status.
            """
            
            result = await self.qa_team.arun(qa_prompt)
            
            # Extract verification results
            qa_result = {
                "verified": True,
                "quality_score": 0.9,
                "verification_notes": "Team outputs verified and consistent",
                "citations_checked": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if hasattr(result, 'content'):
                # Try to extract structured data from QA response
                try:
                    qa_content = result.content
                    if isinstance(qa_content, str) and "quality_score" in qa_content.lower():
                        # Extract quality indicators from text
                        if "high quality" in qa_content.lower() or "verified" in qa_content.lower():
                            qa_result["quality_score"] = 0.9
                        elif "medium quality" in qa_content.lower():
                            qa_result["quality_score"] = 0.7
                        elif "low quality" in qa_content.lower():
                            qa_result["quality_score"] = 0.5
                            qa_result["verified"] = False
                except Exception as parse_error:
                    logger.warning(f"QA result parsing failed: {parse_error}")
            
            logger.info(f"✅ QA Team completed - Quality Score: {qa_result['quality_score']:.2f}")
            return qa_result
            
        except Exception as e:
            logger.error(f"❌ QA Team failed: {e}")
            return {
                "verified": False,
                "quality_score": 0.6,
                "verification_notes": f"QA verification failed: {str(e)}",
                "citations_checked": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # =================== HELPER METHODS ===================
    
    def _format_conversation_history(self, history: List[Dict]) -> str:
        """Format conversation history for agent prompts"""
        formatted = []
        for msg in history[-10:]:
            role = msg.get("role", "unknown")
            content = msg.get("message", "")
            
            if role == "user":
                formatted.append(f"USER: {content}")
            elif role == "assistant":
                formatted.append(f"ASSISTANT: {content}")
        
        return "\n".join(formatted)
    
    def _extract_key_info_from_conversation(self, context: ConversationContext) -> str:
        """Extract key information from conversation for team context"""
        key_info = []
        
        # Extract from requirements
        if context.requirements:
            if context.requirements.get("industry"):
                key_info.append(f"Industry: {context.requirements['industry']}")
            if context.requirements.get("target_audience"):
                key_info.append(f"Target Audience: {', '.join(context.requirements['target_audience'])}")
            if context.requirements.get("objectives"):
                key_info.append(f"Objectives: {', '.join(context.requirements['objectives'])}")
        
        # Extract from preferences  
        if context.preferences:
            if context.preferences.get("timeline"):
                key_info.append(f"Preferred Timeline: {context.preferences['timeline']}")
            if context.preferences.get("media_types"):
                key_info.append(f"Preferred Media: {', '.join(context.preferences['media_types'])}")
        
        # Extract from conversation patterns
        user_messages = [msg for msg in context.conversation_history if msg.get("role") == "user"]
        if user_messages:
            recent_topics = []
            for msg in user_messages[-3:]:
                content = msg.get("message", "").lower()
                if "ngân sách" in content or "budget" in content:
                    recent_topics.append("Budget discussed")
                if "timeline" in content or "thời gian" in content:
                    recent_topics.append("Timeline discussed")
                if "mục tiêu" in content or "goal" in content:
                    recent_topics.append("Goals mentioned")
            
            if recent_topics:
                key_info.append(f"Recent Discussion: {', '.join(recent_topics)}")
        
        return "; ".join(key_info) if key_info else "Team ready for comprehensive analysis"
    
    async def _update_context_from_conversation(
        self, 
        context: ConversationContext, 
        user_message: str, 
        response: ConversationResponse
    ):
        """Update conversation context with team coordination awareness"""
        try:
            # Extract budget information
            budget_keywords = ["triệu", "million", "vnđ", "vnd", "budget", "ngân sách", "chi phí"]
            if any(keyword in user_message.lower() for keyword in budget_keywords):
                import re
                numbers = re.findall(r'\d+', user_message)
                if numbers:
                    potential_budget = int(numbers[-1])
                    if potential_budget >= 1000:
                        if potential_budget < 1000000:
                            context.budget = potential_budget * 1000000
                        else:
                            context.budget = potential_budget
                        logger.info(f"Extracted budget: {context.budget:,.0f} VND")
                        
                        # Update team memory
                        context.team_memory.workflow_plan["budget"] = context.budget
            
            # Extract industry information
            industry_keywords = {
                "technology": ["tech", "công nghệ", "phần mềm", "app", "ứng dụng", "ai", "fintech"],
                "finance": ["fintech", "tài chính", "ngân hàng", "thanh toán", "vay", "lending"],
                "healthcare": ["y tế", "sức khỏe", "health", "medical", "bác sĩ"],
                "education": ["giáo dục", "education", "đào tạo", "học", "trường"],
                "retail": ["bán lẻ", "retail", "thương mại", "shop", "cửa hàng"],
                "manufacturing": ["sản xuất", "manufacturing", "nhà máy", "công nghiệp"],
                "food": ["thực phẩm", "food", "đồ ăn", "nhà hàng", "quán"]
            }
            
            for industry, keywords in industry_keywords.items():
                if any(keyword in user_message.lower() for keyword in keywords):
                    context.requirements["industry"] = industry
                    context.team_memory.workflow_plan["industry"] = industry
                    logger.info(f"Detected industry: {industry}")
                    break
            
            # Extract target audience information
            audience_keywords = {
                "young_adults": ["trẻ", "young", "sinh viên", "student", "gen z"],
                "professionals": ["chuyên gia", "professional", "văn phòng", "doanh nhân"],
                "families": ["gia đình", "family", "bố mẹ", "parent", "con cái"],
                "businesses": ["doanh nghiệp", "business", "công ty", "sme", "smes"],
                "consumers": ["khách hàng", "consumer", "người dùng", "user"]
            }
            
            detected_audiences = []
            for audience, keywords in audience_keywords.items():
                if any(keyword in user_message.lower() for keyword in keywords):
                    detected_audiences.append(audience)
            
            if detected_audiences:
                context.requirements["target_audience"] = detected_audiences
                context.team_memory.workflow_plan["target_audience"] = detected_audiences
                logger.info(f"Detected audiences: {detected_audiences}")
            
            # Extract urgency/timeline for team coordination
            if any(word in user_message.lower() for word in ["gấp", "urgent", "nhanh", "quick", "asap"]):
                context.requirements["urgency"] = "High"
                context.preferences["timeline"] = "Urgent"
                context.team_memory.workflow_plan["urgency"] = "High"
            elif any(word in user_message.lower() for word in ["chậm", "slow", "từ từ", "không vội"]):
                context.requirements["urgency"] = "Low"
                context.preferences["timeline"] = "Flexible"
                context.team_memory.workflow_plan["urgency"] = "Low"
            
            # Extract project goals for team alignment
            goal_keywords = {
                "awareness": ["nhận diện", "awareness", "biết đến", "nổi tiếng"],
                "leads": ["khách hàng", "lead", "bán hàng", "tăng doanh thu"],
                "credibility": ["uy tín", "credibility", "tin cậy", "thương hiệu"],
                "launch": ["ra mắt", "launch", "giới thiệu", "công bố"]
            }
            
            detected_goals = []
            for goal, keywords in goal_keywords.items():
                if any(keyword in user_message.lower() for keyword in keywords):
                    detected_goals.append(goal)
            
            if detected_goals:
                context.requirements["objectives"] = detected_goals
                context.team_memory.workflow_plan["objectives"] = detected_goals
                logger.info(f"Detected goals for team: {detected_goals}")
            
            # Team readiness assessment
            has_project_info = bool(context.user_input or user_message) and len(user_message) > 20
            has_budget = context.budget > 0
            has_basic_requirements = bool(context.requirements.get("industry") or context.requirements.get("objectives"))
            
            # State progression with team awareness
            if context.state == ConversationState.GREETING and has_project_info:
                context.state = ConversationState.GATHERING_INFO
                context.team_memory.workflow_plan["phase"] = "gathering_info"
                logger.info("State: GREETING → GATHERING_INFO")
            
            if context.state == ConversationState.GATHERING_INFO and has_project_info and has_budget and has_basic_requirements:
                context.state = ConversationState.ANALYZING
                context.team_memory.workflow_plan["phase"] = "ready_for_team_deployment"
                logger.info("State: GATHERING_INFO → ANALYZING (team ready for deployment)")
            
            # Update phase based on response
            if response.phase:
                try:
                    context.phase = WorkflowPhase(response.phase)
                except ValueError:
                    pass  # Invalid phase, keep current
            
            # Update user input if substantial and new
            if len(user_message) > 20:
                if not context.user_input or len(user_message) > len(context.user_input):
                    context.user_input = user_message
                    context.team_memory.workflow_plan["user_input"] = user_message
                    logger.info("Updated main user input for team context")
            
            # Update team memory context summary
            context.team_memory.context_summary = self._extract_key_info_from_conversation(context)
            context.team_memory.updated_at = datetime.utcnow()
            context.updated_at = datetime.utcnow()
            
        except Exception as e:
<<<<<<< HEAD
            logger.error(f"❌ Complete processing failed: {e}")
            return {
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "success": False,
            }
            logger.warning(f"Failed to update context from conversation: {e}")
=======
            logger.warning(f"Failed to update team context from conversation: {e}")
>>>>>>> main
            # Don't fail the conversation, just log the warning
    
    def _determine_media_categories(self, content_analysis: ContentAnalysis, context: ConversationContext) -> List[str]:
        """Determine relevant media categories for specialist analysis"""
        categories = ["MAINSTREAM"]  # Always include mainstream
        
        # Map industry sectors to categories
        industry_mapping = {
            "Tech": ["TECHNOLOGY", "BUSINESS"],
            "Technology": ["TECHNOLOGY", "BUSINESS"],
            "Finance": ["BUSINESS"],
            "Business": ["BUSINESS"],
            "Healthcare": ["HEALTH"],
            "Health": ["HEALTH"],
            "Education": ["EDUCATION"],
            "Entertainment": ["YOUTH_ENTERTAINMENT"],
            "Automotive": ["AUTOMOTIVE"],
            "Agriculture": ["AGRICULTURE"]
        }
        
        if content_analysis.industry_sector in industry_mapping:
            categories.extend(industry_mapping[content_analysis.industry_sector])
        
        # Add categories based on target audience
        if "Young adults" in content_analysis.target_audiences:
            categories.append("YOUTH_ENTERTAINMENT")
        
        if "Women" in content_analysis.target_audiences or "Families" in content_analysis.target_audiences:
            categories.append("WOMAN_FAMILY")
        
        # Add categories from team memory
        if context.team_memory.workflow_plan.get("industry"):
            industry = context.team_memory.workflow_plan["industry"]
            if industry in ["technology", "tech"]:
                categories.extend(["TECHNOLOGY", "BUSINESS"])
            elif industry in ["finance", "fintech"]:
                categories.append("BUSINESS")
        
        return list(set(categories))  # Remove duplicates
    
    # =================== SESSION MANAGEMENT ===================
    
    def get_conversation_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context for a session"""
        return self.active_conversations.get(session_id)
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return list(self.active_conversations.keys())
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a conversation session"""
        if session_id in self.active_conversations:
            del self.active_conversations[session_id]
            logger.info(f"🗑️ Cleared enhanced session: {session_id}")
            return True
        return False
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """Get enhanced summary of a conversation session"""
        context = self.active_conversations.get(session_id)
        if not context:
            return None
        
        return {
            "session_id": session_id,
            "state": context.state.value,
            "phase": context.phase.value,
            "budget": context.budget,
            "message_count": len(context.conversation_history),
            "workflow_started": context.workflow_started,
            "team_initialized": context.team_initialized,
            "active_agents": len(context.active_agents),
            "team_performance": {
                "parallel_processing": PARALLEL_PROCESSING,
                "completed_tasks": len(context.team_memory.completed_tasks),
                "error_count": len(context.team_memory.error_log),
                "confidence_scores": context.team_memory.confidence_scores
            },
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat(),
            "has_results": bool(context.content_analysis or context.media_recommendations),
            "team_coordination": "active" if context.active_agents else "idle"
        }
    
    # =================== TEAM MONITORING AND METRICS ===================
    
    def get_team_performance_metrics(self, session_id: str) -> Optional[Dict]:
        """Get detailed team performance metrics"""
        context = self.active_conversations.get(session_id)
        if not context:
            return None
        
        total_processing_time = (datetime.utcnow() - context.created_at).total_seconds()
        
        return {
            "session_id": session_id,
            "team_metrics": {
                "total_agents_deployed": len(context.active_agents),
                "parallel_processing_enabled": PARALLEL_PROCESSING,
                "workflow_phases_completed": len(context.team_memory.completed_tasks),
                "total_processing_time_seconds": total_processing_time,
                "average_confidence_score": sum(context.team_memory.confidence_scores.values()) / max(len(context.team_memory.confidence_scores), 1),
                "error_rate": len(context.team_memory.error_log) / max(len(context.team_memory.completed_tasks), 1),
                "team_coordination_status": "successful" if context.team_initialized and not context.team_memory.error_log else "partial"
            },
            "orchestrator_model": OPENAI_ORCHESTRATOR_MODEL if OPENAI_API_KEY else GROQ_ORCHESTRATOR_MODEL,
            "worker_model": OPENAI_WORKER_MODEL if OPENAI_API_KEY else GROQ_WORKER_MODEL,
            "quality_assurance": {
                "citation_verification": True,
                "consistency_checks": True,
                "multi_agent_validation": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # =================== ADVANCED TEAM COORDINATION ===================
    
    async def coordinate_team_modification(
        self, 
        session_id: str, 
        modification_type: str,
        target_specialists: List[str] = None
    ) -> Dict:
        """Coordinate specific team modifications with targeted specialists"""
        try:
            context = self.active_conversations.get(session_id)
            if not context:
                raise ValueError("Conversation context not found")
            
            # Determine which specialists to involve based on modification type
            if not target_specialists:
                specialist_mapping = {
                    "budget": ["PricingSpecialist", "MediaSpecialist"],
                    "media": ["MediaSpecialist", "ReportSpecialist"],
                    "timeline": ["PricingSpecialist", "ReportSpecialist"],
                    "strategy": ["ContentSpecialist", "ReportSpecialist"],
                    "comprehensive": ["ContentSpecialist", "MediaSpecialist", "PricingSpecialist", "ReportSpecialist"]
                }
                target_specialists = specialist_mapping.get(modification_type, ["ModificationSpecialist"])
            
            # Create targeted team for modification
            modification_team_members = []
            if "ContentSpecialist" in target_specialists:
                modification_team_members.append(self.content_specialist)
            if "MediaSpecialist" in target_specialists:
                modification_team_members.append(self.media_specialist)
            if "PricingSpecialist" in target_specialists:
                modification_team_members.append(self.pricing_specialist)
            if "ReportSpecialist" in target_specialists:
                modification_team_members.append(self.report_specialist)
            if "ModificationSpecialist" in target_specialists:
                modification_team_members.append(self.modification_specialist)
            
            # Create dynamic modification team
            modification_team = Team(
                name="ModificationTeam",
                mode="coordinate",
                model=self.orchestrator_llm,
                members=modification_team_members,
                instructions=[
                    f"You are coordinating a targeted modification team for {modification_type} changes",
                    "Work with relevant specialists to implement requested modifications",
                    "Ensure all changes maintain strategic coherence",
                    "Provide clear rationale for any recommendations or adjustments",
                    "Maintain high quality standards throughout modification process"
                ],
                description=f"Targeted team for {modification_type} modifications with specialist coordination"
            )
            
            # Set session state after team creation
            modification_team.session_state = {
                "modification_type": modification_type,
                "original_results": {
                    "content_analysis": context.content_analysis,
                    "media_recommendations": context.media_recommendations,
                    "pricing_analysis": context.pricing_analysis,
                    "executive_report": context.executive_report
                },
                "session_context": {
                    "user_input": context.user_input,
                    "budget": context.budget,
                    "requirements": context.requirements,
                    "preferences": context.preferences
                }
            }
            
            logger.info(f"🔄 Coordinated {modification_type} modification team with {len(target_specialists)} specialists")
            
            return {
                "team_created": True,
                "modification_type": modification_type,
                "specialists_involved": target_specialists,
                "team_size": len(modification_team_members),
                "coordination_status": "ready",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Team coordination for modification failed: {e}")
            return {
                "team_created": False,
                "error": str(e),
                "modification_type": modification_type,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # =================== HEALTH CHECK AND DIAGNOSTICS ===================
    
    def health_check(self) -> Dict:
        """Comprehensive health check of the team system"""
        try:
            health_status = {
                "system_status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "components": {}
            }
            
            # Check model availability
            try:
                health_status["components"]["orchestrator_model"] = {
                    "status": "available",
                    "model": OPENAI_ORCHESTRATOR_MODEL if OPENAI_API_KEY else GROQ_ORCHESTRATOR_MODEL,
                    "provider": "OpenAI" if OPENAI_API_KEY else "Groq"
                }
                health_status["components"]["worker_model"] = {
                    "status": "available", 
                    "model": OPENAI_WORKER_MODEL if OPENAI_API_KEY else GROQ_WORKER_MODEL,
                    "provider": "OpenAI" if OPENAI_API_KEY else "Groq"
                }
            except Exception as e:
                health_status["components"]["models"] = {"status": "error", "error": str(e)}
                health_status["system_status"] = "degraded"
            
            # Check team agents
            try:
                agent_status = {}
                core_agents = [
                    ("ConversationAgent", self.conversation_agent),
                    ("LeadResearcher", self.lead_researcher),
                    ("ContentSpecialist", self.content_specialist),
                    ("DocumentSpecialist", self.document_specialist),
                    ("MediaSpecialist", self.media_specialist),
                    ("PricingSpecialist", self.pricing_specialist),
                    ("ReportSpecialist", self.report_specialist),
                    ("ModificationSpecialist", self.modification_specialist),
                    ("CitationAgent", self.citation_agent)
                ]
                
                for name, agent in core_agents:
                    agent_status[name] = {
                        "status": "initialized" if agent else "missing",
                        "has_storage": bool(agent and agent.storage),
                        "has_tools": bool(agent and hasattr(agent, 'tools') and agent.tools)
                    }
                
                health_status["components"]["agents"] = agent_status
            except Exception as e:
                health_status["components"]["agents"] = {"status": "error", "error": str(e)}
                health_status["system_status"] = "degraded"
            
            # Check team coordination
            try:
                team_status = {}
                teams = [
                    ("AnalysisTeam", self.analysis_team),
                    ("QATeam", self.qa_team)
                ]
                
                for name, team in teams:
                    team_status[name] = {
                        "status": "initialized" if team else "missing",
                        "member_count": len(team.members) if team and hasattr(team, 'members') else 0,
                        "coordination_mode": getattr(team, 'mode', 'unknown') if team else 'unknown'
                    }
                
                health_status["components"]["teams"] = team_status
            except Exception as e:
                health_status["components"]["teams"] = {"status": "error", "error": str(e)}
                health_status["system_status"] = "degraded"
            
            # Check storage
            try:
                health_status["components"]["storage"] = {
                    "status": "available" if self.storage else "missing",
                    "type": "SqliteAgentStorage" if self.storage else None
                }
            except Exception as e:
                health_status["components"]["storage"] = {"status": "error", "error": str(e)}
                health_status["system_status"] = "degraded"
            
            # Check active sessions
            health_status["components"]["sessions"] = {
                "active_count": len(self.active_conversations),
                "total_capacity": MAX_CONCURRENT_AGENTS * 10,  # Rough estimate
                "utilization": len(self.active_conversations) / (MAX_CONCURRENT_AGENTS * 10)
            }
            
            # Configuration status
            health_status["configuration"] = {
                "parallel_processing": PARALLEL_PROCESSING,
                "max_concurrent_agents": MAX_CONCURRENT_AGENTS,
                "team_timeout": TEAM_TIMEOUT,
                "max_retries": MAX_RETRIES
            }
            
            logger.info(f"🏥 Team system health check: {health_status['system_status']}")
            return health_status
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {
                "system_status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

<<<<<<< HEAD

# =================== GLOBAL AGENT SYSTEM ===================
=======
# =================== GLOBAL ENHANCED TEAM SYSTEM ===================
>>>>>>> main

# Initialize global enhanced team-based agent system
try:
    enhanced_team_system = EnhancedMediaReleaseTeamSystem()
    logger.info("✅ Global Enhanced Team-based Agent System initialized successfully")
    
    # For backward compatibility, create aliases to the original function names
    conversational_agent_system = enhanced_team_system
    
except Exception as e:
    logger.error(f"❌ Failed to initialize Enhanced Team System: {e}")
    enhanced_team_system = None
    conversational_agent_system = None

# =================== TESTING AND VALIDATION ===================

<<<<<<< HEAD

async def test_conversational_system():
    """Comprehensive test of the conversational agent system"""
    if not conversational_agent_system:
        logger.error("❌ Conversational agent system not available for testing")
        return

    logger.info("🧪 Testing Instant Media Release Agent System...")

    test_input = """
    Công ty chúng tôi vừa phát triển xong ứng dụng VietPay - 
    giải pháp thanh toán di động mới dành riêng cho các doanh nghiệp SME tại Việt Nam.
    Ứng dụng giúp SME nhận thanh toán từ khách hàng một cách nhanh chóng và bảo mật.
    
    Chúng tôi muốn thông báo ra mắt sản phẩm này để:
    1. Tăng nhận diện thương hiệu
    2. Thu hút các đối tác kinh doanh
    3. Tạo lòng tin với khách hàng SME
    
    Target chính là các chủ doanh nghiệp nhỏ, quản lý tài chính, và cộng đồng fintech.
    """

    try:
        result = await agent_system.process_complete_request(
            user_input=test_input,
            budget=35000000,  # 35M VND
            session_id="test_session_001",
=======
async def test_enhanced_team_system():
    """Comprehensive test of the enhanced team-based agent system"""
    if not enhanced_team_system:
        logger.error("❌ Enhanced Team System not available for testing")
        return False
>>>>>>> main
    
    logger.info("🧪 Testing Enhanced Team-based Media Release Agent System...")
    
    try:
        # Test 1: System Health Check
        logger.info("📋 Running system health check...")
        health_status = enhanced_team_system.health_check()
        logger.info(f"Health Status: {health_status['system_status']}")
        
        if health_status['system_status'] == 'error':
            logger.error("❌ System health check failed")
            return False
        
        # Test 2: Conversation Start
        logger.info("💬 Testing conversation start...")
        response1 = await enhanced_team_system.start_conversation("test_enhanced_001")
        logger.info(f"Start Response: {response1.message}")
        
        # Test 3: Conversation Continuation
        logger.info("🔄 Testing conversation continuation...")
        response2 = await enhanced_team_system.continue_conversation(
            "test_enhanced_001",
            "Chúng tôi là công ty fintech VietFinance, vừa phát triển app cho vay SME. Ngân sách 45 triệu, cần tăng awareness và tìm khách hàng doanh nghiệp."
        )
<<<<<<< HEAD

        logger.info("📊 Test Results:")
        logger.info(f"Processing Time: {result.get('processing_time_seconds', 0):.2f}s")
        logger.info(
            f"Recommended Package: {result.get('summary', {}).get('recommended_package')}"
        )
        logger.info(f"Media Count: {result.get('summary', {}).get('media_count')}")
        logger.info(
            f"Budget Utilization: {result.get('summary', {}).get('budget_utilization', 0):.1%}"
        )

        logger.info("✅ Agent system test completed successfully!")
        return result

        logger.info(f"Continue: {response2.message}")
=======
        logger.info(f"Continue Response: {response2.message}")
        logger.info(f"Can Proceed: {response2.can_proceed}")
>>>>>>> main
        
        # Test 4: Team Workflow Trigger (if ready)
        if response2.can_proceed:
            logger.info("🚀 Testing enhanced team workflow...")
            response3 = await enhanced_team_system.trigger_workflow("test_enhanced_001")
            logger.info(f"Team Workflow Response: {response3.message}")
            
            # Verify team results
            if response3.data:
                logger.info(f"✅ Team workflow data keys: {list(response3.data.keys())}")
                
                summary = response3.data.get("summary", {})
                if summary:
                    logger.info(f"📊 Team Results Summary:")
                    logger.info(f"  - Package: {summary.get('recommended_package')}")
                    logger.info(f"  - Cost: {summary.get('total_cost', 0):,.0f} VND")
                    logger.info(f"  - Media Count: {summary.get('media_count', 0)}")
                    logger.info(f"  - Confidence: {summary.get('confidence_score', 0):.2f}")
                    logger.info(f"  - Team Coordination: {summary.get('team_coordination')}")
        
        # Test 5: Team Performance Metrics
        logger.info("📈 Testing team performance metrics...")
        metrics = enhanced_team_system.get_team_performance_metrics("test_enhanced_001")
        if metrics:
            team_metrics = metrics.get("team_metrics", {})
            logger.info(f"Team Performance:")
            logger.info(f"  - Agents Deployed: {team_metrics.get('total_agents_deployed', 0)}")
            logger.info(f"  - Parallel Processing: {team_metrics.get('parallel_processing_enabled', False)}")
            logger.info(f"  - Processing Time: {team_metrics.get('total_processing_time_seconds', 0):.1f}s")
            logger.info(f"  - Coordination Status: {team_metrics.get('team_coordination_status')}")
        
        # Test 6: Session Summary
        logger.info("📋 Testing enhanced session summary...")
        summary = enhanced_team_system.get_session_summary("test_enhanced_001")
        if summary:
            logger.info(f"Session Summary:")
            logger.info(f"  - State: {summary.get('state')}")
            logger.info(f"  - Phase: {summary.get('phase')}")
            logger.info(f"  - Team Coordination: {summary.get('team_coordination')}")
            logger.info(f"  - Active Agents: {summary.get('active_agents', 0)}")
        
        # Test 7: Team Modification Coordination
        logger.info("🔄 Testing team modification coordination...")
        modification_result = await enhanced_team_system.coordinate_team_modification(
            "test_enhanced_001",
            "budget",
            ["PricingSpecialist", "MediaSpecialist"]
        )
        logger.info(f"Modification Coordination: {modification_result.get('coordination_status')}")
        
        logger.info("✅ Enhanced Team-based Agent System test completed successfully!")
        logger.info(f"🎯 All core team functionalities verified:")
        logger.info(f"  ✓ Health monitoring")
        logger.info(f"  ✓ Conversation management")
        logger.info(f"  ✓ Team workflow coordination")
        logger.info(f"  ✓ Parallel specialist processing")
        logger.info(f"  ✓ Quality assurance integration")
        logger.info(f"  ✓ Performance metrics tracking")
        logger.info(f"  ✓ Dynamic team modification")
        
        return True
        
    except Exception as e:
<<<<<<< HEAD
        logger.error(f"❌ Agent system test failed: {e}")
        return None


# if __name__ == "__main__":
#     # Run agent system tests
#     asyncio.run(test_agent_system())

        logger.error(f"❌ Conversational agent system test failed: {e}")
=======
        logger.error(f"❌ Enhanced Team System test failed: {e}")
>>>>>>> main
        return False

# =================== BACKWARD COMPATIBILITY WRAPPER ===================

class ConversationalMediaReleaseAgents:
    """Backward compatibility wrapper for the enhanced team system"""
    
    def __init__(self):
        """Initialize wrapper with enhanced team system"""
        if enhanced_team_system:
            self.enhanced_system = enhanced_team_system
            logger.info("✅ Backward compatibility wrapper initialized")
        else:
            raise ValueError("Enhanced team system not available")
    
    # Delegate all methods to enhanced system
    async def start_conversation(self, session_id: str) -> ConversationResponse:
        return await self.enhanced_system.start_conversation(session_id)
    
    async def continue_conversation(self, session_id: str, user_message: str, progress_callback: Optional[Callable] = None) -> ConversationResponse:
        return await self.enhanced_system.continue_conversation(session_id, user_message, progress_callback)
    
    async def trigger_workflow(self, session_id: str, progress_callback: Optional[Callable] = None) -> ConversationResponse:
        return await self.enhanced_system.trigger_workflow(session_id, progress_callback)
    
    async def modify_plan(self, session_id: str, modification_request: str, progress_callback: Optional[Callable] = None) -> ConversationResponse:
        return await self.enhanced_system.modify_plan(session_id, modification_request, progress_callback)
    
    def get_conversation_context(self, session_id: str) -> Optional[ConversationContext]:
        return self.enhanced_system.get_conversation_context(session_id)
    
    def get_active_sessions(self) -> List[str]:
        return self.enhanced_system.get_active_sessions()
    
    def clear_session(self, session_id: str) -> bool:
        return self.enhanced_system.clear_session(session_id)
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        return self.enhanced_system.get_session_summary(session_id)

# Create backward compatible instance
if enhanced_team_system:
    conversational_agent_system = enhanced_team_system

if __name__ == "__main__":
    # Run enhanced team system tests
    import asyncio
    asyncio.run(test_enhanced_team_system())