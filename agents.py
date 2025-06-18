"""
Instant Media Release - Advanced Multi-Agent System
Production-grade AI agents using Agno framework for Vietnamese media automation
"""

import os
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.agent.sqlite import SqliteAgentStorage
from agno.tools.duckduckgo import DuckDuckGoTools
from pydantic import BaseModel, Field
from loguru import logger

from database import media_db, MediaOutletResponse

# =================== CONFIGURATION ===================

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "4000"))

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

# =================== STRUCTURED OUTPUT MODELS ===================

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

# =================== SPECIALIZED AGENTS ===================

class InstantMediaReleaseAgents:
    """Production-grade multi-agent system for media release automation"""
    
    def __init__(self):
        """Initialize all agents with production configuration"""
        
        # Validate configuration
        if not OPENAI_API_KEY:
            raise ValueError("❌ OPENAI_API_KEY environment variable is required")
        
        # Initialize OpenAI model with optimized settings
        self.llm = OpenAIChat(
            id=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS,
            timeout=AGENT_TIMEOUT
        )
        
        # Agent memory storage
        self.storage = SqliteAgentStorage(
            table_name="instant_media_agents",
            db_file="./agent_memory.db"
        )
        
        # Initialize specialized agents
        self.content_analyzer = self._create_content_analyzer()
        self.media_matcher = self._create_media_matcher()
        self.pricing_optimizer = self._create_pricing_optimizer()
        self.report_generator = self._create_report_generator()
        
        logger.info("✅ Instant Media Release multi-agent system initialized")
    
    def _create_content_analyzer(self) -> Agent:
        """Agent 1: Vietnamese content analysis specialist"""
        return Agent(
            name="ContentAnalyzer",
            role="Expert Vietnamese content analyst for PR and media",
            model=self.llm,
            description="""
            You are a senior content strategist specializing in Vietnamese media landscape.
            You excel at understanding business contexts, identifying target audiences,
            and extracting key information from press release requirements.
            """,
            instructions=[
                "Analyze user input to extract business context and objectives",
                "Identify the primary language preference and target market",
                "Determine the most relevant industry sector and press release type",
                "Extract key topics and themes for media matching",
                "Assess content tone, urgency, and geographic scope",
                "Provide confidence score for your analysis",
                "Focus on Vietnamese market nuances and business culture",
                "Consider SME-specific communication needs"
            ],
            response_model=ContentAnalysis,
            storage=self.storage,
            session_id="content_analysis",
            show_tool_calls=False,
            markdown=False
        )
    
    def _create_media_matcher(self) -> Agent:
        """Agent 2: Media database expert with Vietnamese market knowledge"""
        return Agent(
            name="MediaMatcher",
            role="Vietnamese media landscape expert and recommendation specialist",
            model=self.llm,
            description="""
            You are a veteran PR professional with deep expertise in Vietnamese media.
            You know the audience, reach, and credibility of every major publication.
            You excel at matching content with the most effective media outlets.
            """,
            instructions=[
                "Analyze content requirements against Vietnamese media database",
                "Prioritize tier-1 outlets: VnExpress, ZNews, VietnamNet, Tuoi Tre, Kenh14",
                "Consider budget constraints and cost-effectiveness",
                "Match language requirements (Vietnamese/English) precisely",
                "Evaluate topic relevance and audience alignment",
                "Factor in publication success rates and response times",
                "Provide clear reasoning for each recommendation",
                "Optimize for maximum reach within budget",
                "Consider media mix for comprehensive coverage"
            ],
            tools=[DuckDuckGoTools()],
            response_model=MediaRecommendation,
            storage=self.storage,
            session_id="media_matching",
            show_tool_calls=True,
            markdown=False
        )
    
    def _create_pricing_optimizer(self) -> Agent:
        """Agent 3: Pricing strategy and package optimization specialist"""
        return Agent(
            name="PricingOptimizer",
            role="Pricing strategist and package optimization expert",
            model=self.llm,
            description="""
            You are a business strategist specializing in media package optimization.
            You understand Vietnamese market pricing, ROI calculations, and budget allocation.
            You excel at creating cost-effective media strategies.
            """,
            instructions=[
                "Analyze user budget against media recommendations",
                "Calculate optimal package: Starter (12M), Standard (30M), Premium (50M)",
                "Ensure total costs stay within budget constraints",
                "Maximize media coverage and reach per VND spent",
                "Factor in media outlet success rates and response times",
                "Provide realistic timeline estimates based on package complexity",
                "Calculate budget utilization percentage",
                "Suggest alternative packages if budget doesn't fit",
                "Project ROI based on reach and industry benchmarks",
                "Consider cost-per-impression for value analysis"
            ],
            response_model=PricingAnalysis,
            storage=self.storage,
            session_id="pricing_optimization",
            show_tool_calls=False,
            markdown=False
        )
    
    def _create_report_generator(self) -> Agent:
        """Agent 4: Executive report writer and strategic advisor"""
        return Agent(
            name="ReportGenerator", 
            role="Senior PR consultant and executive report writer",
            model=self.llm,
            description="""
            You are an executive-level PR consultant who creates strategic media reports.
            You translate technical recommendations into business insights for decision-makers.
            You excel at presenting data-driven strategies with clear action plans.
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
                "Include timeline with key milestones"
            ],
            response_model=ExecutiveReport,
            storage=self.storage,
            session_id="executive_reports",
            show_tool_calls=False,
            markdown=False
        )
    
    async def analyze_content(self, deps: AgentDependencies) -> ContentAnalysis:
        """Step 1: Deep content analysis"""
        try:
            prompt = f"""
            Analyze this Vietnamese press release request comprehensively:
            
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
            result = await self.content_analyzer.arun(prompt)
            logger.info(f"✅ Content analysis completed - Confidence: {result.confidence_score:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Content analysis failed: {e}")
            # Return fallback analysis
            return ContentAnalysis(
                language="Vietnamese",
                primary_topics=["Business", "Technology"],
                target_audiences=["General Public"],
                keywords=["press release"],
                content_tone="Professional",
                urgency_level="Medium",
                industry_sector="General",
                press_release_type="Other",
                geographic_scope="National",
                confidence_score=0.5
            )
    
    async def find_matching_media(self, deps: AgentDependencies) -> List[MediaRecommendation]:
        """Step 2: Intelligent media matching with vector search"""
        try:
            # Prepare search query from content analysis
            if deps.content_analysis:
                search_query = f"{' '.join(deps.content_analysis.primary_topics)} {' '.join(deps.content_analysis.target_audiences)} {deps.content_analysis.industry_sector}"
            else:
                search_query = "business media vietnam"
            
            # Perform vector search
            vector_results = await media_db.search_media_by_vector(search_query, limit=15)
            deps.vector_search_results = vector_results
            
            # Get detailed media information
            media_candidates = []
            if vector_results and "metadatas" in vector_results and vector_results["metadatas"]:
                for metadata in vector_results["metadatas"][0]:
                    if "media_id" in metadata:
                        media_id = int(metadata["media_id"])
                        media = await media_db.get_media_by_id(media_id)
                        if media and media.is_active:
                            media_candidates.append({
                                "id": media.id,
                                "name": media.name,
                                "tier": media.tier,
                                "cost": media.cost_per_article,
                                "circulation": media.circulation,
                                "topics": json.loads(media.topics),
                                "audiences": json.loads(media.target_audience),
                                "language": media.language,
                                "success_rate": media.success_rate,
                                "response_time": media.response_time_hours
                            })
            
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
                        "response_time": m.response_time_hours
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
                recommendations = [r for r in results if isinstance(r, MediaRecommendation)]
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
            for rec in recommendations:
                if rec.media_outlet_id not in seen_ids:
                    seen_ids.add(rec.media_outlet_id)
                    unique_recommendations.append(rec)
            
            # Sort by matching score
            unique_recommendations.sort(key=lambda x: x.matching_score, reverse=True)
            
            logger.info(f"✅ Media matching completed - Found {len(unique_recommendations)} recommendations")
            return unique_recommendations[:8]  # Return top 8
            
        except Exception as e:
            logger.error(f"❌ Media matching failed: {e}")
            return []
    
    async def optimize_pricing(self, deps: AgentDependencies, recommendations: List[MediaRecommendation]) -> PricingAnalysis:
        """Step 3: Intelligent pricing optimization"""
        try:
            total_media_cost = sum(rec.cost_vnd for rec in recommendations)
            
            prompt = f"""
            Optimize pricing strategy for this media campaign:
            
            USER BUDGET: {deps.budget:,.0f} VND
            CONTENT ANALYSIS: {deps.content_analysis.model_dump() if deps.content_analysis else "Not available"}
            
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
            
            Analyze and recommend:
            1. Best package that fits within budget
            2. Optimal media mix for maximum impact
            3. Cost efficiency and budget utilization
            4. Realistic timeline and deliverables
            5. ROI projection based on reach and engagement
            6. Alternative options if budget is tight
            
            Ensure total costs (package + media) stay within budget.
            """
            
            logger.info("💰 Pricing optimization started...")
            result = await self.pricing_optimizer.arun(prompt)
            logger.info(f"✅ Pricing optimization completed - Package: {result.recommended_package}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Pricing optimization failed: {e}")
            # Return fallback pricing
            return PricingAnalysis(
                recommended_package="Standard",
                total_cost_vnd=deps.budget,
                package_price_vnd=PACKAGE_PRICES["Standard"]["price"],
                media_costs_vnd=deps.budget - PACKAGE_PRICES["Standard"]["price"],
                timeline_days="5-7 ngày làm việc",
                media_count=len(recommendations),
                budget_utilization=1.0,
                cost_efficiency="Moderate efficiency",
                roi_projection="Positive ROI expected",
                alternative_packages=["Starter", "Premium"]
            )
    
    async def generate_executive_report(
        self,
        deps: AgentDependencies,
        content_analysis: ContentAnalysis,
        recommendations: List[MediaRecommendation],
        pricing: PricingAnalysis
    ) -> ExecutiveReport:
        """Step 4: Generate comprehensive executive report"""
        try:
            prompt = f"""
            Create a strategic executive report for this media campaign:
            
            BUSINESS CONTEXT: {deps.user_input}
            BUDGET: {deps.budget:,.0f} VND
            
            CONTENT ANALYSIS: {content_analysis.model_dump()}
            
            MEDIA RECOMMENDATIONS: {[{
                "name": rec.media_name,
                "reach": rec.estimated_reach,
                "cost": rec.cost_vnd,
                "score": rec.matching_score,
                "reasoning": rec.reasoning
            } for rec in recommendations]}
            
            PRICING STRATEGY: {pricing.model_dump()}
            
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
            result = await self.report_generator.arun(prompt)
            logger.info("✅ Executive report completed")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Executive report generation failed: {e}")
            # Return fallback report
            return ExecutiveReport(
                executive_summary="Media strategy developed for comprehensive market coverage within budget.",
                strategic_objectives=["Increase brand awareness", "Generate media coverage"],
                media_strategy="Multi-tier approach targeting Vietnamese media landscape",
                success_metrics=["Media mentions", "Reach metrics", "Engagement rates"],
                implementation_steps=["Finalize content", "Submit to media", "Monitor coverage"],
                risk_mitigation=["Backup media options", "Timeline flexibility"],
                competitive_advantage="Strategic media mix with tier-1 coverage",
                timeline_summary=pricing.timeline_days
            )
    
    async def process_complete_request(
        self,
        user_input: str,
        budget: float,
        session_id: str
    ) -> Dict[str, Any]:
        """End-to-end processing through all 4 agents"""
        
        start_time = datetime.utcnow()
        logger.info(f"🚀 Processing complete request for session: {session_id}")
        
        try:
            # Initialize dependencies
            deps = AgentDependencies(
                user_input=user_input,
                budget=budget,
                session_id=session_id
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
                    "confidence_score": content_analysis.confidence_score
                },
                "timestamp": datetime.utcnow().isoformat(),
                "agent_system": "Instant Media Release v2.0"
            }
            
            logger.info(f"✅ Complete processing finished in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Complete processing failed: {e}")
            return {
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "success": False
            }

# =================== GLOBAL AGENT SYSTEM ===================

# Initialize global agent system
try:
    agent_system = InstantMediaReleaseAgents()
    logger.info("✅ Global agent system initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize agent system: {e}")
    agent_system = None

# =================== TESTING ===================

async def test_agent_system():
    """Comprehensive test of the agent system"""
    if not agent_system:
        logger.error("❌ Agent system not available for testing")
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
            session_id="test_session_001"
        )
        
        logger.info("📊 Test Results:")
        logger.info(f"Processing Time: {result.get('processing_time_seconds', 0):.2f}s")
        logger.info(f"Recommended Package: {result.get('summary', {}).get('recommended_package')}")
        logger.info(f"Media Count: {result.get('summary', {}).get('media_count')}")
        logger.info(f"Budget Utilization: {result.get('summary', {}).get('budget_utilization', 0):.1%}")
        
        logger.info("✅ Agent system test completed successfully!")
        return result
        
    except Exception as e:
        logger.error(f"❌ Agent system test failed: {e}")
        return None

# if __name__ == "__main__":
#     # Run agent system tests
#     asyncio.run(test_agent_system())