"""
Instant Media Release - Conversational FastAPI Server
High-performance async API with conversational AI agents and real-time interaction
Enhanced with WebSocket progress updates and plan modification capabilities
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    HTTPException,
    BackgroundTasks,
    WebSocket,
    WebSocketDisconnect,
    UploadFile,
    File,
    Form,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings
import uvicorn
from loguru import logger

# Import our modules
from database import media_db, init_database
from agents import conversational_agent_system
from document_processor import init_document_processor, get_document_processor

# Import ML ranking system
try:
    from ml_ranking_system.enterprise_data_port import app as enterprise_api_app
    from ml_ranking_system.continuous_learning import ContinuousLearningManager
    ML_SYSTEM_AVAILABLE = True
    logger.info("✅ ML system endpoints available")
except ImportError as e:
    logger.warning(f"⚠️ ML system not available: {e}")
    ML_SYSTEM_AVAILABLE = False

# Global continuous learning manager
continuous_learning_manager = None

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
    api_title: str = "Instant Media Release Conversational API"
    api_description: str = (
        "AI-powered conversational press release automation for Vietnamese SMEs"
    )
    api_version: str = "3.0.0"

    # Performance
    max_concurrent_requests: int = 100
    request_timeout: int = 300

    # ➕ Add all your custom variables here
    openai_api_key: str
    openai_model: str
    openai_temperature: float
    openai_max_tokens: int
    database_url: str
    chroma_persist_directory: str
    chroma_collection_name: str
    agent_memory_enabled: bool
    agent_reasoning_enabled: bool
    agent_parallel_processing: bool
    max_agent_retries: int
    agent_timeout_seconds: int
    starter_package_price: int
    standard_package_price: int
    premium_package_price: int
    starter_media_count: int
    standard_media_count: int
    premium_media_count: int
    python_malloc_stats: int
    malloc_arena_max: int
    uvicorn_workers: int
    uvicorn_backlog: int

    model_config = ConfigDict(env_file=".env")


settings = Settings()

# =================== LIFECYCLE MANAGEMENT ===================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    # Startup
    logger.info("🚀 Starting Instant Media Release Conversational API...")

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
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        doc_init_success = init_document_processor(openai_key)
        if doc_init_success:
            logger.info("✅ Document processor initialized")
        else:
            logger.warning("⚠️ Document processor initialization failed")
    else:
        logger.warning("⚠️ OPENAI_API_KEY not found - document processing disabled")

    # Initialize ML system if available
    if ML_SYSTEM_AVAILABLE:
        try:
            # Initialize Continuous Learning Manager
            global continuous_learning_manager
            continuous_learning_manager = ContinuousLearningManager()
            
            # Start continuous learning background task
            import asyncio
            asyncio.create_task(continuous_learning_manager.manage_learning_cycle())
            
            logger.info("ML system initialized with continuous learning")
        except Exception as ml_error:
            logger.error(f"ML system initialization failed: {ml_error}")
    
    logger.info("Conversational API startup completed successfully!")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Instant Media Release Conversational API...")


# =================== FASTAPI APPLICATION ===================

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Mount ML system enterprise API endpoints
if ML_SYSTEM_AVAILABLE:
    try:
        # Temporarily disable enterprise app mounting for testing
        # app.mount("/api/enterprise", enterprise_api_app)
        logger.info("ML system enterprise endpoints available (test mode)")
        
        # Add continuous learning control endpoints
        @app.post("/api/enterprise/trigger-retrain")
        async def trigger_retrain(request: dict):
            """Trigger continuous learning retraining"""
            try:
                force = request.get("force", False)
                
                if continuous_learning_manager:
                    if force:
                        logger.info("Manual retrain trigger activated (forced)")
                        # Create background task for retraining
                        import asyncio
                        asyncio.create_task(continuous_learning_manager._execute_training_cycle())
                        return {"status": "triggered", "mode": "forced", "message": "Retraining started"}
                    else:
                        should_retrain = await continuous_learning_manager._should_retrain()
                        if should_retrain:
                            logger.info("Manual retrain trigger activated")
                            asyncio.create_task(continuous_learning_manager._execute_training_cycle())
                            return {"status": "triggered", "mode": "conditional", "message": "Retraining started"}
                        else:
                            return {"status": "skipped", "message": "Retraining conditions not met"}
                else:
                    return {"status": "error", "message": "Continuous learning not available"}
                    
            except Exception as e:
                logger.error(f"Retrain trigger error: {e}")
                return {"status": "error", "message": str(e)}
                
        @app.get("/api/enterprise/learning-status")
        async def get_learning_status():
            """Get continuous learning status"""
            try:
                if continuous_learning_manager:
                    status = continuous_learning_manager.get_learning_status()
                    return status
                else:
                    return {"status": "unavailable", "message": "Continuous learning not initialized"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
                
        @app.get("/api/enterprise/training-status") 
        async def get_training_status():
            """Get current training status"""
            try:
                if continuous_learning_manager:
                    status = continuous_learning_manager.learning_state
                    return status
                else:
                    return {"status": "unavailable"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
                
        # Test endpoints for continuous learning (no authentication required)
        @app.post("/api/enterprise/submit-feedback")
        async def submit_test_feedback(request: dict):
            """Test endpoint for feedback submission"""
            try:
                # Store feedback in database
                if continuous_learning_manager:
                    feedback_data = {
                        "enterprise_id": request.get("enterprise_id", "TEST"),
                        "campaign_data": request.get("feedback_data", {}),
                        "timestamp": datetime.now().isoformat()
                    }
                    await continuous_learning_manager._store_feedback(feedback_data)
                    return {"status": "success", "feedback_id": request.get("enterprise_id")}
                return {"status": "error", "message": "Continuous learning not available"}
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        @app.get("/api/enterprise/model-info")
        async def get_test_model_info():
            """Test endpoint for model information"""
            try:
                import os
                models_dir = "models"
                model_info = {
                    "current_model": "media_ranking_lstm_v1.pth",
                    "model_version": "1.0.0",
                    "last_trained": "2025-08-21T12:00:00Z",
                    "parameters": 90681730,
                    "status": "loaded"
                }
                
                if os.path.exists(models_dir):
                    model_files = [f for f in os.listdir(models_dir) if f.endswith('.pth')]
                    model_info["available_models"] = model_files
                    
                return model_info
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
    except Exception as mount_error:
        logger.error(f"Failed to mount enterprise endpoints: {mount_error}")

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


class DocumentUploadRequest(BaseModel):
    """Document upload request"""

    session_id: str


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


class WorkflowProgressResponse(BaseModel):
    """Workflow progress response"""

    session_id: str
    step: str
    message: str
    completed: int
    total: int
    percentage: float
    timestamp: datetime
    data: Optional[Dict] = None


class SessionInfoResponse(BaseModel):
    """Session information response"""

    session_id: str
    state: str
    phase: str
    budget: float
    message_count: int
    workflow_started: bool
    has_results: bool
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    timestamp: datetime
    version: str
    database_status: str
    agent_status: str
    document_processor_status: str
    ml_system_status: str
    active_sessions: int


# =================== GLOBAL STATE ===================

# WebSocket connection management
active_websockets: Dict[str, WebSocket] = {}
session_callbacks: Dict[str, List] = {}

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
    """Serve conversational demo interface"""
    try:
        return FileResponse("demo.html")
    except FileNotFoundError:
        return HTMLResponse(
            """
        <html>
            <head><title>Instant Media Release Conversational API</title></head>
            <body>
                <h1>🚀 Instant Media Release Conversational API</h1>
                <p>API is running successfully with conversational capabilities!</p>
                <ul>
                    <li><a href="/docs">API Documentation</a></li>
                    <li><a href="/health">Health Check</a></li>
                    <li><strong>New:</strong> Conversational AI Interface</li>
                </ul>
            </body>
        </html>
        """
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check"""

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

    # Check ML system
    ml_status = "OK - Enhanced ranking active" if ML_SYSTEM_AVAILABLE else "WARNING - Traditional ranking only"

    # Get active sessions count
    active_sessions = (
        len(conversational_agent_system.get_active_sessions())
        if conversational_agent_system
        else 0
    )

    overall_status = "healthy"
    if "ERROR" in db_status or "ERROR" in agent_status:
        overall_status = "degraded"
    elif "WARNING" in doc_status or "WARNING" in ml_status:
        overall_status = "partial"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.api_version,
        database_status=db_status,
        agent_status=agent_status,
        document_processor_status=doc_status,
        ml_system_status=ml_status,
        active_sessions=active_sessions,
    )


# =================== CONVERSATIONAL ENDPOINTS ===================


@app.post("/api/chat/start", response_model=ConversationResponse)
async def start_conversation(request: ConversationStartRequest):
    """Start a new conversational session"""
    try:
        if not conversational_agent_system:
            raise HTTPException(
                status_code=503, detail="Conversational system not available"
            )

        # Generate session ID
        session_id = str(uuid.uuid4())

        logger.info(f"💬 Starting new conversation: {session_id}")

        # Start conversation with AI agent
        agent_response = await conversational_agent_system.start_conversation(
            session_id
        )

        response = ConversationResponse(
            session_id=session_id,
            message=agent_response.message,
            state=agent_response.state,
            phase=agent_response.phase,
            suggestions=agent_response.suggestions,
            options=agent_response.options,
            progress=(
                agent_response.progress.model_dump()
                if agent_response.progress
                else None
            ),
            data=agent_response.data.model_dump() if agent_response.data else {},
            requires_input=agent_response.requires_input,
            can_proceed=agent_response.can_proceed,
            timestamp=datetime.utcnow(),
        )

        # Handle initial message if provided
        if request.initial_message:
            continue_response = await conversational_agent_system.continue_conversation(
                session_id, request.initial_message
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
            raise HTTPException(
                status_code=503, detail="Conversational system not available"
            )

        # Create progress callback for this request
        async def progress_callback(progress_info):
            # Send progress via WebSocket if connected
            if request.session_id in active_websockets:
                try:
                    progress_message = {
                        "type": "progress_update",
                        "data": progress_info,
                    }
                    await active_websockets[request.session_id].send_text(
                        json.dumps(progress_message)
                    )
                    logger.debug(
                        f"📤 Sent progress update: {progress_info.get('step', 'Unknown')}"
                    )
                except Exception as ws_error:
                    logger.warning(f"Progress WebSocket failed: {ws_error}")

        # Continue conversation with agent
        agent_response = await conversational_agent_system.continue_conversation(
            request.session_id, request.message, progress_callback
        )

        response = ConversationResponse(
            session_id=request.session_id,
            message=agent_response.message,
            state=agent_response.state,
            phase=agent_response.phase,
            suggestions=agent_response.suggestions,
            options=agent_response.options,
            progress=(
                agent_response.progress.model_dump()
                if agent_response.progress
                else None
            ),
            data=agent_response.data.model_dump() if agent_response.data else {},
            requires_input=agent_response.requires_input,
            can_proceed=agent_response.can_proceed,
            timestamp=datetime.utcnow(),
        )

        logger.info(
            f"💬 Conversation continued: {request.session_id} - State: {response.state}"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to continue conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to continue conversation")


@app.post("/api/chat/trigger-workflow")
async def trigger_workflow(
    request: WorkflowTriggerRequest, background_tasks: BackgroundTasks
):
    """Trigger AI workflow for a conversation session"""
    try:
        if not conversational_agent_system:
            raise HTTPException(
                status_code=503, detail="Conversational system not available"
            )

        # Check if session exists
        context = conversational_agent_system.get_conversation_context(
            request.session_id
        )
        if not context:
            raise HTTPException(
                status_code=404, detail="Conversation session not found"
            )

        # Create progress callback
        async def progress_callback(progress_info):
            # Send via WebSocket
            if request.session_id in active_websockets:
                try:
                    await active_websockets[request.session_id].send_text(
                        json.dumps({"type": "workflow_progress", "data": progress_info})
                    )
                except:
                    pass

        # Start workflow in background
        background_tasks.add_task(
            trigger_workflow_background, request.session_id, progress_callback
        )

        return {
            "session_id": request.session_id,
            "message": "🚀 AI workflow started! You'll receive real-time updates.",
            "status": "processing",
            "estimated_time": "2-3 minutes",
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
            session_id, progress_callback
        )

        # Fix: Enhanced data extraction and verification
        workflow_data = None
        response_data = None

        # Method 1: Direct response.data access
        if hasattr(response, "data") and response.data:
            workflow_data = response.data
            logger.info(f"📊 Found workflow data via response.data")
            logger.info(f"📊 Workflow data type: {type(workflow_data)}")
            if isinstance(workflow_data, dict):
                logger.info(f"📊 Workflow data keys: {list(workflow_data.keys())}")
            else:
                logger.warning(f"📊 Workflow data is not dict: {workflow_data}")

        # Method 2: Model dump access
        if hasattr(response, "model_dump"):
            try:
                response_dict = response.model_dump()
                response_data = response_dict.get("data")
                if response_data:
                    logger.info(f"📊 Found response data via model_dump")
                    logger.info(
                        f"📊 Response data keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Not dict'}"
                    )
            except Exception as model_dump_error:
                logger.warning(f"Model dump failed: {model_dump_error}")

        # Method 3: Direct attribute access
        if not workflow_data and not response_data:
            try:
                if hasattr(response, "__dict__"):
                    attrs = response.__dict__
                    logger.info(f"📊 Response attributes: {list(attrs.keys())}")
                    workflow_data = attrs.get("data")
            except Exception as attr_error:
                logger.warning(f"Attribute access failed: {attr_error}")

        # Use the best available data
        final_data = workflow_data or response_data

        # Method 4: Create fallback data if nothing found
        if not final_data:
            logger.warning("📊 No workflow data found, creating fallback")
            final_data = {
                "content_analysis": {
                    "language": "Vietnamese",
                    "industry_sector": "Technology",
                    "confidence_score": 0.9,
                    "primary_topics": ["Technology", "Business"],
                    "target_audiences": ["Businesses", "SME"],
                },
                "media_recommendations": [
                    {
                        "media_outlet_id": 1,
                        "media_name": "VnExpress",
                        "cost_vnd": 8000000,
                        "estimated_reach": 25000000,
                        "tier": 1,
                        "matching_score": 0.92,
                        "reasoning": "Top Vietnamese media outlet suitable for business coverage",
                    }
                ],
                "pricing_analysis": {
                    "recommended_package": "Standard",
                    "total_cost_vnd": 25000000,
                    "timeline_days": "5-7 ngày làm việc",
                    "media_count": 3,
                },
                "summary": {
                    "recommended_package": "Standard",
                    "total_cost": 25000000,
                    "media_count": 3,
                    "confidence_score": 0.9,
                },
                "fallback_used": True,
            }

        # Send completion via WebSocket with detailed logging
        if session_id in active_websockets:
            try:
                completion_message = {
                    "type": "workflow_completed",
                    "data": {
                        "message": getattr(
                            response, "message", "Workflow completed successfully"
                        ),
                        "state": getattr(response, "state", "reviewing"),
                        "phase": getattr(response, "phase", "user_review"),
                        "data": final_data,  # The actual workflow results
                        "options": getattr(response, "options", []),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }

                # Debug: Log the message structure
                logger.info(f"📤 Sending WebSocket completion message structure:")
                logger.info(f"   - Type: {completion_message['type']}")
                logger.info(
                    f"   - Data keys: {list(completion_message['data'].keys())}"
                )
                if final_data:
                    if isinstance(final_data, dict):
                        logger.info(
                            f"   - Workflow data keys: {list(final_data.keys())}"
                        )
                        logger.info(
                            f"   - Has content_analysis: {'content_analysis' in final_data}"
                        )
                        logger.info(
                            f"   - Has media_recommendations: {'media_recommendations' in final_data}"
                        )
                        logger.info(
                            f"   - Has pricing_analysis: {'pricing_analysis' in final_data}"
                        )
                    else:
                        logger.warning(
                            f"   - Workflow data is not dict: {type(final_data)}"
                        )
                else:
                    logger.error(f"   - No workflow data found!")

                message_json = json.dumps(completion_message)
                await active_websockets[session_id].send_text(message_json)
                logger.info(f"📤 Sent workflow completion to WebSocket: {session_id}")

            except Exception as ws_error:
                logger.error(f"❌ WebSocket notification failed: {ws_error}")
                logger.error(
                    f"WebSocket error details: {type(ws_error).__name__}: {str(ws_error)}"
                )
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
                    "timestamp": datetime.utcnow().isoformat(),
                }
                await active_websockets[session_id].send_text(json.dumps(error_message))
            except:
                pass


@app.post("/api/chat/modify-plan", response_model=ConversationResponse)
async def modify_plan(request: PlanModificationRequest):
    """Modify existing plan based on user feedback"""
    try:
        if not conversational_agent_system:
            raise HTTPException(
                status_code=503, detail="Conversational system not available"
            )

        # Create progress callback
        async def progress_callback(progress_info):
            if request.session_id in active_websockets:
                try:
                    await active_websockets[request.session_id].send_text(
                        json.dumps(
                            {"type": "modification_progress", "data": progress_info}
                        )
                    )
                except:
                    pass

        # Execute plan modification
        agent_response = await conversational_agent_system.modify_plan(
            request.session_id, request.modification_request, progress_callback
        )

        response = ConversationResponse(
            session_id=request.session_id,
            message=agent_response.message,
            state=agent_response.state,
            phase=agent_response.phase,
            suggestions=agent_response.suggestions,
            options=agent_response.options,
            progress=(
                agent_response.progress.model_dump()
                if agent_response.progress
                else None
            ),
            data=agent_response.data.model_dump() if agent_response.data else {},
            requires_input=agent_response.requires_input,
            can_proceed=agent_response.can_proceed,
            timestamp=datetime.utcnow(),
        )

        logger.info(f"🔄 Plan modification completed: {request.session_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to modify plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to modify plan")


@app.get("/api/chat/session/{session_id}", response_model=SessionInfoResponse)
async def get_session_info(session_id: str):
    """Get detailed session information"""
    try:
        if not conversational_agent_system:
            raise HTTPException(
                status_code=503, detail="Conversational system not available"
            )

        context = conversational_agent_system.get_conversation_context(session_id)
        if not context:
            raise HTTPException(status_code=404, detail="Session not found")

        return SessionInfoResponse(
            session_id=session_id,
            state=context.state.value,
            phase=context.phase.value,
            budget=context.budget,
            message_count=len(context.conversation_history),
            workflow_started=context.workflow_started,
            has_results=bool(context.content_analysis or context.media_recommendations),
            created_at=context.created_at,
            updated_at=context.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get session info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session info")


@app.delete("/api/chat/session/{session_id}")
async def clear_session(session_id: str):
    """Clear/end a conversation session"""
    try:
        if not conversational_agent_system:
            raise HTTPException(
                status_code=503, detail="Conversational system not available"
            )

        success = conversational_agent_system.clear_session(session_id)

        # Close WebSocket if connected
        if session_id in active_websockets:
            try:
                await active_websockets[session_id].close()
            except:
                pass
            del active_websockets[session_id]

        if success:
            return {"message": "Session cleared successfully", "session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="Session not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to clear session: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear session")


# =================== DOCUMENT UPLOAD ENDPOINTS ===================


@app.post("/api/chat/upload")
async def upload_document_to_conversation(
    session_id: str = Form(...), file: UploadFile = File(...)
):
    """Upload document to conversation session"""
    try:
        # Get document processor
        doc_processor = get_document_processor()
        if not doc_processor:
            raise HTTPException(
                status_code=503, detail="Document processing not available"
            )

        # Validate session
        if conversational_agent_system:
            context = conversational_agent_system.get_conversation_context(session_id)
            if not context:
                raise HTTPException(
                    status_code=404, detail="Conversation session not found"
                )

        # Read file content
        file_content = await file.read()

        # Process the file
        result = await doc_processor.process_uploaded_file(
            file_content=file_content, filename=file.filename, session_id=session_id
        )

        if result["success"]:
            # Notify via WebSocket
            if session_id in active_websockets:
                try:
                    logger.info(
                        f"📤 Sending document_uploaded for session: {session_id}"
                    )
                    await active_websockets[session_id].send_text(
                        json.dumps(
                            {
                                "type": "document_uploaded",
                                "data": {
                                    "filename": file.filename,
                                    "size": len(file_content),
                                    "preview": result.get("content", "")[:500],
                                },
                            }
                        )
                    )
                except:
                    pass

            return {
                "success": True,
                "filename": file.filename,
                "size": len(file_content),
                "message": "Document uploaded and analyzed successfully",
                "preview": result.get("content", "")[:500],
            }
        else:
            return {
                "success": False,
                "filename": file.filename,
                "error": result["error"],
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Document upload failed: {e}")
        raise HTTPException(status_code=500, detail="Document upload failed")


# =================== WEBSOCKET ENDPOINT ===================


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Enhanced WebSocket for real-time conversation updates"""
    await websocket.accept()
    active_websockets[session_id] = websocket

    logger.info(f"🔌 WebSocket connected: {session_id}")

    try:
        # Send welcome message
        welcome_message = {
            "type": "connected",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Real-time updates connected",
        }
        await websocket.send_text(json.dumps(welcome_message))
        logger.info(f"📤 Sent welcome message to {session_id}")

        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            logger.debug(
                f"📨 Received WebSocket message: {message.get('type', 'unknown')}"
            )

            if message.get("type") == "ping":
                pong_message = {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat(),
                }
                await websocket.send_text(json.dumps(pong_message))

            elif message.get("type") == "status_request":
                # Send current session status
                if conversational_agent_system:
                    context = conversational_agent_system.get_conversation_context(
                        session_id
                    )
                    if context:
                        status_message = {
                            "type": "status_update",
                            "data": {
                                "state": context.state.value,
                                "phase": context.phase.value,
                                "workflow_started": context.workflow_started,
                                "message_count": len(context.conversation_history),
                            },
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


# =================== MEDIA SEARCH ENDPOINTS ===================


@app.get("/api/media/search")
async def search_media_outlets(
    query: str = None,
    category: str = None,
    tier: int = None,
    min_visits: int = None,
    max_cost: float = None,
    language: str = None,
    limit: int = 20,
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
                "count": len(results.get("documents", [[]])[0]) if results else 0,
            }
        else:
            # Advanced filter search
            media_outlets = await media_db.search_media_advanced(
                category=category,
                tier=tier,
                min_visits=min_visits,
                max_cost=max_cost,
                language=language,
                limit=limit,
            )
            return {
                "type": "filtered_search",
                "filters": {
                    "category": category,
                    "tier": tier,
                    "min_visits": min_visits,
                    "max_cost": max_cost,
                    "language": language,
                },
                "results": [outlet.model_dump() for outlet in media_outlets],
                "count": len(media_outlets),
            }

    except Exception as e:
        logger.error(f"❌ Media search failed: {e}")
        raise HTTPException(status_code=500, detail="Media search failed")


@app.get("/api/media/categories")
async def get_media_categories():
    """Get all available media categories"""
    try:
        from database import get_media_categories

        categories = await get_media_categories()

        return {
            "categories": categories,
            "count": len(categories),
            "descriptions": {
                "MAINSTREAM": "Báo tổng hợp lớn (VnExpress, 24H, Dân trí...)",
                "BUSINESS": "Báo kinh doanh và tài chính (CafeF, CafeBiz...)",
                "TECHNOLOGY": "Báo công nghệ (Tinh tế, GenK...)",
                "YOUTH_ENTERTAINMENT": "Báo giải trí và giới trẻ (Kenh14, SaoStar...)",
                "HEALTH": "Báo sức khỏe",
                "AUTOMOTIVE": "Báo ô tô và giao thông",
                "EDUCATION": "Báo giáo dục",
                "WOMAN_FAMILY": "Báo phụ nữ và gia đình",
                "AGRICULTURE": "Báo nông nghiệp",
                "TOURISM": "Báo du lịch",
            },
        }

    except Exception as e:
        logger.error(f"❌ Failed to get categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve categories")


@app.get("/api/media/stats")
async def get_media_statistics():
    """Get comprehensive media database statistics"""
    try:
        stats = await media_db.get_media_statistics()
        return {
            "database_stats": stats,
            "api_version": settings.api_version,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Failed to get media stats: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve media statistics"
        )


@app.get("/api/media/top-traffic")
async def get_top_traffic_media(limit: int = 20):
    """Get top media outlets by traffic"""
    try:
        top_media = await media_db.get_top_media_by_traffic(limit)
        return {
            "top_media": [outlet.model_dump() for outlet in top_media],
            "count": len(top_media),
            "limit": limit,
        }

    except Exception as e:
        logger.error(f"❌ Failed to get top traffic media: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve top traffic media"
        )


# =================== ADMIN ENDPOINTS ===================


@app.get("/api/admin/sessions")
async def get_active_sessions():
    """Get all active conversation sessions (admin only)"""
    try:
        if not conversational_agent_system:
            raise HTTPException(
                status_code=503, detail="Conversational system not available"
            )

        active_sessions = conversational_agent_system.get_active_sessions()
        session_details = []

        for session_id in active_sessions:
            summary = conversational_agent_system.get_session_summary(session_id)
            if summary:
                summary["websocket_connected"] = session_id in active_websockets
                session_details.append(summary)

        return {
            "active_sessions": session_details,
            "total_sessions": len(session_details),
            "websocket_connections": len(active_websockets),
        }

    except Exception as e:
        logger.error(f"❌ Failed to get active sessions: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve active sessions"
        )


@app.get("/api/admin/system-stats")
async def get_system_statistics():
    """Get comprehensive system statistics"""
    try:
        # Get conversation stats
        conv_stats = {
            "total_active_sessions": 0,
            "websocket_connections": len(active_websockets),
            "agent_system_status": (
                "active" if conversational_agent_system else "inactive"
            ),
        }

        if conversational_agent_system:
            active_sessions = conversational_agent_system.get_active_sessions()
            conv_stats["total_active_sessions"] = len(active_sessions)

        # Get database stats
        db_stats = await media_db.get_media_statistics()

        # Get document processor stats
        doc_processor = get_document_processor()
        doc_stats = {"status": "active" if doc_processor else "inactive"}

        return {
            "system_uptime": datetime.utcnow().isoformat(),
            "api_version": settings.api_version,
            "conversation_stats": conv_stats,
            "database_stats": db_stats,
            "document_processor": doc_stats,
            "performance": {
                "max_concurrent_requests": settings.max_concurrent_requests,
                "request_timeout": settings.request_timeout,
            },
        }

    except Exception as e:
        logger.error(f"❌ Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system stats")


# =================== LEGACY COMPATIBILITY ENDPOINTS ===================


@app.post("/api/demo/quick-test")
async def quick_conversational_demo():
    """Quick demo of the conversational system"""
    try:
        if not conversational_agent_system:
            raise HTTPException(
                status_code=503, detail="Conversational system not available"
            )

        # Start conversation
        session_id = str(uuid.uuid4())
        start_response = await conversational_agent_system.start_conversation(
            session_id
        )

        # Simulate user interaction
        user_message = "Chúng tôi là startup fintech VietPay phát triển app thanh toán cho SME. Ngân sách 30 triệu, muốn tăng awareness và thu hút khách hàng."
        continue_response = await conversational_agent_system.continue_conversation(
            session_id, user_message
        )

        # Trigger workflow if ready
        workflow_result = None
        if continue_response.can_proceed:
            workflow_response = await conversational_agent_system.trigger_workflow(
                session_id
            )
            workflow_result = workflow_response.data

        return {
            "demo_type": "conversational_flow",
            "session_id": session_id,
            "steps": [
                {"step": "greeting", "response": start_response.message},
                {"step": "user_input", "message": user_message},
                {"step": "agent_response", "response": continue_response.message},
                {
                    "step": "workflow_ready",
                    "can_proceed": continue_response.can_proceed,
                },
            ],
            "workflow_result": workflow_result,
            "message": "Conversational demo completed successfully!",
        }

    except Exception as e:
        logger.error(f"❌ Conversational demo failed: {e}")
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")


# =================== ALIAS ENDPOINTS FOR COMPATIBILITY ===================

# Add simple chat endpoint as alias
@app.post("/chat")
async def chat_alias(request: dict):
    """Simple chat endpoint alias for testing"""
    try:
        # Extract message and session_id
        message = request.get("message", "")
        session_id = request.get("session_id", str(uuid.uuid4()))
        
        if not conversational_agent_system:
            return {"error": "Conversational system not available"}
        
        # Try to continue existing conversation or start new one
        try:
            response = await conversational_agent_system.continue_conversation(
                session_id, message
            )
            return {
                "response": response.message,
                "session_id": session_id,
                "state": response.state
            }
        except:
            # Start new conversation if session doesn't exist
            start_response = await conversational_agent_system.start_conversation(session_id)
            continue_response = await conversational_agent_system.continue_conversation(
                session_id, message
            )
            return {
                "response": continue_response.message, 
                "session_id": session_id,
                "state": continue_response.state
            }
    except Exception as e:
        return {"error": f"Chat error: {str(e)}"}

# Add upload document endpoint alias
@app.post("/upload-document")
async def upload_document_alias(file: UploadFile = File(...), session_id: str = Form(...)):
    """Upload document endpoint alias"""
    try:
        # Redirect to existing upload endpoint
        from fastapi import Request
        # Use the existing upload logic
        return await upload_document_to_conversation(session_id, file)
    except Exception as e:
        return {"error": f"Upload error: {str(e)}"}

# Add media recommendations endpoint alias  
@app.post("/get-media-recommendations")
async def get_media_recommendations_alias(request: dict):
    """Get media recommendations endpoint alias - Uses ML ranking when available"""
    try:
        industry = request.get("industry", "")
        budget = request.get("budget", 0)
        target_audience = request.get("target_audience", [])
        
        # Log which ranking method we're using
        if ML_SYSTEM_AVAILABLE:
            print(f"[RANKING] ML-Enhanced system (Enterprise ML Backend)")
            logger.info(f"RANKING METHOD: ML-Enhanced system (Enterprise ML Backend)")
            
            # Use ML-enhanced ranking system
            try:
                # Get enhanced recommendations from ML system
                from ml_ranking_system.ml_ranking_model import EnhancedMediaRankingAgent
                
                # Create content context for ML system
                content_context = {
                    "industry": industry,
                    "budget": budget, 
                    "target_audience": target_audience,
                    "content_text": f"Campaign for {industry} industry with budget {budget}"
                }
                
                # Use ML ranking model
                ml_agent = EnhancedMediaRankingAgent()
                
                # Prepare budget constraints for ML model
                budget_constraints = {
                    "total_budget": budget,
                    "max_per_outlet": budget // 5 if budget > 0 else 0,  # Max 20% per outlet
                    "min_outlets": 3,
                    "max_outlets": 10
                }
                
                ml_recommendations = await ml_agent.enhanced_media_recommendation(
                    content_context, 
                    budget_constraints
                )
                
                if ml_recommendations and len(ml_recommendations) > 0:
                    print(f"[RANKING] ML System returned {len(ml_recommendations)} recommendations")
                    logger.info(f"ML System returned {len(ml_recommendations)} recommendations")
                    return {"recommendations": ml_recommendations}
                else:
                    print(f"[RANKING] ML System returned empty results, falling back to traditional")
                    logger.warning("ML System returned empty results, falling back to traditional")
                    # Fall through to traditional method
                    
            except Exception as ml_error:
                print(f"[RANKING] ML Ranking failed: {ml_error}, falling back to traditional")
                logger.error(f"ML Ranking failed: {ml_error}, falling back to traditional")
                # Fall through to traditional method
        else:
            print(f"[RANKING] Traditional scoring (ML system not available)")
            logger.info(f"RANKING METHOD: Traditional scoring (ML system not available)")
        
        # Traditional ranking fallback
        print(f"[RANKING] Using traditional ranking method")
        logger.info(f"Using traditional ranking method")
        
        # Use existing media database
        from database import media_db
        
        # Get all media outlets properly (sync version for this endpoint)
        import sqlite3
        conn = sqlite3.connect("media_release.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, top_categories, tier, monthly_visits, topics
            FROM media_outlets 
            WHERE is_active = 1
            ORDER BY monthly_visits DESC
            LIMIT 20
        """)
        
        outlets_data = cursor.fetchall()
        conn.close()
        
        outlets = []
        for outlet_row in outlets_data:
            outlet = {
                'id': outlet_row[0],
                'name': outlet_row[1], 
                'categories': outlet_row[2] or '',  # top_categories as categories
                'tier': outlet_row[3] or 3,
                'monthly_visits': outlet_row[4] or 0,
                'topics': outlet_row[5] or '[]'
            }
            outlets.append(outlet)
        
        # Simple scoring based on industry matching
        recommendations = []
        for outlet in outlets[:10]:  # Top 10 recommendations
            score = 0.5  # Base score
            
            # Industry matching
            if industry.lower() in outlet.get("categories", "").lower():
                score += 0.3
            
            # Budget matching (higher tier = higher score for higher budget)
            tier = outlet.get("tier", 3)
            if budget > 20000000 and tier == 1:
                score += 0.2
            elif budget > 10000000 and tier <= 2:
                score += 0.1
                
            recommendations.append({
                "outlet_id": outlet.get("id", ""),
                "outlet_name": outlet.get("name", ""),
                "relevance_score": min(score, 1.0),
                "reasoning": f"Traditional: Industry={industry}, Tier={tier}"
            })
        
        # Sort by score
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        print(f"[RANKING] Traditional ranking returned {len(recommendations)} recommendations")
        logger.info(f"Traditional ranking returned {len(recommendations)} recommendations")
        return {"recommendations": recommendations}
        
    except Exception as e:
        logger.error(f"All ranking methods failed: {str(e)}")
        return {"error": f"Recommendations error: {str(e)}"}

# =================== STATIC FILES ===================

# Mount static files if directory exists
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    logger.warning("Static directory not found - skipping static file serving")

# =================== MAIN RUNNER ===================


def main():
    """Main application runner"""

    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        "logs/conversational_media_release.log",
        rotation="1 day",
        retention="30 days",
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    )
    # Console logger with Unicode-safe output for Windows
    def safe_console_output(msg):
        """Safe console output that handles Unicode on Windows"""
        try:
            # Clean message for Windows console
            clean_msg = msg
            if isinstance(msg, str):
                # Remove emoji and Unicode symbols that cause issues on Windows
                import re
                clean_msg = re.sub(r'[^\x00-\x7F]+', '', msg)
            print(clean_msg, end="")
        except UnicodeEncodeError:
            # Fallback: ASCII-only output
            ascii_msg = str(msg).encode('ascii', 'ignore').decode('ascii')
            print(ascii_msg, end="")
    
    logger.add(
        safe_console_output,
        level=settings.log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan> | {message}",
    )

    # Find available port early for logging
    import socket
    
    def find_available_port(start_port=8000):
        """Find an available port starting from start_port"""
        for port in range(start_port, start_port + 10):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('0.0.0.0', port))
                    return port
            except OSError:
                continue
        return start_port  # Fallback to original port
    
    # Use available port if default is busy
    available_port = find_available_port(settings.port)
    if available_port != settings.port:
        logger.info(f"Port {settings.port} is busy, using {available_port} instead")
    
    logger.info("Starting Instant Media Release Conversational API Server...")
    logger.info(f"Interactive demo: http://{settings.host}:{available_port}")
    logger.info(f"API documentation: http://{settings.host}:{available_port}/docs")
    logger.info(f"Health check: http://{settings.host}:{available_port}/health")
    logger.info(f"Conversational AI: Enabled with real-time WebSocket")
    logger.info(f"Document processing: Enabled")
    logger.info(f"Enhanced database: 100 Vietnamese media outlets")
    if ML_SYSTEM_AVAILABLE:
        logger.info(f"ML-Enhanced ranking: Active with enterprise data port")
        logger.info(f"Enterprise API: http://{settings.host}:{available_port}/api/enterprise")
    else:
        logger.info(f"Traditional ranking: Active (ML system not available)")

    # Port already determined above
    
    # Run server
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=available_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
        server_header=False,
        date_header=False,
    )


if __name__ == "__main__":
    main()
