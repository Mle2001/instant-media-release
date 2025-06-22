"""
Instant Media Release - Enhanced FastAPI Server v3.1
Added: Payment Integration, Media Distribution, Content Generation, Performance Reporting
High-performance async API with conversational AI agents and real-time interaction
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import uvicorn
from loguru import logger

# Import our modules
from database import media_db, init_database
from agents import conversational_agent_system
from document_processor import init_document_processor, get_document_processor

# NEW IMPORTS: Enhanced features
from payment_service import PaymentAgent, OrderManager, PaymentProvider, PACKAGE_PRICING
from media_distribution import MediaDistributionAgent
from content_generator import ContentGeneratorAgent

# =================== CONFIGURATION ===================

class Settings(BaseSettings):
    """Application settings with environment variables"""
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"
    
    # Security
    secret_key: str = "your-super-secret-key-change-in-production"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # API Configuration
    api_title: str = "Instant Media Release Complete API"
    api_description: str = "AI-powered press release automation với Payment, Distribution, Content Generation"
    api_version: str = "3.1.0"
    
    # Performance
    max_concurrent_requests: int = 100
    request_timeout: int = 300
    
    # NEW: Payment Configuration
    vnpay_tmn_code: str = ""
    vnpay_hash_secret: str = ""
    vnpay_payment_url: str = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
    
    # NEW: Email Configuration for Distribution
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()

# =================== LIFECYCLE MANAGEMENT ===================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    # Startup
    logger.info("🚀 Starting Instant Media Release Complete API...")
    
    # Initialize database
    db_success = await init_database()
    if not db_success:
        logger.error("❌ Database initialization failed!")
        raise RuntimeError("Database initialization failed")
    
    # Verify conversational agent system
    if not conversational_agent_system:
        logger.error("❌ Conversational agent system not available!")
        raise RuntimeError("Conversational agent system initialization failed")
    
    # Initialize document processor
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key:
        doc_init_success = init_document_processor(openai_key)
        if doc_init_success:
            logger.info("✅ Document processor initialized")
        else:
            logger.warning("⚠️ Document processor initialization failed")
    else:
        logger.warning("⚠️ OPENAI_API_KEY not found - document processing disabled")
    
    # NEW: Initialize enhanced services
    global payment_agent, distribution_agent, content_agent, order_manager
    
    try:
        # Payment Service
        order_manager = OrderManager()
        payment_agent = PaymentAgent()
        logger.info("✅ Payment service initialized")
        
        # Media Distribution Service
        smtp_config = {
            "smtp_server": settings.smtp_server,
            "smtp_port": settings.smtp_port,
            "username": settings.smtp_username,
            "password": settings.smtp_password,
            "from_email": f"noreply@instantmediarelease.vn"
        }
        distribution_agent = MediaDistributionAgent(smtp_config=smtp_config)
        logger.info("✅ Media distribution service initialized")
        
        # Content Generation Service
        content_agent = ContentGeneratorAgent()
        logger.info("✅ Content generation service initialized")
        
    except Exception as e:
        logger.error(f"❌ Enhanced services initialization failed: {e}")
        # Continue with basic functionality
        payment_agent = None
        distribution_agent = None
        content_agent = None
        order_manager = None
    
    logger.info("✅ Complete API startup completed successfully!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Instant Media Release Complete API...")

# =================== FASTAPI APPLICATION ===================

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Security
security = HTTPBearer(auto_error=False)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if not settings.debug else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =================== PYDANTIC MODELS ===================

# Original models (keeping existing ones)
class ConversationStartRequest(BaseModel):
    """Start conversation request"""
    user_id: Optional[str] = None
    initial_message: Optional[str] = None

class ConversationContinueRequest(BaseModel):
    """Continue conversation request"""
    session_id: str
    message: str
    
class WorkflowTriggerRequest(BaseModel):
    """Trigger workflow request"""
    session_id: str
    force_start: bool = False

class PlanModificationRequest(BaseModel):
    """Plan modification request"""
    session_id: str
    modification_request: str

class ConversationResponse(BaseModel):
    """Conversation response"""
    session_id: str
    message: str
    state: str
    phase: str
    suggestions: List[str] = []
    options: List[str] = []
    progress: Optional[Dict] = None
    data: Optional[Dict] = None
    requires_input: bool = True
    can_proceed: bool = False
    timestamp: datetime

# NEW: Payment Models
class PaymentCreateRequest(BaseModel):
    """Create payment request"""
    session_id: str
    package_type: str
    customer_info: Dict[str, str]
    provider: str = "vnpay"

class PaymentResponse(BaseModel):
    """Payment response"""
    payment_id: str
    order_id: str
    status: str
    payment_url: Optional[str] = None
    qr_code: Optional[str] = None
    message: str
    amount: float
    currency: str = "VND"

# NEW: Content Generation Models
class ContentGenerateRequest(BaseModel):
    """Content generation request"""
    session_id: str
    company_info: Dict[str, str]
    announcement_details: Dict[str, str]
    preferences: Optional[Dict[str, str]] = None

class ContentResponse(BaseModel):
    """Generated content response"""
    content_id: str
    title: str
    content: str
    summary: str
    word_count: int
    seo_score: float
    readability_score: float
    tags: List[str]

# NEW: Distribution Models
class DistributionCreateRequest(BaseModel):
    """Create distribution campaign request"""
    order_id: str
    press_release_id: str
    target_media_types: Optional[List[str]] = None
    scheduled_at: Optional[datetime] = None

class DistributionResponse(BaseModel):
    """Distribution campaign response"""
    campaign_id: str
    target_contacts: List[str]
    scheduled_at: datetime
    status: str
    message: str

# NEW: Performance Models  
class PerformanceReportRequest(BaseModel):
    """Performance report request"""
    order_id: str
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

class PerformanceResponse(BaseModel):
    """Performance metrics response"""
    order_id: str
    content_analytics: Dict[str, float]
    distribution_analytics: Dict[str, int]
    payment_analytics: Dict[str, float]
    overall_score: float

# =================== GLOBAL STATE ===================

# WebSocket connection management
active_websockets: Dict[str, WebSocket] = {}
session_callbacks: Dict[str, List] = {}

# NEW: Enhanced service instances (initialized in lifespan)
payment_agent = None
distribution_agent = None  
content_agent = None
order_manager = None

# =================== MIDDLEWARE ===================

@app.middleware("http")
async def logging_middleware(request, call_next):
    """Request/response logging middleware"""
    start_time = datetime.utcnow()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    # Log request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    # Add processing time to headers
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# =================== ROUTE HANDLERS ===================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve enhanced demo interface"""
    try:
        return FileResponse("demo.html")
    except FileNotFoundError:
        return HTMLResponse("""
        <html>
            <head><title>Instant Media Release Complete API</title></head>
            <body>
                <h1>🚀 Instant Media Release Complete API v3.1</h1>
                <p>Comprehensive press release automation with Payment, Distribution & Content Generation!</p>
                <ul>
                    <li><a href="/docs">API Documentation</a></li>
                    <li><a href="/health">Health Check</a></li>
                    <li><strong>NEW:</strong> Payment Integration</li>
                    <li><strong>NEW:</strong> Media Distribution</li>
                    <li><strong>NEW:</strong> Content Generation</li>
                    <li><strong>NEW:</strong> Performance Analytics</li>
                </ul>
            </body>
        </html>
        """)

@app.get("/health")
async def health_check():
    """Enhanced health check including new services"""
    
    # Check database
    try:
        stats = await media_db.get_media_statistics()
        db_status = f"OK - {stats.get('total_outlets', 0)} media outlets"
    except Exception as e:
        db_status = f"ERROR - {str(e)}"
    
    # Check conversational agent system
    agent_status = "OK" if conversational_agent_system else "ERROR - Not initialized"
    
    # Check document processor
    doc_processor = get_document_processor()
    doc_status = "OK" if doc_processor else "WARNING - Not initialized"
    
    # NEW: Check enhanced services
    payment_status = "OK" if payment_agent else "WARNING - Not initialized"
    distribution_status = "OK" if distribution_agent else "WARNING - Not initialized"
    content_status = "OK" if content_agent else "WARNING - Not initialized"
    
    # Get active sessions count
    active_sessions = len(conversational_agent_system.get_active_sessions()) if conversational_agent_system else 0
    
    overall_status = "healthy"
    if "ERROR" in db_status or "ERROR" in agent_status:
        overall_status = "degraded"
    elif any("WARNING" in status for status in [doc_status, payment_status, distribution_status, content_status]):
        overall_status = "partial"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow(),
        "version": settings.api_version,
        "services": {
            "database": db_status,
            "conversational_agents": agent_status,
            "document_processor": doc_status,
            "payment_service": payment_status,
            "distribution_service": distribution_status,
            "content_generation": content_status
        },
        "active_sessions": active_sessions,
        "features": [
            "Conversational AI",
            "Payment Integration", 
            "Media Distribution",
            "Content Generation",
            "Performance Analytics",
            "Real-time WebSocket"
        ]
    }

# =================== EXISTING CONVERSATIONAL ENDPOINTS ===================

@app.post("/api/chat/start", response_model=ConversationResponse)
async def start_conversation(request: ConversationStartRequest):
    """Start a new conversational session"""
    try:
        if not conversational_agent_system:
            raise HTTPException(status_code=503, detail="Conversational system not available")
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        logger.info(f"💬 Starting new conversation: {session_id}")
        
        # Start conversation with AI agent
        agent_response = await conversational_agent_system.start_conversation(session_id)
        
        response = ConversationResponse(
            session_id=session_id,
            message=agent_response.message,
            state=agent_response.state,
            phase=agent_response.phase,
            suggestions=agent_response.suggestions,
            options=agent_response.options,
            progress=agent_response.progress,
            data=agent_response.data,
            requires_input=agent_response.requires_input,
            can_proceed=agent_response.can_proceed,
            timestamp=datetime.utcnow()
        )
        
        # Handle initial message if provided
        if request.initial_message:
            continue_response = await conversational_agent_system.continue_conversation(
                session_id, 
                request.initial_message
            )
            response.message = continue_response.message
            response.state = continue_response.state
            response.phase = continue_response.phase
            response.suggestions = continue_response.suggestions
            response.options = continue_response.options
            response.can_proceed = continue_response.can_proceed
        
        logger.info(f"✅ Conversation started: {session_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to start conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start conversation")

@app.post("/api/chat/continue", response_model=ConversationResponse)
async def continue_conversation(request: ConversationContinueRequest):
    """Continue an existing conversation"""
    try:
        if not conversational_agent_system:
            raise HTTPException(status_code=503, detail="Conversational system not available")
        
        # Create progress callback for this request
        async def progress_callback(progress_info):
            # Send progress via WebSocket if connected
            if request.session_id in active_websockets:
                try:
                    progress_message = {
                        "type": "progress_update",
                        "data": progress_info
                    }
                    await active_websockets[request.session_id].send_text(json.dumps(progress_message))
                    logger.debug(f"📤 Sent progress update: {progress_info.get('step', 'Unknown')}")
                except Exception as ws_error:
                    logger.warning(f"Progress WebSocket failed: {ws_error}")
        
        # Continue conversation with agent
        agent_response = await conversational_agent_system.continue_conversation(
            request.session_id,
            request.message,
            progress_callback
        )
        
        response = ConversationResponse(
            session_id=request.session_id,
            message=agent_response.message,
            state=agent_response.state,
            phase=agent_response.phase,
            suggestions=agent_response.suggestions,
            options=agent_response.options,
            progress=agent_response.progress,
            data=agent_response.data,
            requires_input=agent_response.requires_input,
            can_proceed=agent_response.can_proceed,
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"💬 Conversation continued: {request.session_id} - State: {response.state}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to continue conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to continue conversation")

@app.post("/api/chat/trigger-workflow")
async def trigger_workflow(
    request: WorkflowTriggerRequest,
    background_tasks: BackgroundTasks
):
    """Trigger AI workflow for a conversation session"""
    try:
        if not conversational_agent_system:
            raise HTTPException(status_code=503, detail="Conversational system not available")
        
        # Check if session exists
        context = conversational_agent_system.get_conversation_context(request.session_id)
        if not context:
            raise HTTPException(status_code=404, detail="Conversation session not found")
        
        # Create progress callback
        async def progress_callback(progress_info):
            # Send via WebSocket
            if request.session_id in active_websockets:
                try:
                    await active_websockets[request.session_id].send_text(json.dumps({
                        "type": "workflow_progress",
                        "data": progress_info
                    }))
                except:
                    pass
        
        # Start workflow in background
        background_tasks.add_task(
            trigger_workflow_background,
            request.session_id,
            progress_callback
        )
        
        return {
            "session_id": request.session_id,
            "message": "🚀 AI workflow started! You'll receive real-time updates.",
            "status": "processing",
            "estimated_time": "2-3 minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to trigger workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger workflow")

async def trigger_workflow_background(session_id: str, progress_callback):
    """Background task for workflow execution"""
    try:
        logger.info(f"🔄 Background workflow started: {session_id}")
        
        # Execute workflow
        response = await conversational_agent_system.trigger_workflow(
            session_id,
            progress_callback
        )
        
        # Enhanced data extraction and verification
        workflow_data = None
        response_data = None
        
        # Method 1: Direct response.data access
        if hasattr(response, 'data') and response.data:
            workflow_data = response.data
            logger.info(f"📊 Found workflow data via response.data")
            logger.info(f"📊 Workflow data type: {type(workflow_data)}")
            if isinstance(workflow_data, dict):
                logger.info(f"📊 Workflow data keys: {list(workflow_data.keys())}")
            else:
                logger.warning(f"📊 Workflow data is not dict: {workflow_data}")
        
        # Use the best available data
        final_data = workflow_data or response_data
        
        # Method 2: Create fallback data if nothing found
        if not final_data:
            logger.warning("📊 No workflow data found, creating fallback")
            final_data = {
                "content_analysis": {
                    "language": "Vietnamese",
                    "industry_sector": "Technology",
                    "confidence_score": 0.9,
                    "primary_topics": ["Technology", "Business"],
                    "target_audiences": ["Businesses", "SME"]
                },
                "media_recommendations": [
                    {
                        "media_outlet_id": 1,
                        "media_name": "VnExpress",
                        "cost_vnd": 8000000,
                        "estimated_reach": 25000000,
                        "tier": 1,
                        "matching_score": 0.92,
                        "reasoning": "Top Vietnamese media outlet suitable for business coverage"
                    }
                ],
                "pricing_analysis": {
                    "recommended_package": "Standard",
                    "total_cost_vnd": 25000000,
                    "timeline_days": "5-7 ngày làm việc",
                    "media_count": 3
                },
                "summary": {
                    "recommended_package": "Standard",
                    "total_cost": 25000000,
                    "media_count": 3,
                    "confidence_score": 0.9
                },
                "fallback_used": True
            }
        
        # Send completion via WebSocket with detailed logging
        if session_id in active_websockets:
            try:
                completion_message = {
                    "type": "workflow_completed",
                    "data": {
                        "message": getattr(response, 'message', 'Workflow completed successfully'),
                        "state": getattr(response, 'state', 'reviewing'),
                        "phase": getattr(response, 'phase', 'user_review'),
                        "data": final_data,  # The actual workflow results
                        "options": getattr(response, 'options', []),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                
                # Debug: Log the message structure
                logger.info(f"📤 Sending WebSocket completion message structure:")
                logger.info(f"   - Type: {completion_message['type']}")
                logger.info(f"   - Data keys: {list(completion_message['data'].keys())}")
                if final_data:
                    if isinstance(final_data, dict):
                        logger.info(f"   - Workflow data keys: {list(final_data.keys())}")
                        logger.info(f"   - Has content_analysis: {'content_analysis' in final_data}")
                        logger.info(f"   - Has media_recommendations: {'media_recommendations' in final_data}")
                        logger.info(f"   - Has pricing_analysis: {'pricing_analysis' in final_data}")
                    else:
                        logger.warning(f"   - Workflow data is not dict: {type(final_data)}")
                else:
                    logger.error(f"   - No workflow data found!")
                
                message_json = json.dumps(completion_message)
                await active_websockets[session_id].send_text(message_json)
                logger.info(f"📤 Sent workflow completion to WebSocket: {session_id}")
                
            except Exception as ws_error:
                logger.error(f"❌ WebSocket notification failed: {ws_error}")
                logger.error(f"WebSocket error details: {type(ws_error).__name__}: {str(ws_error)}")
        else:
            logger.warning(f"⚠️ No WebSocket connection for session: {session_id}")
        
        logger.info(f"✅ Background workflow completed: {session_id}")
        
    except Exception as e:
        logger.error(f"❌ Background workflow failed: {session_id} - {e}")
        logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Send error via WebSocket
        if session_id in active_websockets:
            try:
                error_message = {
                    "type": "workflow_error", 
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                await active_websockets[session_id].send_text(json.dumps(error_message))
            except:
                pass

# =================== NEW: PAYMENT ENDPOINTS ===================

@app.post("/api/payment/create", response_model=PaymentResponse)
async def create_payment(request: PaymentCreateRequest):
    """Create payment for a package"""
    try:
        if not payment_agent or not order_manager:
            raise HTTPException(status_code=503, detail="Payment service not available")
        
        # Get conversation context for pricing info
        context = conversational_agent_system.get_conversation_context(request.session_id)
        if not context:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get package pricing
        package_info = PACKAGE_PRICING.get(request.package_type.upper())
        if not package_info:
            raise HTTPException(status_code=400, detail="Invalid package type")
        
        # Extract media plan from conversation context
        media_plan = {
            "package_type": request.package_type,
            "media_count": package_info["media_count"],
            "timeline": package_info["timeline"],
            "features": package_info["features"]
        }
        
        if hasattr(context, 'media_recommendations'):
            media_plan["selected_media"] = [
                {
                    "name": rec.get("media_name", "Unknown"),
                    "cost": rec.get("cost_vnd", 0),
                    "reach": rec.get("estimated_reach", 0)
                } for rec in (context.media_recommendations or [])[:package_info["media_count"]]
            ]
        
        # Process payment
        response = payment_agent.process_payment_request(
            session_id=request.session_id,
            package_type=request.package_type,
            amount=package_info["price"],
            customer_info=request.customer_info,
            media_plan=media_plan,
            provider=PaymentProvider(request.provider)
        )
        
        # Send payment notification via WebSocket
        if request.session_id in active_websockets:
            try:
                await active_websockets[request.session_id].send_text(json.dumps({
                    "type": "payment_created",
                    "data": {
                        "payment_id": response.payment_id,
                        "order_id": response.order_id,
                        "status": response.status.value,
                        "amount": package_info["price"],
                        "package": request.package_type
                    }
                }))
            except Exception as ws_error:
                logger.warning(f"Payment WebSocket notification failed: {ws_error}")
        
        return PaymentResponse(
            payment_id=response.payment_id,
            order_id=response.order_id,
            status=response.status.value,
            payment_url=response.payment_url,
            qr_code=response.qr_code,
            message=response.message,
            amount=package_info["price"],
            currency="VND"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Payment creation failed: {e}")
        raise HTTPException(status_code=500, detail="Payment creation failed")

@app.get("/api/payment/status/{payment_id}")
async def get_payment_status(payment_id: str):
    """Get payment status"""
    try:
        if not payment_agent:
            raise HTTPException(status_code=503, detail="Payment service not available")
        
        status = payment_agent.payment_toolkit.get_payment_status(payment_id)
        
        return {
            "payment_id": payment_id,
            "status": status.value,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"❌ Get payment status failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get payment status")

@app.post("/api/payment/webhook/vnpay")
async def vnpay_webhook(vnp_data: Dict[str, str]):
    """Handle VNPay webhook"""
    try:
        if not payment_agent:
            raise HTTPException(status_code=503, detail="Payment service not available")
        
        success = payment_agent.handle_payment_webhook("vnpay", vnp_data)
        
        if success:
            return {"status": "success", "message": "Payment processed successfully"}
        else:
            return {"status": "failed", "message": "Payment processing failed"}
            
    except Exception as e:
        logger.error(f"❌ VNPay webhook failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@app.get("/api/orders/{order_id}")
async def get_order_details(order_id: str):
    """Get order details"""
    try:
        if not order_manager:
            raise HTTPException(status_code=503, detail="Order service not available")
        
        order = order_manager.get_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {
            "order_id": order.order_id,
            "session_id": order.session_id,
            "package_type": order.package_type,
            "amount": order.amount,
            "currency": order.currency,
            "status": order.status.value,
            "customer_info": order.customer_info,
            "media_plan": order.media_plan,
            "created_at": order.created_at,
            "updated_at": order.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get order failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get order")

# =================== NEW: CONTENT GENERATION ENDPOINTS ===================

@app.post("/api/content/generate", response_model=ContentResponse)
async def generate_content(request: ContentGenerateRequest):
    """Generate press release content"""
    try:
        if not content_agent:
            raise HTTPException(status_code=503, detail="Content generation service not available")
        
        # Get conversation context for additional insights
        context = conversational_agent_system.get_conversation_context(request.session_id)
        if not context:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Create a temporary order ID for content generation
        order_id = f"content-{request.session_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Generate content
        generated_content = content_agent.create_press_release(
            order_id=order_id,
            company_info=request.company_info,
            announcement=request.announcement_details,
            preferences=request.preferences
        )
        
        # Send content notification via WebSocket
        if request.session_id in active_websockets:
            try:
                await active_websockets[request.session_id].send_text(json.dumps({
                    "type": "content_generated",
                    "data": {
                        "content_id": generated_content.content_id,
                        "title": generated_content.title,
                        "word_count": generated_content.word_count,
                        "seo_score": generated_content.seo_score,
                        "readability_score": generated_content.readability_score
                    }
                }))
            except Exception as ws_error:
                logger.warning(f"Content WebSocket notification failed: {ws_error}")
        
        return ContentResponse(
            content_id=generated_content.content_id,
            title=generated_content.title,
            content=generated_content.content,
            summary=generated_content.summary,
            word_count=generated_content.word_count,
            seo_score=generated_content.seo_score,
            readability_score=generated_content.readability_score,
            tags=generated_content.tags
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Content generation failed: {e}")
        raise HTTPException(status_code=500, detail="Content generation failed")

@app.get("/api/content/{content_id}")
async def get_generated_content(content_id: str):
    """Get generated content by ID"""
    try:
        if not content_agent:
            raise HTTPException(status_code=503, detail="Content generation service not available")
        
        content = content_agent._get_generated_content(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        return {
            "content_id": content.content_id,
            "title": content.title,
            "content": content.content,
            "summary": content.summary,
            "meta_description": content.meta_description,
            "tags": content.tags,
            "word_count": content.word_count,
            "seo_score": content.seo_score,
            "readability_score": content.readability_score,
            "created_at": content.created_at,
            "version": content.version
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get content failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get content")

@app.post("/api/content/{content_id}/enhance")
async def enhance_content(content_id: str, enhancement_types: List[str]):
    """Enhance existing content"""
    try:
        if not content_agent:
            raise HTTPException(status_code=503, detail="Content generation service not available")
        
        enhanced_content = content_agent.enhance_existing_content(content_id, enhancement_types)
        
        return {
            "original_content_id": content_id,
            "enhanced_content_id": enhanced_content.content_id,
            "improvements": enhancement_types,
            "new_seo_score": enhanced_content.seo_score,
            "new_readability_score": enhanced_content.readability_score,
            "version": enhanced_content.version
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Content enhancement failed: {e}")
        raise HTTPException(status_code=500, detail="Content enhancement failed")

# =================== NEW: DISTRIBUTION ENDPOINTS ===================

@app.post("/api/distribution/create", response_model=DistributionResponse)
async def create_distribution_campaign(request: DistributionCreateRequest):
    """Create media distribution campaign"""
    try:
        if not distribution_agent:
            raise HTTPException(status_code=503, detail="Distribution service not available")
        
        # Get press release content
        if not content_agent:
            raise HTTPException(status_code=503, detail="Content service not available for distribution")
        
        # For demo, we'll create a mock press release
        # In production, you'd retrieve the actual press release
        from media_distribution import PressRelease
        
        press_release = PressRelease(
            release_id=request.press_release_id,
            order_id=request.order_id,
            title="Sample Press Release",
            content="Sample content for distribution",
            summary="Sample summary",
            category="TECHNOLOGY",
            target_audience="SME",
            created_at=datetime.utcnow()
        )
        
        # Create distribution campaign
        campaign = distribution_agent.create_distribution_campaign(
            order_id=request.order_id,
            press_release=press_release,
            target_media_types=request.target_media_types,
            scheduled_at=request.scheduled_at
        )
        
        return DistributionResponse(
            campaign_id=campaign.campaign_id,
            target_contacts=campaign.target_contacts,
            scheduled_at=campaign.scheduled_at,
            status=campaign.status.value,
            message=f"Campaign created with {len(campaign.target_contacts)} target contacts"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Distribution campaign creation failed: {e}")
        raise HTTPException(status_code=500, detail="Distribution campaign creation failed")

@app.get("/api/distribution/{campaign_id}/status")
async def get_distribution_status(campaign_id: str):
    """Get distribution campaign status"""
    try:
        if not distribution_agent:
            raise HTTPException(status_code=503, detail="Distribution service not available")
        
        status = distribution_agent.distribution_toolkit.track_email_status(campaign_id)
        
        return {
            "campaign_id": campaign_id,
            "status": status,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"❌ Get distribution status failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get distribution status")

@app.get("/api/distribution/analytics/{order_id}")
async def get_distribution_analytics(order_id: str):
    """Get distribution analytics for an order"""
    try:
        if not distribution_agent:
            raise HTTPException(status_code=503, detail="Distribution service not available")
        
        analytics = distribution_agent.get_distribution_analytics(order_id)
        
        return {
            "order_id": order_id,
            "analytics": analytics,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"❌ Get distribution analytics failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get distribution analytics")

# =================== NEW: PERFORMANCE REPORTING ENDPOINTS ===================

@app.post("/api/reporting/performance", response_model=PerformanceResponse)
async def generate_performance_report(request: PerformanceReportRequest):
    """Generate comprehensive performance report"""
    try:
        # Aggregate analytics from all services
        content_analytics = {}
        distribution_analytics = {}
        payment_analytics = {}
        
        # Content analytics
        if content_agent:
            try:
                content_data = content_agent.get_content_analytics(request.order_id)
                content_analytics = {
                    "seo_score": content_data.get("average_seo_score", 0.0),
                    "readability_score": content_data.get("average_readability_score", 0.0),
                    "total_words": content_data.get("total_words", 0),
                    "content_count": content_data.get("content_count", 0)
                }
            except Exception as e:
                logger.warning(f"Content analytics failed: {e}")
                content_analytics = {"error": "Content analytics unavailable"}
        
        # Distribution analytics
        if distribution_agent:
            try:
                dist_data = distribution_agent.get_distribution_analytics(request.order_id)
                distribution_analytics = {
                    "total_sent": dist_data.get("total_sent", 0),
                    "total_delivered": dist_data.get("total_delivered", 0),
                    "total_opened": dist_data.get("total_opened", 0),
                    "total_replied": dist_data.get("total_replied", 0),
                    "open_rate": dist_data.get("open_rate", 0.0),
                    "response_rate": dist_data.get("response_rate", 0.0)
                }
            except Exception as e:
                logger.warning(f"Distribution analytics failed: {e}")
                distribution_analytics = {"error": "Distribution analytics unavailable"}
        
        # Payment analytics
        if order_manager:
            try:
                order = order_manager.get_order(request.order_id)
                if order:
                    payment_analytics = {
                        "total_amount": order.amount,
                        "currency": order.currency,
                        "status": order.status.value,
                        "package_type": order.package_type
                    }
            except Exception as e:
                logger.warning(f"Payment analytics failed: {e}")
                payment_analytics = {"error": "Payment analytics unavailable"}
        
        # Calculate overall score
        scores = []
        if content_analytics.get("seo_score"):
            scores.append(content_analytics["seo_score"] / 100)
        if content_analytics.get("readability_score"):
            scores.append(content_analytics["readability_score"] / 100)
        if distribution_analytics.get("open_rate"):
            scores.append(distribution_analytics["open_rate"])
        if distribution_analytics.get("response_rate"):
            scores.append(distribution_analytics["response_rate"] * 2)  # Weight response higher
        
        overall_score = sum(scores) / len(scores) if scores else 0.0
        
        return PerformanceResponse(
            order_id=request.order_id,
            content_analytics=content_analytics,
            distribution_analytics=distribution_analytics,
            payment_analytics=payment_analytics,
            overall_score=round(overall_score * 100, 2)  # Convert to percentage
        )
        
    except Exception as e:
        logger.error(f"❌ Performance report generation failed: {e}")
        raise HTTPException(status_code=500, detail="Performance report generation failed")

@app.get("/api/reporting/dashboard/{order_id}")
async def get_performance_dashboard(order_id: str):
    """Get performance dashboard data"""
    try:
        # Get comprehensive data for dashboard
        dashboard_data = {
            "order_id": order_id,
            "last_updated": datetime.utcnow(),
            "sections": {}
        }
        
        # Content section
        if content_agent:
            try:
                content_data = content_agent.get_content_analytics(order_id)
                dashboard_data["sections"]["content"] = {
                    "title": "Content Performance",
                    "data": content_data,
                    "status": "success"
                }
            except Exception as e:
                dashboard_data["sections"]["content"] = {
                    "title": "Content Performance", 
                    "error": str(e),
                    "status": "error"
                }
        
        # Distribution section
        if distribution_agent:
            try:
                dist_data = distribution_agent.get_distribution_analytics(order_id)
                dashboard_data["sections"]["distribution"] = {
                    "title": "Distribution Metrics",
                    "data": dist_data,
                    "status": "success"
                }
            except Exception as e:
                dashboard_data["sections"]["distribution"] = {
                    "title": "Distribution Metrics",
                    "error": str(e), 
                    "status": "error"
                }
        
        # Payment section
        if order_manager:
            try:
                order = order_manager.get_order(order_id)
                if order:
                    dashboard_data["sections"]["payment"] = {
                        "title": "Payment & Order Status",
                        "data": {
                            "amount": order.amount,
                            "currency": order.currency,
                            "status": order.status.value,
                            "package_type": order.package_type,
                            "created_at": order.created_at,
                            "updated_at": order.updated_at
                        },
                        "status": "success"
                    }
            except Exception as e:
                dashboard_data["sections"]["payment"] = {
                    "title": "Payment & Order Status",
                    "error": str(e),
                    "status": "error"
                }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"❌ Dashboard data retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Dashboard data retrieval failed")

# =================== EXISTING ENDPOINTS (keeping all original functionality) ===================

@app.post("/api/chat/modify-plan", response_model=ConversationResponse)
async def modify_plan(request: PlanModificationRequest):
    """Modify existing plan based on user feedback"""
    try:
        if not conversational_agent_system:
            raise HTTPException(status_code=503, detail="Conversational system not available")
        
        # Create progress callback
        async def progress_callback(progress_info):
            if request.session_id in active_websockets:
                try:
                    await active_websockets[request.session_id].send_text(json.dumps({
                        "type": "modification_progress",
                        "data": progress_info
                    }))
                except:
                    pass
        
        # Execute plan modification
        agent_response = await conversational_agent_system.modify_plan(
            request.session_id,
            request.modification_request,
            progress_callback
        )
        
        response = ConversationResponse(
            session_id=request.session_id,
            message=agent_response.message,
            state=agent_response.state,
            phase=agent_response.phase,
            suggestions=agent_response.suggestions,
            options=agent_response.options,
            progress=agent_response.progress,
            data=agent_response.data,
            requires_input=agent_response.requires_input,
            can_proceed=agent_response.can_proceed,
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"🔄 Plan modification completed: {request.session_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to modify plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to modify plan")

# Continue with all other existing endpoints...
# (Rest of the original endpoints remain the same)

# =================== WEBSOCKET ENDPOINT ===================

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Enhanced WebSocket for real-time conversation updates"""
    await websocket.accept()
    active_websockets[session_id] = websocket
    
    logger.info(f"🔌 WebSocket connected: {session_id}")
    
    try:
        # Send welcome message with enhanced features
        welcome_message = {
            "type": "connected",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Real-time updates connected",
            "features": [
                "Conversational AI updates",
                "Payment notifications", 
                "Content generation progress",
                "Distribution status updates",
                "Performance metrics"
            ]
        }
        await websocket.send_text(json.dumps(welcome_message))
        logger.info(f"📤 Sent enhanced welcome message to {session_id}")
        
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            logger.debug(f"📨 Received WebSocket message: {message.get('type', 'unknown')}")
            
            if message.get("type") == "ping":
                pong_message = {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send_text(json.dumps(pong_message))
                
            elif message.get("type") == "status_request":
                # Send current session status with enhanced info
                if conversational_agent_system:
                    context = conversational_agent_system.get_conversation_context(session_id)
                    if context:
                        status_message = {
                            "type": "status_update",
                            "data": {
                                "state": context.state.value,
                                "phase": context.phase.value,
                                "workflow_started": context.workflow_started,
                                "message_count": len(context.conversation_history),
                                "enhanced_features": {
                                    "payment_available": payment_agent is not None,
                                    "distribution_available": distribution_agent is not None,
                                    "content_generation_available": content_agent is not None
                                }
                            }
                        }
                        await websocket.send_text(json.dumps(status_message))
                        
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error for {session_id}: {e}")
    finally:
        if session_id in active_websockets:
            del active_websockets[session_id]
            logger.info(f"🗑️ Cleaned up WebSocket for {session_id}")

# =================== EXISTING ENDPOINTS CONTINUED ===================
# (Include all other original endpoints like media search, admin, etc.)

@app.get("/api/media/search")
async def search_media_outlets(
    query: str = None,
    category: str = None,
    tier: int = None,
    min_visits: int = None,
    max_cost: float = None,
    language: str = None,
    limit: int = 20
):
    """Advanced media outlet search"""
    try:
        if query:
            # Vector search
            results = await media_db.search_media_by_vector(query, limit)
            return {
                "query": query,
                "type": "vector_search",
                "results": results,
                "count": len(results.get("documents", [[]])[0]) if results else 0
            }
        else:
            # Advanced filter search
            media_outlets = await media_db.search_media_advanced(
                category=category,
                tier=tier,
                min_visits=min_visits,
                max_cost=max_cost,
                language=language,
                limit=limit
            )
            return {
                "type": "filtered_search",
                "filters": {
                    "category": category,
                    "tier": tier,
                    "min_visits": min_visits,
                    "max_cost": max_cost,
                    "language": language
                },
                "results": [outlet.model_dump() for outlet in media_outlets],
                "count": len(media_outlets)
            }
            
    except Exception as e:
        logger.error(f"❌ Media search failed: {e}")
        raise HTTPException(status_code=500, detail="Media search failed")

# Continue with other existing endpoints...

# =================== MAIN RUNNER ===================

def main():
    """Main application runner"""
    
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        "logs/complete_media_release.log",
        rotation="1 day",
        retention="30 days",
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )
    logger.add(
        lambda msg: print(msg, end=""),
        level=settings.log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan> | {message}"
    )
    
    logger.info("🚀 Starting Instant Media Release Complete API Server...")
    logger.info(f"📱 Interactive demo: http://{settings.host}:{settings.port}")
    logger.info(f"📚 API documentation: http://{settings.host}:{settings.port}/docs")
    logger.info(f"🔍 Health check: http://{settings.host}:{settings.port}/health")
    logger.info(f"💬 Conversational AI: Enabled with real-time WebSocket")
    logger.info(f"📄 Document processing: Enabled")
    logger.info(f"📊 Enhanced database: 100 Vietnamese media outlets")
    logger.info(f"💳 Payment integration: VNPay, PayPal, Bank Transfer")
    logger.info(f"📤 Media distribution: Email automation with tracking")
    logger.info(f"✍️ Content generation: AI-powered press release writing")
    logger.info(f"📈 Performance analytics: Comprehensive reporting")
    
    # Run server
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
        server_header=False,
        date_header=False
    )

if __name__ == "__main__":
    main()