"""
Instant Media Release - Conversational Multi-Agent System
Advanced interactive AI agents with real-time user collaboration
Enhanced with state management and workflow coordination
"""

import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.agent.sqlite import SqliteAgentStorage
from agno.tools.duckduckgo import DuckDuckGoTools
from pydantic import BaseModel, Field
from loguru import logger

from database import media_db
from document_processor import get_document_processor

# =================== CONFIGURATION ===================

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))

# Groq Configuration (Alternative)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Agent Configuration
AGENT_TIMEOUT = int(os.getenv("AGENT_TIMEOUT_SECONDS", "120"))
MAX_RETRIES = int(os.getenv("MAX_AGENT_RETRIES", "3"))
PARALLEL_PROCESSING = os.getenv("AGENT_PARALLEL_PROCESSING", "true").lower() == "true"

# Business Configuration
PACKAGE_PRICES = {
    "Starter": {
        "price": int(os.getenv("STARTER_PACKAGE_PRICE", "12000000")),
        "media_count": int(os.getenv("STARTER_MEDIA_COUNT", "3")),
        "timeline": "1-3 ngày làm việc",
        "features": ["Chỉnh sửa nhẹ nội dung", "2-3 báo tier-2", "Báo cáo cơ bản"]
    },
    "Standard": {
        "price": int(os.getenv("STANDARD_PACKAGE_PRICE", "30000000")),
        "media_count": int(os.getenv("STANDARD_MEDIA_COUNT", "15")),
        "timeline": "5-7 ngày làm việc",
        "features": ["Viết bài hoàn chỉnh", "12-15 báo bao gồm tier-1", "Báo cáo chi tiết"]
    },
    "Premium": {
        "price": int(os.getenv("PREMIUM_PACKAGE_PRICE", "50000000")),
        "media_count": int(os.getenv("PREMIUM_MEDIA_COUNT", "18")),
        "timeline": "10-14 ngày làm việc", 
        "features": ["Chiến lược + viết bài", "15-18 báo + phỏng vấn", "Social media"]
    }
}

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

# =================== STRUCTURED OUTPUT MODELS ===================

# class ConversationResponse(BaseModel):
#     """Structured conversation response"""
#     message: str = Field(description="Response message to user")
#     state: str = Field(description="Current conversation state")
#     phase: str = Field(description="Current workflow phase")
#     suggestions: List[str] = Field(description="Suggested user actions", default=[])
#     options: List[str] = Field(description="Available options for user", default=[])
#     progress: Optional[Dict] = Field(description="Progress information", default=None)
#     data: Optional[Dict] = Field(description="Additional data", default=None)
#     requires_input: bool = Field(description="Whether user input is required", default=True)
#     can_proceed: bool = Field(description="Whether workflow can proceed", default=False)

class ConversationResponse(BaseModel):
    """
    Structured conversation response for Vietnamese PR consultation chatbot.
    This model defines the exact JSON format that AI agents MUST return.
    """
    
    message: str = Field(
        description="""
        Main conversational response message to user in Vietnamese.
        Should be natural, helpful, and contextually appropriate.
        Examples: 
        - 'Cảm ơn bạn đã chia sẻ! Fintech cho SME là lĩnh vực rất tiềm năng...'
        - 'Tuyệt vời! Với ngân sách 30 triệu, chúng ta có nhiều lựa chọn hiệu quả...'
        - 'Tôi hiểu bạn muốn tăng awareness. Bạn có thể chia sẻ thêm về...'
        Length: 50-300 characters for optimal user experience.
        """
    )
    
    state: str = Field(
        description="""
        Current conversation state representing user journey progress.
        VALID VALUES ONLY:
        - 'greeting': Initial welcome, getting basic info
        - 'gathering_info': Collecting project details, budget, requirements  
        - 'analyzing': Ready to process, confirming final details
        - 'planning': AI agents working on strategy
        - 'confirming': Showing results, waiting for user approval
        - 'executing': Implementing approved plan
        - 'reviewing': User reviewing recommendations
        - 'modifying': User requesting changes to plan
        - 'completed': Process finished successfully
        - 'error': Something went wrong, need to restart/fix
        """
    )
    
    phase: str = Field(
        description="""
        Current workflow execution phase (more granular than state).
        VALID VALUES ONLY:
        - 'idle': No active processing
        - 'content_analysis': AI analyzing user input and requirements
        - 'document_analysis': Processing uploaded files (PDF/DOC)
        - 'media_matching': Finding suitable Vietnamese media outlets
        - 'pricing_optimization': Calculating optimal package (Starter/Standard/Premium)
        - 'report_generation': Creating executive strategy report
        - 'user_review': Waiting for user feedback on recommendations
        - 'plan_modification': Adjusting plan based on user feedback
        """
    )
    
    suggestions: List[str] = Field(
        description="""
        Clickable suggestion buttons to guide user conversation.
        Should be 3-5 short, actionable phrases in Vietnamese.
        Examples:
        - ['Mô tả sản phẩm chi tiết', 'Chia sẻ về khách hàng mục tiêu', 'Nói về ngân sách']
        - ['Tăng awareness thương hiệu', 'Thu hút khách hàng mới', 'Xây dựng uy tín']
        - ['Báo tier-1 (VnExpress, 24H)', 'Báo chuyên ngành', 'Báo địa phương']
        Each suggestion: 20-50 characters, clear call-to-action.
        """,
        default=[]
    )
    
    options: List[str] = Field(
        description="""
        Available action options for user at current stage.
        Different from suggestions - these are more formal choices.
        Examples:
        - ['Bắt đầu phân tích AI', 'Tải lên tài liệu', 'Thay đổi ngân sách']
        - ['Phê duyệt kế hoạch', 'Điều chỉnh danh sách báo', 'Thảo luận thêm']
        - ['Gói Starter (12M)', 'Gói Standard (30M)', 'Gói Premium (50M)']
        Use when user needs to make specific decisions.
        """,
        default=[]
    )
    
    progress: Optional[Dict] = Field(
        description="""
        Progress information for ongoing AI processing (optional).
        Structure when provided:
        {
            'step': 'Current step name',
            'completed': number_of_completed_steps,
            'total': total_number_of_steps,
            'percentage': completion_percentage_0_to_100,
            'message': 'User-friendly progress message'
        }
        Only include when state='planning' or phase involves AI agent processing.
        """,
        default=None
    )
    
    data: Optional[Dict] = Field(
        description="""
        Additional structured data for frontend (optional).
        Common use cases:
        - User profile data: {'budget': 30000000, 'industry': 'fintech'}
        - Results summary: {'recommended_media': 5, 'total_cost': 25000000}
        - Workflow results: Complete AI agent analysis results
        - Error details: {'error_type': 'validation', 'field': 'budget'}
        Only include when frontend needs specific data for display/processing.
        """,
        default=None
    )
    
    requires_input: bool = Field(
        description="""
        Whether system is waiting for user input to continue.
        - True: User must respond/interact before next step (default)
        - False: System can proceed automatically (rare cases)
        Examples:
        - True: After asking question, showing options, requesting approval
        - False: During AI processing, automatic redirects, completion messages
        """,
        default=True
    )
    
    can_proceed: bool = Field(
        description="""
        Whether system has enough information to trigger AI workflow.
        Critical for determining when to show 'Bắt đầu phân tích AI' button.
        
        Requirements for True:
        - Have project description (user_input length > 20 chars)
        - Have budget information (budget > 0)
        - Have basic requirements (industry OR objectives identified)
        - State should be 'analyzing' or later
        
        When True: Show workflow trigger button, enable advanced features
        When False: Continue gathering information, show guidance
        """,
        default=False
    )

class ContentAnalysis(BaseModel):
    """Structured output for content analysis agent"""
    language: str = Field(description="Detected language: Vietnamese/English/Both")
    primary_topics: List[str] = Field(description="Main topics/categories (max 5)")
    target_audiences: List[str] = Field(description="Identified target audiences (max 4)")
    keywords: List[str] = Field(description="Key search terms (max 10)")
    content_tone: str = Field(description="Professional/Technical/Casual/Formal")
    urgency_level: str = Field(description="Low/Medium/High")
    industry_sector: str = Field(description="Main industry: Tech/Finance/Healthcare/etc")
    press_release_type: str = Field(description="Product Launch/Partnership/Funding/Event/Other")
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
    risk_mitigation: List[str] = Field(description="Potential risks & solutions (max 3)")
    competitive_advantage: str = Field(description="How this differentiates")
    timeline_summary: str = Field(description="Key milestones")

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
    """FIXED: Enhanced agent response parser with better RunResponse handling"""
    try:
        logger.debug(f"🔍 Parsing {model_class.__name__} from {type(result)}")
        
        # ✅ CASE 1: Already correct model instance
        if isinstance(result, model_class):
            logger.debug("✅ Response is already correct model instance")
            return result
        
        # ✅ CASE 2: Handle RunResponse object (MAIN FIX)
        if hasattr(result, 'content'):
            content = result.content
            logger.debug(f"📦 Found RunResponse content - Type: {type(content)}")
            
            # Nếu content đã là model instance (AGNO auto-parse)
            if isinstance(content, model_class):
                logger.debug("✅ RunResponse content is correct model instance")
                return content
            
            # Nếu content là dict (parsed JSON)
            if isinstance(content, dict):
                logger.debug("✅ RunResponse content is dict, parsing...")
                validated_data = content.copy()
                
                # Ensure required fields exist with defaults
                if model_class == ConversationResponse:
                    defaults = {
                        "suggestions": [],
                        "options": [],
                        "progress": None,
                        "data": None,
                        "requires_input": True,
                        "can_proceed": False
                    }
                    for key, default_value in defaults.items():
                        if key not in validated_data:
                            validated_data[key] = default_value
                
                return model_class(**validated_data)
            
            # Nếu content là string (JSON)
            if isinstance(content, str):
                logger.debug("✅ RunResponse content is string, attempting JSON parse...")
                try:
                    # Clean và parse JSON
                    cleaned_content = content.strip()
                    
                    # Remove markdown if present
                    if "```json" in cleaned_content:
                        start = cleaned_content.find("```json") + 7
                        end = cleaned_content.find("```", start)
                        if end > start:
                            cleaned_content = cleaned_content[start:end].strip()
                    
                    parsed_data = json.loads(cleaned_content)
                    logger.debug(f"✅ Successfully parsed JSON: {list(parsed_data.keys())}")
                    
                    # Add defaults for ConversationResponse
                    if model_class == ConversationResponse:
                        defaults = {
                            "suggestions": [],
                            "options": [],
                            "progress": None,
                            "data": None,
                            "requires_input": True,
                            "can_proceed": False
                        }
                        for key, default_value in defaults.items():
                            if key not in parsed_data:
                                parsed_data[key] = default_value
                    
                    return model_class(**parsed_data)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode failed: {e}")
                    logger.error(f"Content preview: {cleaned_content[:300]}")
                    
                    # Try to extract JSON pattern from text
                    import re
                    json_pattern = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned_content, re.DOTALL)
                    if json_pattern:
                        try:
                            parsed_data = json.loads(json_pattern.group(0))
                            logger.debug("✅ Extracted JSON from text pattern")
                            return model_class(**parsed_data)
                        except:
                            pass
                    
                    raise
        
        # ✅ CASE 3: Direct dict
        if isinstance(result, dict):
            logger.debug("✅ Result is dict, parsing directly...")
            return model_class(**result)
        
        # ✅ CASE 4: String JSON
        if isinstance(result, str):
            logger.debug("✅ Result is string, attempting JSON parse...")
            parsed_data = json.loads(result)
            return model_class(**parsed_data)
        
        # ❌ CASE 5: Unknown format
        logger.error(f"❌ Unknown result format: {type(result)}")
        raise ValueError(f"Cannot parse response type: {type(result)}")
        
    except Exception as e:
        logger.error(f"❌ Error parsing agent response: {e}")
        logger.error(f"Result type: {type(result)}")
        
        # Detailed logging for debugging
        if hasattr(result, 'content'):
            logger.error(f"Content type: {type(result.content)}")
            logger.error(f"Content preview: {str(result.content)[:300] if result.content else 'None'}")
        else:
            logger.error(f"Result preview: {str(result)[:300] if result else 'None'}")
        
        if fallback_data:
            logger.warning(f"🔄 Using fallback data for {model_class.__name__}")
            return model_class(**fallback_data)
        
        # Re-raise with more context
        raise ValueError(f"Failed to parse {model_class.__name__} from {type(result)}: {e}")

async def update_progress(context: ConversationContext, step: str, message: str):
    """Update progress and notify callbacks"""
    context.current_step = step
    context.completed_steps += 1
    context.updated_at = datetime.utcnow()
    
    progress_info = {
        "step": step,
        "message": message,
        "completed": context.completed_steps,
        "total": context.total_steps,
        "percentage": (context.completed_steps / max(context.total_steps, 1)) * 100,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Notify all registered callbacks
    for callback in context.progress_callbacks:
        try:
            await callback(progress_info)
        except Exception as e:
            logger.warning(f"Progress callback failed: {e}")

# =================== CONVERSATIONAL AGENT SYSTEM ===================

class ConversationalMediaReleaseAgents:
    """Advanced conversational multi-agent system with real-time interaction"""
    
    def __init__(self):
        """Initialize conversational agent system"""
        
        # Validate configuration
        if not OPENAI_API_KEY and not GROQ_API_KEY:
            raise ValueError("❌ Either OPENAI_API_KEY or GROQ_API_KEY environment variable is required")
        
        # Initialize model (prefer OpenAI, fallback to Groq)
        if OPENAI_API_KEY:
            self.llm = OpenAIChat(
                id=OPENAI_MODEL,
                api_key=OPENAI_API_KEY,
                temperature=OPENAI_TEMPERATURE,
                max_tokens=OPENAI_MAX_TOKENS,
                timeout=AGENT_TIMEOUT
            )
            logger.info(f"✅ Using OpenAI model: {OPENAI_MODEL}")
        elif GROQ_API_KEY:
            from agno.models.groq import GroqChat
            self.llm = GroqChat(
                id=GROQ_MODEL,
                api_key=GROQ_API_KEY,
                temperature=OPENAI_TEMPERATURE,
                max_tokens=OPENAI_MAX_TOKENS,
                timeout=AGENT_TIMEOUT
            )
            logger.info(f"✅ Using Groq model: {GROQ_MODEL}")
        
        # Agent memory storage
        self.storage = SqliteAgentStorage(
            table_name="conversational_agents",
            db_file="./agent_memory.db"
        )
        
        # Initialize conversation contexts
        self.active_conversations: Dict[str, ConversationContext] = {}
        
        # Initialize specialized agents
        self.conversation_agent = self._create_conversation_agent()
        self.workflow_coordinator = self._create_workflow_coordinator()
        self.content_analyzer = self._create_content_analyzer()
        self.document_analyzer = self._create_document_analyzer()
        self.media_matcher = self._create_media_matcher()
        self.pricing_optimizer = self._create_pricing_optimizer()
        self.report_generator = self._create_report_generator()
        self.plan_modifier = self._create_plan_modifier()
        
        logger.info("✅ Conversational Media Release multi-agent system initialized")
    
    def _create_conversation_agent(self) -> Agent:
        return Agent(
            name="ConversationAgent",
            role="Expert Vietnamese PR consultant and conversational AI assistant",
            model=self.llm,
            instructions=[
                "Engage users in natural, helpful conversation about their PR needs",
                "Gather project information through friendly dialogue, not interrogation", 
                "Explain the process clearly and set proper expectations",
                "Identify when to trigger the AI workflow vs continue conversation",
                "Help users understand their options and make informed decisions",
                "Provide expert advice on Vietnamese media landscape",
                "Be proactive in suggesting improvements and alternatives",
                "Always maintain a professional yet approachable tone",
                "Remember user preferences and adapt conversation accordingly",
                "Guide users through reviewing and modifying recommendations",
                
                # ✅ QUAN TRỌNG: Thêm instructions rõ ràng hơn
                "CRITICAL: You MUST respond in valid JSON format only",
                "NEVER include any text outside the JSON object",
                "JSON must match ConversationResponse schema exactly",
                "Required fields: message, state, phase, suggestions, options, requires_input, can_proceed",
                
                '''RESPONSE TEMPLATE:
                {
                    "message": "Your conversational response here in Vietnamese",
                    "state": "greeting|gathering_info|analyzing|reviewing|etc",
                    "phase": "idle|content_analysis|etc", 
                    "suggestions": ["suggestion1", "suggestion2"],
                    "options": ["option1", "option2"],
                    "requires_input": true,
                    "can_proceed": false
                }'''
            ],
            response_model=ConversationResponse,
            storage=self.storage,
            show_tool_calls=False,
            markdown=False
        )
    
    def _create_workflow_coordinator(self) -> Agent:
        """Coordinates workflow execution and user interactions"""
        return Agent(
            name="WorkflowCoordinator",
            role="AI workflow orchestrator and process manager",
            model=self.llm,
            description="""
            You are an intelligent workflow coordinator who manages the execution of
            specialized AI agents while maintaining user engagement and allowing for
            real-time modifications and feedback.
            """,
            instructions=[
                "Coordinate the execution of specialized agents based on user needs",
                "Make decisions about which agents to run and in what order",
                "Handle user interruptions and modification requests gracefully",
                "Provide real-time updates on workflow progress",
                "Adapt workflow based on intermediate results and user feedback",
                "Ensure efficient resource utilization and error recovery",
                "Maintain context across agent executions",
                "Balance automation with user control and transparency"
            ],
            storage=self.storage,
            show_tool_calls=True,
            markdown=False
        )
    
    def _create_content_analyzer(self) -> Agent:
        """Enhanced content analysis with conversation context"""
        return Agent(
            name="ContentAnalyzer",
            role="Expert Vietnamese content analyst for PR and media with conversation awareness",
            model=self.llm,
            description="""
            You are a senior content strategist specializing in Vietnamese media landscape.
            You excel at understanding business contexts from conversational input,
            identifying target audiences, and extracting key information for media matching.
            """,
            instructions=[
                "Analyze user input and conversation context to extract business requirements",
                "Consider both explicit statements and implied needs from conversation",
                "Identify the primary language preference and target market",
                "Determine the most relevant industry sector and press release type",
                "Extract key topics and themes for media matching",
                "Assess content tone, urgency, and geographic scope",
                "Factor in user's conversational style and preferences",
                "Provide confidence score and explain reasoning",
                "Focus on Vietnamese market nuances and business culture",
                "Consider SME-specific communication needs and constraints",
                "Return ONLY valid JSON in ContentAnalysis format"
            ],
            response_model=ContentAnalysis,
            storage=self.storage,
            session_id="content_analysis",
            show_tool_calls=False,
            markdown=False
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
            instructions=[
                "Analyze uploaded documents in context of user conversation",
                "Extract key information that supports the user's stated goals",
                "Identify compelling data points, quotes, and statistics",
                "Suggest media angles based on both document content and conversation",
                "Assess content quality and usefulness for stated PR purposes",
                "Consider user's industry, target audience, and strategic objectives",
                "Extract supporting evidence for press release claims",
                "Identify insights that align with user's conversational preferences",
                "Focus on Vietnamese market context and business interests",
                "Return ONLY valid JSON in DocumentAnalysis format"
            ],
            response_model=DocumentAnalysis,
            storage=self.storage,
            session_id="document_analysis",
            show_tool_calls=False,
            markdown=False
        )
    
    def _create_media_matcher(self) -> Agent:
        """Enhanced media matcher with conversational insights"""
        return Agent(
            name="MediaMatcher",
            role="Vietnamese media landscape expert with conversational intelligence",
            model=self.llm,
            description="""
            You are a veteran PR professional with deep expertise in Vietnamese media.
            You understand user needs from conversation context and can match content
            with the most effective media outlets while considering user preferences.
            """,
            instructions=[
                "Analyze content requirements and conversation context for media matching",
                "Consider user's stated preferences and budget constraints",
                "Prioritize outlets based on user's industry and target audience",
                "Factor in tier-1 outlets: VnExpress, 24H, Dân trí, Tuổi trẻ, etc.",
                "Consider specialized outlets for business, tech, youth, etc.",
                "Match language requirements (Vietnamese/English) precisely",
                "Evaluate topic relevance and audience alignment from conversation",
                "Factor in publication success rates and response times",
                "Consider user's timeline and urgency requirements",
                "Provide clear reasoning that connects to user's goals",
                "Optimize for maximum reach within stated budget",
                "Return ONLY valid JSON in MediaRecommendation format"
            ],
            response_model=MediaRecommendation,
            tools=[DuckDuckGoTools()],
            storage=self.storage,
            session_id="media_matching",
            show_tool_calls=True,
            markdown=False
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
            instructions=[
                "Analyze user budget and conversation context for optimal pricing",
                "Consider user's stated priorities and success metrics",
                "Calculate optimal package: Starter (12M), Standard (30M), Premium (50M)",
                "Factor in user's timeline preferences and flexibility",
                "Ensure total costs align with user's budget and expectations",
                "Maximize media coverage based on user's stated objectives",
                "Consider user's risk tolerance and growth stage",
                "Factor in conversation insights about user's business priorities",
                "Provide realistic timeline estimates based on package complexity",
                "Calculate budget utilization with conversation context",
                "Suggest alternatives that align with user's stated preferences",
                "Project ROI based on user's success metrics and industry benchmarks",
                "Return ONLY valid JSON in PricingAnalysis format"
            ],
            response_model=PricingAnalysis,
            storage=self.storage,
            session_id="pricing_optimization",
            show_tool_calls=False,
            markdown=False
        )
    
    def _create_report_generator(self) -> Agent:
        """Enhanced report generator with conversational insights"""
        return Agent(
            name="ReportGenerator", 
            role="Senior PR consultant and executive report writer with conversation intelligence",
            model=self.llm,
            description="""
            You are an executive-level PR consultant who creates strategic media reports.
            You translate technical recommendations into business insights while incorporating
            the user's conversational context and stated preferences.
            """,
            instructions=[
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
                "Return ONLY valid JSON in ExecutiveReport format"
            ],
            response_model=ExecutiveReport,
            storage=self.storage,
            session_id="executive_reports",
            show_tool_calls=False,
            markdown=False
        )
    
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
            instructions=[
                "Analyze user feedback and modification requests carefully",
                "Assess the feasibility and impact of requested changes",
                "Provide alternative solutions when requests aren't feasible",
                "Calculate cost and timeline impacts of modifications",
                "Maintain plan coherence while accommodating user needs",
                "Explain trade-offs and implications clearly",
                "Suggest creative alternatives that meet user's underlying needs",
                "Consider budget constraints and market realities",
                "Ensure modified plans remain strategically sound",
                "Return ONLY valid JSON in PlanModification format"
            ],
            response_model=PlanModification,
            storage=self.storage,
            session_id="plan_modification",
            show_tool_calls=False,
            markdown=False
        )
    
    # =================== CONVERSATION MANAGEMENT ===================
    
    async def start_conversation(self, session_id: str) -> ConversationResponse:
        """Start a new conversation with a user"""
        try:
            # Create new conversation context
            context = ConversationContext(
                session_id=session_id,
                state=ConversationState.GREETING,
                phase=WorkflowPhase.IDLE
            )
            
            self.active_conversations[session_id] = context
            
            # Generate greeting
            greeting_prompt = """
            Greet the user as ChiCom AI, your Vietnamese PR consultant assistant.
            
            Introduce yourself briefly and ask about their press release or media campaign needs.
            Be warm, professional, and set the tone for a collaborative conversation.
            
            Explain that you'll help them create an effective media strategy through conversation
            and can launch AI agents to analyze and optimize their campaign when ready.
            
            Return a ConversationResponse with:
            - A friendly greeting message
            - Current state as 'greeting'
            - Suggestions for how they can share their project information
            """
            
            result = await self.conversation_agent.arun(greeting_prompt)
            response = parse_agent_response(result, ConversationResponse, {
                "message": "Xin chào! Tôi là ChiCom AI, chuyên gia tư vấn PR tại Việt Nam. Tôi sẽ giúp bạn tạo ra chiến lược truyền thông hiệu quả. Hãy chia sẻ với tôi về dự án hoặc nhu cầu truyền thông của bạn!",
                "state": "greeting",
                "phase": "idle",
                "suggestions": [
                    "Chia sẻ về dự án/sản phẩm của bạn",
                    "Nói về mục tiêu truyền thông",
                    "Thảo luận về ngân sách và timeline"
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
            
            logger.info(f"💬 Started conversation for session: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Failed to start conversation: {e}")
            return ConversationResponse(
                message="Xin lỗi, có lỗi xảy ra khi khởi tạo cuộc trò chuyện. Vui lòng thử lại!",
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
        """Continue conversation with user input"""
        try:
            # Get conversation context
            context = self.active_conversations.get(session_id)
            if not context:
                return await self.start_conversation(session_id)
            
            # Add progress callback if provided
            if progress_callback and progress_callback not in context.progress_callbacks:
                context.progress_callbacks.append(progress_callback)
            
            # Add user message to history
            context.conversation_history.append({
                "role": "user",
                "message": user_message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Build conversation prompt with context
            conversation_prompt = f"""
            Continue this conversation as ChiCom AI, the Vietnamese PR consultant.
            
            CONVERSATION HISTORY:
            {self._format_conversation_history(context.conversation_history[-10:])}
            
            CURRENT USER MESSAGE: {user_message}
            
            CURRENT STATE: {context.state.value}
            CURRENT PHASE: {context.phase.value}
            
            GATHERED INFORMATION SO FAR:
            - User Input: {context.user_input}
            - Budget: {context.budget:,.0f} VND if > 0
            - Requirements: {json.dumps(context.requirements, ensure_ascii=False)}
            - Preferences: {json.dumps(context.preferences, ensure_ascii=False)}
            
            Your tasks:
            1. Respond to the user's message naturally and helpfully
            2. Gather any missing information through conversation (don't interrogate)
            3. Determine if you have enough information to start the AI workflow
            4. If ready for workflow, ask for confirmation and explain what will happen
            5. If user wants to modify existing plans, acknowledge and prepare for modification
            6. Always maintain a consultative, expert tone
            
            Decision points:
            - If you have: project description, budget range, basic requirements → can start workflow
            - If user asks questions → answer them expertly
            - If user wants to see analysis → trigger workflow
            - If user wants to modify plans → transition to modification mode
            
            Return a ConversationResponse with appropriate state transition.
            """
            
            result = await self.conversation_agent.arun(conversation_prompt)
            response = parse_agent_response(result, ConversationResponse, {
                "message": "Cảm ơn bạn đã chia sẻ! Hãy cho tôi biết thêm về mục tiêu truyền thông của bạn.",
                "state": context.state.value,
                "phase": context.phase.value,
                "requires_input": True,
                "can_proceed": False
            })
            
            # Update context based on response
            await self._update_context_from_conversation(context, user_message, response)
            
            # Add assistant response to history
            context.conversation_history.append({
                "role": "assistant",
                "message": response.message,
                "timestamp": datetime.utcnow().isoformat(),
                "state": response.state
            })
            
            logger.info(f"💬 Continued conversation for session: {session_id} - State: {response.state}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Conversation continuation failed: {e}")
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
        """Trigger the AI workflow based on conversation context"""
        try:
            context = self.active_conversations.get(session_id)
            if not context:
                raise ValueError("Conversation context not found")
            
            # Add progress callback
            if progress_callback and progress_callback not in context.progress_callbacks:
                context.progress_callbacks.append(progress_callback)
            
            # Update state
            context.state = ConversationState.EXECUTING
            context.phase = WorkflowPhase.CONTENT_ANALYSIS
            context.workflow_started = True
            context.total_steps = 5  # Content, Document, Media, Pricing, Report
            context.completed_steps = 0
            
            # Notify user of workflow start
            await update_progress(context, "Workflow Started", "🚀 Bắt đầu phân tích với AI Agents...")
            
            # Run the complete workflow
            workflow_result = await self._execute_complete_workflow(context)
            
            # Generate completion response
            completion_prompt = f"""
            The AI workflow has completed successfully. Present the results to the user.
            
            WORKFLOW RESULTS:
            {json.dumps(workflow_result, ensure_ascii=False, indent=2)}
            
            Create a completion message that:
            1. Announces successful completion
            2. Highlights key insights and recommendations
            3. Invites user to review and provide feedback
            4. Offers options for modification or approval
            5. Maintains consultative tone
            
            Return a ConversationResponse with state 'reviewing' and appropriate options.
            """
            
            result = await self.conversation_agent.arun(completion_prompt)
            response = parse_agent_response(result, ConversationResponse, {
                "message": "✅ Phân tích hoàn thành! Tôi đã tạo được chiến lược truyền thông chi tiết cho bạn. Hãy xem xét và cho tôi biết ý kiến nhé!",
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
            
            # Update context
            context.state = ConversationState.REVIEWING
            context.phase = WorkflowPhase.USER_REVIEW
            
            # Store results in context
            context.content_analysis = workflow_result.get("content_analysis")
            context.document_analysis = workflow_result.get("document_analysis")
            context.media_recommendations = workflow_result.get("media_recommendations", [])
            context.pricing_analysis = workflow_result.get("pricing_analysis")
            context.executive_report = workflow_result.get("executive_report")
            
            logger.info(f"✅ Workflow completed for session: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            
            # Update context to error state
            if session_id in self.active_conversations:
                self.active_conversations[session_id].state = ConversationState.ERROR
            
            return ConversationResponse(
                message=f"❌ Có lỗi xảy ra trong quá trình phân tích: {str(e)}. Tôi sẽ thử lại hoặc bạn có thể chia sẻ thêm thông tin.",
                state="error",
                phase="idle",
                suggestions=["Thử lại phân tích", "Chia sẻ thêm thông tin", "Bắt đầu lại cuộc trò chuyện"],
                requires_input=True,
                can_proceed=False
            )
    
    async def modify_plan(
        self, 
        session_id: str, 
        modification_request: str,
        progress_callback: Optional[Callable] = None
    ) -> ConversationResponse:
        """Handle user plan modification requests"""
        try:
            context = self.active_conversations.get(session_id)
            if not context:
                raise ValueError("Conversation context not found")
            
            # Add progress callback
            if progress_callback and progress_callback not in context.progress_callbacks:
                context.progress_callbacks.append(progress_callback)
            
            context.state = ConversationState.MODIFYING
            context.phase = WorkflowPhase.PLAN_MODIFICATION
            context.needs_modification = True
            
            await update_progress(context, "Plan Modification", "🔄 Đang phân tích yêu cầu thay đổi...")
            
            # Analyze modification request
            modification_prompt = f"""
            Analyze this plan modification request in context of the current media strategy.
            
            USER MODIFICATION REQUEST: {modification_request}
            
            CURRENT PLAN:
            - Content Analysis: {json.dumps(context.content_analysis, ensure_ascii=False) if context.content_analysis else "N/A"}
            - Pricing: {json.dumps(context.pricing_analysis, ensure_ascii=False) if context.pricing_analysis else "N/A"}
            - Media Count: {len(context.media_recommendations)}
            - Budget: {context.budget:,.0f} VND
            
            MEDIA RECOMMENDATIONS:
            {json.dumps(context.media_recommendations[:5], ensure_ascii=False, indent=2)}
            
            Analyze what the user wants to change and assess:
            1. Type of modification (budget, media selection, timeline, strategy)
            2. Feasibility of the request
            3. Impact on other parts of the plan
            4. Alternative suggestions if request isn't optimal
            5. Cost and timeline implications
            
            Return a PlanModification analysis.
            """
            
            result = await self.plan_modifier.arun(modification_prompt)
            modification_analysis = parse_agent_response(result, PlanModification, {
                "modification_type": "General",
                "original_value": "Current plan",
                "new_value": modification_request,
                "impact_assessment": "Requires detailed analysis",
                "feasibility": "Medium",
                "alternative_suggestions": ["Discuss alternatives"],
                "cost_impact": 0.0,
                "timeline_impact": "No change"
            })
            
            # Generate response based on modification analysis
            response_prompt = f"""
            Respond to the user's modification request based on this analysis.
            
            MODIFICATION ANALYSIS: {modification_analysis.model_dump()}
            USER REQUEST: {modification_request}
            
            Create a helpful response that:
            1. Acknowledges their request specifically
            2. Explains the feasibility and impacts
            3. Suggests alternatives if needed
            4. Asks for confirmation or further clarification
            5. Maintains collaborative tone
            
            If modification is feasible, offer to implement it.
            If not optimal, explain why and suggest better alternatives.
            """
            
            result = await self.conversation_agent.arun(response_prompt)
            response = parse_agent_response(result, ConversationResponse, {
                "message": "Tôi hiểu yêu cầu của bạn. Để thay đổi hiệu quả nhất, chúng ta cần cân nhắc một số yếu tố. Bạn có muốn tôi giải thích chi tiết không?",
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
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"🔄 Plan modification analyzed for session: {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Plan modification failed: {e}")
            return ConversationResponse(
                message="Xin lỗi, có lỗi khi phân tích yêu cầu thay đổi. Bạn có thể mô tả lại chi tiết hơn không?",
                state="modifying",
                phase="plan_modification",
                requires_input=True,
                can_proceed=False
            )
    
    # =================== WORKFLOW EXECUTION ===================
    
    async def _execute_complete_workflow(self, context: ConversationContext) -> Dict[str, Any]:
        """Execute complete workflow with real-time progress updates"""
        try:
            workflow_results = {}
            
            # Step 1: Content Analysis
            await update_progress(context, "Content Analysis", "📊 Phân tích nội dung và yêu cầu...")
            content_analysis = await self._analyze_content_with_context(context)
            workflow_results["content_analysis"] = content_analysis.model_dump()
            
            # Step 2: Document Analysis (if documents available)
            await update_progress(context, "Document Analysis", "📄 Phân tích tài liệu đính kèm...")
            document_analysis = await self._analyze_documents_with_context(context)
            if document_analysis:
                workflow_results["document_analysis"] = document_analysis.model_dump()
            
            # Step 3: Media Matching
            await update_progress(context, "Media Matching", "🎯 Tìm kiếm báo chí phù hợp...")
            media_recommendations = await self._find_matching_media_with_context(context, content_analysis, document_analysis)
            workflow_results["media_recommendations"] = [rec.model_dump() for rec in media_recommendations]
            
            # Step 4: Pricing Optimization
            await update_progress(context, "Pricing Optimization", "💰 Tối ưu hóa gói dịch vụ...")
            pricing_analysis = await self._optimize_pricing_with_context(context, media_recommendations)
            workflow_results["pricing_analysis"] = pricing_analysis.model_dump()
            
            # Step 5: Executive Report Generation
            await update_progress(context, "Report Generation", "📋 Tạo báo cáo chiến lược...")
            executive_report = await self._generate_executive_report_with_context(
                context, content_analysis, media_recommendations, pricing_analysis, document_analysis
            )
            workflow_results["executive_report"] = executive_report.model_dump()
            
            # Calculate processing summary
            processing_time = (datetime.utcnow() - context.created_at).total_seconds()
            workflow_results.update({
                "session_id": context.session_id,
                "processing_time_seconds": processing_time,
                "summary": {
                    "recommended_package": pricing_analysis.recommended_package,
                    "total_cost": pricing_analysis.total_cost_vnd,
                    "media_count": len(media_recommendations),
                    "timeline": pricing_analysis.timeline_days,
                    "budget_utilization": pricing_analysis.budget_utilization,
                    "confidence_score": content_analysis.confidence_score,
                    "documents_analyzed": bool(document_analysis),
                    "document_quality": document_analysis.document_quality if document_analysis else None
                },
                "timestamp": datetime.utcnow().isoformat(),
                "agent_system": "Conversational Media Release v3.0"
            })
            
            await update_progress(context, "Completed", "✅ Hoàn thành phân tích!")
            
            logger.info(f"✅ Complete workflow finished for session: {context.session_id}")
            return workflow_results
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            await update_progress(context, "Error", f"❌ Lỗi: {str(e)}")
            raise
    
    async def _analyze_content_with_context(self, context: ConversationContext) -> ContentAnalysis:
        """Enhanced content analysis using conversation context"""
        try:
            # Compile comprehensive input from conversation
            conversation_summary = self._extract_key_info_from_conversation(context)
            
            prompt = f"""
            Analyze this comprehensive project information from conversation context:
            
            MAIN PROJECT DESCRIPTION: {context.user_input}
            BUDGET: {context.budget:,.0f} VND
            
            CONVERSATION INSIGHTS:
            {conversation_summary}
            
            REQUIREMENTS: {json.dumps(context.requirements, ensure_ascii=False)}
            PREFERENCES: {json.dumps(context.preferences, ensure_ascii=False)}
            
            CONVERSATION HISTORY CONTEXT:
            {self._format_conversation_history(context.conversation_history[-5:])}
            
            Perform comprehensive analysis considering:
            1. Explicit project information shared
            2. Implied needs from conversation context
            3. User's communication style and preferences
            4. Industry context and market positioning
            5. Target audience insights from dialogue
            6. Strategic objectives mentioned in conversation
            7. Constraints and priorities discussed
            
            Return analysis in ContentAnalysis JSON format.
            """
            
            result = await self.content_analyzer.arun(prompt)
            
            # Parse with enhanced fallback using conversation context
            fallback_data = {
                "language": context.preferences.get("language", "Vietnamese"),
                "primary_topics": context.requirements.get("topics", ["Business", "Technology"]),
                "target_audiences": context.requirements.get("audiences", ["General Public"]),
                "keywords": ["press release", context.requirements.get("industry", "business")],
                "content_tone": context.preferences.get("tone", "Professional"),
                "urgency_level": context.requirements.get("urgency", "Medium"),
                "industry_sector": context.requirements.get("industry", "General"),
                "press_release_type": context.requirements.get("type", "Other"),
                "geographic_scope": context.requirements.get("scope", "National"),
                "confidence_score": 0.8
            }
            
            content_analysis = parse_agent_response(result, ContentAnalysis, fallback_data)
            logger.info(f"✅ Content analysis completed with context - Confidence: {content_analysis.confidence_score:.2f}")
            
            return content_analysis
            
        except Exception as e:
            logger.error(f"❌ Content analysis failed: {e}")
            # Return fallback analysis with conversation context
            return ContentAnalysis(
                language=context.preferences.get("language", "Vietnamese"),
                primary_topics=context.requirements.get("topics", ["Business", "Technology"]),
                target_audiences=context.requirements.get("audiences", ["General Public"]),
                keywords=["press release"],
                content_tone="Professional",
                urgency_level="Medium",
                industry_sector="General",
                press_release_type="Other",
                geographic_scope="National",
                confidence_score=0.6
            )
    
    async def _analyze_documents_with_context(self, context: ConversationContext) -> Optional[DocumentAnalysis]:
        """Enhanced document analysis with conversation context"""
        try:
            # Get document processor
            doc_processor = get_document_processor()
            if not doc_processor:
                logger.warning("Document processor not available")
                return None
            
            # Get uploaded documents for this session
            session_docs = doc_processor.get_session_documents(context.session_id)
            if not session_docs:
                logger.info(f"No documents found for session {context.session_id}")
                return None
            
            # Create search query from conversation context
            search_terms = []
            if context.requirements.get("topics"):
                search_terms.extend(context.requirements["topics"])
            if context.user_input:
                search_terms.append(context.user_input[:100])  # First 100 chars
            
            search_query = " ".join(search_terms) if search_terms else "business project information"
            
            # Search documents for relevant content
            search_results = await doc_processor.search_user_documents(
                query=search_query,
                session_id=context.session_id,
                limit=10
            )
            
            if not search_results:
                logger.warning("No relevant content found in uploaded documents")
                return None
            
            # Compile document content for analysis
            document_content = "\n\n".join([
                result.get("content", "") for result in search_results
            ])
            
            # Include conversation context in analysis
            conversation_summary = self._extract_key_info_from_conversation(context)
            
            prompt = f"""
            Analyze these uploaded documents in context of the user's conversational requirements:
            
            USER PROJECT CONTEXT: {context.user_input}
            CONVERSATION INSIGHTS: {conversation_summary}
            USER REQUIREMENTS: {json.dumps(context.requirements, ensure_ascii=False)}
            USER PREFERENCES: {json.dumps(context.preferences, ensure_ascii=False)}
            
            DOCUMENT CONTENT:
            {document_content[:4000]}  # Limit content to avoid token limits
            
            SESSION DOCUMENTS: {[doc["filename"] for doc in session_docs]}
            
            Extract valuable information considering:
            1. User's stated goals and objectives from conversation
            2. Target audience mentioned in dialogue
            3. Strategic priorities discussed
            4. Media angles that align with conversation context
            5. Supporting data that reinforces user's key messages
            6. Vietnamese market relevance and positioning
            
            Return analysis in DocumentAnalysis JSON format.
            """
            
            result = await self.document_analyzer.arun(prompt)
            
            # Parse response with conversation-aware fallback
            fallback_data = {
                "document_summary": f"Document analyzed for {context.requirements.get('industry', 'business')} project",
                "key_information": ["Business information extracted from documents"],
                "relevant_topics": context.requirements.get("topics", ["Business"]),
                "target_audience_insights": context.requirements.get("audiences", ["General audience"]),
                "media_angles": ["Business story angle", "Market development angle"],
                "supporting_data": ["Supporting information available from documents"],
                "document_quality": "Medium",
                "confidence_score": 0.7
            }
            
            document_analysis = parse_agent_response(result, DocumentAnalysis, fallback_data)
            logger.info("✅ Document analysis completed with conversation context")
            
            return document_analysis
            
        except Exception as e:
            logger.error(f"❌ Document analysis failed: {e}")
            return None
    
    async def _find_matching_media_with_context(
        self, 
        context: ConversationContext,
        content_analysis: ContentAnalysis,
        document_analysis: Optional[DocumentAnalysis]
    ) -> List[MediaRecommendation]:
        """Enhanced media matching with conversation and database integration"""
        try:
            # Build comprehensive search query
            search_terms = []
            search_terms.extend(content_analysis.primary_topics)
            search_terms.extend(content_analysis.target_audiences)
            search_terms.append(content_analysis.industry_sector)
            
            if document_analysis:
                search_terms.extend(document_analysis.relevant_topics)
            
            # Add conversation-specific terms
            if context.requirements.get("preferred_media"):
                search_terms.extend(context.requirements["preferred_media"])
            
            search_query = " ".join(search_terms)
            
            # Enhanced vector search with new database
            vector_results = await media_db.search_media_by_vector(search_query, limit=15)
            
            # Get candidate media outlets
            media_candidates = []
            if vector_results and "metadatas" in vector_results and vector_results["metadatas"]:
                for metadata in vector_results["metadatas"][0]:
                    if "media_id" in metadata:
                        media_id = int(metadata["media_id"])
                        media = await media_db.get_media_by_id(media_id)
                        if media and media.is_active:
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
                            media_candidates.append({
                                "id": media.id,
                                "name": media.name,
                                "category": media.category,
                                "tier": media.tier,
                                "cost": media.cost_per_article,
                                "monthly_visits": media.monthly_visits,
                                "top_categories": media.top_categories,
                                "topics": media.topics,
                                "audiences": media.target_audience,
                                "language": media.language,
                                "success_rate": media.success_rate,
                                "response_time": media.response_time_hours
                            })
            
            logger.info(f"🎯 Found {len(media_candidates)} candidate media outlets")
            
            # Enhanced matching with conversation context
            conversation_summary = self._extract_key_info_from_conversation(context)
            document_context = ""
            if document_analysis:
                document_context = f"""
                DOCUMENT INSIGHTS:
                - Media Angles: {', '.join(document_analysis.media_angles)}
                - Key Topics: {', '.join(document_analysis.relevant_topics)}
                - Target Audience Insights: {', '.join(document_analysis.target_audience_insights)}
                """
            
            # Process recommendations with enhanced context
            recommendations = []
            for i, candidate in enumerate(media_candidates[:10]):  # Process top 10
                try:
                    prompt = f"""
                    Evaluate this Vietnamese media outlet for the conversational project:
                    
                    CONTENT ANALYSIS: {content_analysis.model_dump()}
                    CONVERSATION CONTEXT: {conversation_summary}
                    USER BUDGET: {context.budget:,.0f} VND
                    USER PREFERENCES: {json.dumps(context.preferences, ensure_ascii=False)}
                    {document_context}
                    
                    MEDIA OUTLET TO EVALUATE: {json.dumps(candidate, ensure_ascii=False, indent=2)}
                    
                    Consider:
                    1. Alignment with user's stated objectives from conversation
                    2. Budget constraints and cost-effectiveness
                    3. Target audience match based on conversation insights
                    4. Content topic relevance
                    5. Language compatibility
                    6. Reach and credibility for user's goals
                    7. Response time fitting user's timeline preferences
                    
                    Return MediaRecommendation JSON for this specific outlet.
                    """
                    
                    result = await self.media_matcher.arun(prompt)
                    
                    # Parse with conversation-aware fallback
                    fallback_data = {
                        "media_outlet_id": candidate["id"],
                        "media_name": candidate["name"],
                        "matching_score": min(0.9, 0.6 + (candidate.get("monthly_visits", 1000000) / 100000000)),  # Safe calculation
                        "reasoning": f"Good fit for {content_analysis.industry_sector} in {candidate.get('category', 'general')} category",
                        "estimated_reach": candidate.get("monthly_visits", 1000000),  # Safe default
                        "cost_vnd": candidate.get("cost", 1000000),  # Safe default
                        "tier": candidate.get("tier", 2),  # Default tier 2
                        "language_match": candidate.get("language", "Vietnamese") == content_analysis.language or content_analysis.language == "Both",
                        "topic_overlap": 0.7,
                        "audience_fit": 0.7
                    }
                    
                    recommendation = parse_agent_response(result, MediaRecommendation, fallback_data)
                    recommendations.append(recommendation)
                    
                    # Small delay to avoid overwhelming
                    await asyncio.sleep(0.3)
                    
                except Exception as e:
                    logger.warning(f"Failed to process media candidate {candidate['name']}: {e}")
                    continue
            
            # Sort by matching score and apply conversation-based preferences
            recommendations.sort(key=lambda x: x.matching_score, reverse=True)
            
            # Apply budget filtering
            budget_filtered = []
            cumulative_cost = 0
            for rec in recommendations:
                if cumulative_cost + rec.cost_vnd <= context.budget * 0.8:  # Use 80% of budget for media
                    budget_filtered.append(rec)
                    cumulative_cost += rec.cost_vnd
                elif len(budget_filtered) < 3:  # Ensure at least 3 recommendations
                    budget_filtered.append(rec)
            
            logger.info(f"✅ Media matching completed - {len(budget_filtered)} recommendations within budget")
            return budget_filtered[:8]  # Return top 8
            
        except Exception as e:
            logger.error(f"❌ Media matching failed: {e}")
            return []
    
    async def _optimize_pricing_with_context(
        self, 
        context: ConversationContext,
        recommendations: List[MediaRecommendation]
    ) -> PricingAnalysis:
        """Enhanced pricing optimization with conversation context"""
        try:
            total_media_cost = sum(rec.cost_vnd for rec in recommendations) if recommendations else 0
            
            # Include conversation preferences in pricing
            conversation_summary = self._extract_key_info_from_conversation(context)
            document_context = ""
            
            # Fix: Safely access document_analysis - handle both dict and object
            if hasattr(context, 'document_analysis') and context.document_analysis:
                if isinstance(context.document_analysis, dict):
                    document_context = f"""
                    DOCUMENT ANALYSIS SUMMARY:
                    - Quality: {context.document_analysis.get('document_quality', 'Medium')}
                    - Supporting Data Available: {len(context.document_analysis.get('supporting_data', []))} items
                    - Media Angles: {len(context.document_analysis.get('media_angles', []))} potential angles
                    """
                elif hasattr(context.document_analysis, 'document_quality'):
                    # It's a Pydantic model
                    document_context = f"""
                    DOCUMENT ANALYSIS SUMMARY:
                    - Quality: {context.document_analysis.document_quality}
                    - Supporting Data Available: {len(context.document_analysis.supporting_data)} items
                    - Media Angles: {len(context.document_analysis.media_angles)} potential angles
                    """
            
            # Fix: Safely access content_analysis
            content_analysis_data = "Not available"
            if hasattr(context, 'content_analysis') and context.content_analysis:
                if isinstance(context.content_analysis, dict):
                    content_analysis_data = json.dumps(context.content_analysis, ensure_ascii=False)
                elif hasattr(context.content_analysis, 'model_dump'):
                    content_analysis_data = json.dumps(context.content_analysis.model_dump(), ensure_ascii=False)
                elif hasattr(context.content_analysis, '__dict__'):
                    content_analysis_data = json.dumps(context.content_analysis.__dict__, ensure_ascii=False)
            
            # Fix: Ensure budget is not zero
            safe_budget = max(context.budget if context.budget > 0 else 25000000, 1000000)  # Minimum 1M VND
            
            prompt = f"""
            Optimize pricing strategy considering conversation context and user preferences:
            
            USER BUDGET: {safe_budget:,.0f} VND
            CONTENT ANALYSIS: {content_analysis_data}
            CONVERSATION INSIGHTS: {conversation_summary}
            USER PREFERENCES: {json.dumps(context.preferences, ensure_ascii=False)}
            USER REQUIREMENTS: {json.dumps(context.requirements, ensure_ascii=False)}
            {document_context}
            
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
            
            Consider user's:
            - Stated timeline preferences from conversation
            - Quality expectations mentioned
            - Growth stage and business priorities
            - Risk tolerance and budget flexibility
            
            Return optimal PricingAnalysis JSON.
            """
            
            result = await self.pricing_optimizer.arun(prompt)
            
            # Determine best package based on budget and conversation
            if safe_budget <= 15000000:
                recommended_package = "Starter"
            elif safe_budget <= 35000000:
                recommended_package = "Standard"
            else:
                recommended_package = "Premium"
            
            # Fix: Safe budget utilization calculation
            package_price = PACKAGE_PRICES[recommended_package]["price"]
            total_cost = min(safe_budget, package_price + total_media_cost)
            budget_utilization = min(1.0, total_cost / safe_budget) if safe_budget > 0 else 0.0
            
            # Parse with conversation-aware fallback
            fallback_data = {
                "recommended_package": recommended_package,
                "total_cost_vnd": total_cost,
                "package_price_vnd": package_price,
                "media_costs_vnd": min(total_media_cost, max(0, safe_budget - package_price)),
                "timeline_days": PACKAGE_PRICES[recommended_package]["timeline"],
                "media_count": max(1, len(recommendations)),
                "budget_utilization": budget_utilization,
                "cost_efficiency": "Good value for Vietnamese market",
                "roi_projection": "Positive ROI expected based on reach and industry benchmarks",
                "alternative_packages": [pkg for pkg in PACKAGE_PRICES.keys() if pkg != recommended_package]
            }
            
            try:
                pricing_analysis = parse_agent_response(result, PricingAnalysis, fallback_data)
            except Exception as parse_error:
                logger.warning(f"Pricing parse failed, using fallback: {parse_error}")
                pricing_analysis = PricingAnalysis(**fallback_data)
            
            logger.info(f"✅ Pricing optimization completed - Package: {pricing_analysis.recommended_package}")
            return pricing_analysis
            
        except Exception as e:
            logger.error(f"❌ Pricing optimization failed: {e}")
            
            # Return conversation-aware fallback pricing
            safe_budget = max(context.budget if context.budget > 0 else 25000000, 1000000)
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
                cost_efficiency="Value-optimized for conversation requirements",
                roi_projection="Positive ROI expected",
                alternative_packages=[pkg for pkg in PACKAGE_PRICES.keys() if pkg != recommended_package]
            )
    
    async def _generate_executive_report_with_context(
        self,
        context: ConversationContext,
        content_analysis: ContentAnalysis,
        recommendations: List[MediaRecommendation],
        pricing: PricingAnalysis,
        document_analysis: Optional[DocumentAnalysis] = None
    ) -> ExecutiveReport:
        """Generate comprehensive executive report with conversation insights"""
        try:
            # Compile conversation insights
            conversation_summary = self._extract_key_info_from_conversation(context)
            
            # Include document analysis in prompt if available
            document_section = ""
            if document_analysis:
                document_section = f"""
                DOCUMENT ANALYSIS: {document_analysis.model_dump()}
                
                Key Supporting Evidence:
                - {chr(10).join(['• ' + item for item in document_analysis.supporting_data])}
                
                Media Angles from Documents:
                - {chr(10).join(['• ' + angle for angle in document_analysis.media_angles])}
                
                Document Quality Assessment: {document_analysis.document_quality}
                """
            
            prompt = f"""
            Create a strategic executive report that incorporates conversation insights:
            
            BUSINESS CONTEXT: {context.user_input}
            BUDGET: {context.budget:,.0f} VND
            
            CONVERSATION INSIGHTS: {conversation_summary}
            USER PREFERENCES: {json.dumps(context.preferences, ensure_ascii=False)}
            USER REQUIREMENTS: {json.dumps(context.requirements, ensure_ascii=False)}
            
            CONTENT ANALYSIS: {content_analysis.model_dump()}
            {document_section}
            
            MEDIA RECOMMENDATIONS: {[{
                "name": rec.media_name,
                "reach": rec.estimated_reach,
                "cost": rec.cost_vnd,
                "score": rec.matching_score,
                "reasoning": rec.reasoning
            } for rec in recommendations]}
            
            PRICING STRATEGY: {pricing.model_dump()}
            
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
            
            # Parse with conversation-aware fallback
            fallback_data = {
                "executive_summary": f"Comprehensive media strategy developed for {content_analysis.industry_sector} project with {len(recommendations)} targeted outlets within {context.budget:,.0f} VND budget.",
                "strategic_objectives": [
                    "Increase brand awareness in Vietnamese market",
                    "Generate qualified media coverage",
                    "Build market presence and credibility",
                    "Engage target audience effectively"
                ],
                "media_strategy": f"Multi-tier approach targeting Vietnamese {content_analysis.industry_sector} landscape with focus on tier-1 outlets and {pricing.recommended_package} package execution",
                "success_metrics": [
                    "Media mentions and coverage quality",
                    "Reach and impression metrics", 
                    "Audience engagement rates",
                    "Brand awareness lift measurement",
                    "Lead generation and business impact"
                ],
                "implementation_steps": [
                    "Finalize content and messaging",
                    "Submit to prioritized media outlets",
                    "Monitor coverage and engagement",
                    "Measure results against KPIs",
                    "Optimize strategy based on performance",
                    "Follow up and build media relationships"
                ],
                "risk_mitigation": [
                    "Backup media options identified",
                    "Timeline flexibility built in",
                    "Budget contingency planned"
                ],
                "competitive_advantage": "Strategic media mix with tier-1 coverage, Vietnamese market expertise, and conversation-tailored approach",
                "timeline_summary": pricing.timeline_days
            }
            
            executive_report = parse_agent_response(result, ExecutiveReport, fallback_data)
            logger.info("✅ Executive report completed with conversation context")
            
            return executive_report
            
        except Exception as e:
            logger.error(f"❌ Executive report generation failed: {e}")
            # Return conversation-aware fallback report
            return ExecutiveReport(
                executive_summary=f"Personalized media strategy developed through conversation for {context.budget:,.0f} VND budget targeting Vietnamese {content_analysis.industry_sector} market.",
                strategic_objectives=[
                    "Achieve conversation-specified goals",
                    "Generate targeted media coverage",
                    "Build market presence efficiently",
                    "Deliver measurable business impact"
                ],
                media_strategy=f"Conversation-tailored approach with {pricing.recommended_package} package targeting {len(recommendations)} strategic outlets",
                success_metrics=[
                    "Media coverage quality and reach",
                    "Audience engagement metrics",
                    "Business impact measurement",
                    "ROI achievement",
                    "Strategic goal completion"
                ],
                implementation_steps=[
                    "Execute conversation-agreed strategy",
                    "Deploy to selected media outlets", 
                    "Monitor and measure performance",
                    "Optimize based on results",
                    "Scale successful approaches",
                    "Build long-term media relationships"
                ],
                risk_mitigation=[
                    "Multiple media options secured",
                    "Flexible execution timeline",
                    "Budget optimization strategies"
                ],
                competitive_advantage="Conversation-customized strategy with Vietnamese market expertise and personalized execution approach",
                timeline_summary=pricing.timeline_days
            )
    
    # =================== HELPER METHODS ===================
    
    def _format_conversation_history(self, history: List[Dict]) -> str:
        """Format conversation history for agent prompts"""
        formatted = []
        for msg in history[-10:]:  # Last 10 messages
            role = msg.get("role", "unknown")
            content = msg.get("message", "")
            timestamp = msg.get("timestamp", "")
            
            if role == "user":
                formatted.append(f"USER: {content}")
            elif role == "assistant":
                formatted.append(f"ASSISTANT: {content}")
        
        return "\n".join(formatted)
    
    def _extract_key_info_from_conversation(self, context: ConversationContext) -> str:
        """Extract key information from conversation for agent context"""
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
            if context.preferences.get("communication_style"):
                key_info.append(f"Communication Style: {context.preferences['communication_style']}")
        
        # Extract from conversation patterns
        user_messages = [msg for msg in context.conversation_history if msg.get("role") == "user"]
        if user_messages:
            recent_topics = []
            for msg in user_messages[-3:]:  # Last 3 user messages
                content = msg.get("message", "").lower()
                if "ngân sách" in content or "budget" in content:
                    recent_topics.append("Budget discussed")
                if "timeline" in content or "thời gian" in content:
                    recent_topics.append("Timeline discussed")
                if "mục tiêu" in content or "goal" in content:
                    recent_topics.append("Goals mentioned")
            
            if recent_topics:
                key_info.append(f"Recent Discussion: {', '.join(recent_topics)}")
        
        return "; ".join(key_info) if key_info else "Limited conversation context available"
    
    async def _update_context_from_conversation(
        self, 
        context: ConversationContext, 
        user_message: str, 
        response: ConversationResponse
    ):
        """Update conversation context based on user input and response"""
        try:
            # Extract budget information
            budget_keywords = ["triệu", "million", "vnđ", "vnd", "budget", "ngân sách", "chi phí"]
            if any(keyword in user_message.lower() for keyword in budget_keywords):
                # Try to extract budget number
                import re
                numbers = re.findall(r'\d+', user_message)
                if numbers:
                    potential_budget = int(numbers[-1])  # Take last number
                    if potential_budget >= 1000:  # Reasonable budget check
                        if potential_budget < 1000000:  # Likely in millions
                            context.budget = potential_budget * 1000000
                        else:
                            context.budget = potential_budget
                        logger.info(f"Extracted budget: {context.budget:,.0f} VND")
            
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
                logger.info(f"Detected audiences: {detected_audiences}")
            
            # Extract urgency/timeline
            if any(word in user_message.lower() for word in ["gấp", "urgent", "nhanh", "quick", "asap"]):
                context.requirements["urgency"] = "High"
                context.preferences["timeline"] = "Urgent"
            elif any(word in user_message.lower() for word in ["chậm", "slow", "từ từ", "không vội"]):
                context.requirements["urgency"] = "Low"
                context.preferences["timeline"] = "Flexible"
            
            # Extract project goals
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
                logger.info(f"Detected goals: {detected_goals}")
            
            # Update conversation state based on gathered information
            has_project_info = bool(context.user_input or user_message) and len(user_message) > 20
            has_budget = context.budget > 0
            has_basic_requirements = bool(context.requirements.get("industry") or context.requirements.get("objectives"))
            
            # State progression logic
            if context.state == ConversationState.GREETING and has_project_info:
                context.state = ConversationState.GATHERING_INFO
                logger.info("State: GREETING → GATHERING_INFO")
            
            if context.state == ConversationState.GATHERING_INFO and has_project_info and has_budget and has_basic_requirements:
                context.state = ConversationState.ANALYZING
                logger.info("State: GATHERING_INFO → ANALYZING (ready for workflow)")
            
            # Update phase based on response
            if response.phase:
                try:
                    context.phase = WorkflowPhase(response.phase)
                except ValueError:
                    pass  # Invalid phase, keep current
            
            # Update user input if it's substantial and new
            if len(user_message) > 20:
                if not context.user_input or len(user_message) > len(context.user_input):
                    context.user_input = user_message
                    logger.info("Updated main user input")
            
            context.updated_at = datetime.utcnow()
            
        except Exception as e:
            logger.warning(f"Failed to update context from conversation: {e}")
            # Don't fail the conversation, just log the warning
    
    def _determine_media_categories(self, content_analysis: ContentAnalysis, context: ConversationContext) -> List[str]:
        """Determine relevant media categories based on analysis and conversation"""
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
        
        # Add categories from conversation context
        if context.requirements.get("industry"):
            industry = context.requirements["industry"]
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
            logger.info(f"🗑️ Cleared session: {session_id}")
            return True
        return False
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """Get summary of a conversation session"""
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
            "created_at": context.created_at.isoformat(),
            "updated_at": context.updated_at.isoformat(),
            "has_results": bool(context.content_analysis or context.media_recommendations)
        }

# =================== GLOBAL AGENT SYSTEM ===================

# Initialize global conversational agent system
try:
    conversational_agent_system = ConversationalMediaReleaseAgents()
    logger.info("✅ Global conversational agent system initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize conversational agent system: {e}")
    conversational_agent_system = None

# =================== TESTING ===================

async def test_conversational_system():
    """Comprehensive test of the conversational agent system"""
    if not conversational_agent_system:
        logger.error("❌ Conversational agent system not available for testing")
        return
    
    logger.info("🧪 Testing Conversational Media Release Agent System...")
    
    try:
        # Test conversation start
        response1 = await conversational_agent_system.start_conversation("test_session_001")
        logger.info(f"Start: {response1.message}")
        
        # Test conversation continuation
        response2 = await conversational_agent_system.continue_conversation(
            "test_session_001",
            "Chúng tôi là công ty fintech VietPay, vừa phát triển xong app thanh toán cho SME. Ngân sách khoảng 30 triệu."
        )
        logger.info(f"Continue: {response2.message}")
        
        # Test workflow trigger  
        if response2.can_proceed:
            response3 = await conversational_agent_system.trigger_workflow("test_session_001")
            logger.info(f"Workflow: {response3.message}")
        
        # Test session summary
        summary = conversational_agent_system.get_session_summary("test_session_001")
        logger.info(f"Summary: {summary}")
        
        logger.info("✅ Conversational agent system test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Conversational agent system test failed: {e}")
        return False

if __name__ == "__main__":
    # Run conversational system tests
    import asyncio
    asyncio.run(test_conversational_system())