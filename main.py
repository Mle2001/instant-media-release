"""
Instant Media Release - Production FastAPI Server
High-performance async API with Agno AI integration
"""

import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import uvicorn
from loguru import logger

# Import our modules
from database import media_db, init_database, UserRequestCreate, get_database
from agents import agent_system

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
    api_title: str = "Instant Media Release API"
    api_description: str = "AI-powered press release automation for Vietnamese SMEs"
    api_version: str = "2.0.0"
    
    # Performance
    max_concurrent_requests: int = 100
    request_timeout: int = 300
    
    class Config:
        env_file = ".env"

settings = Settings()

# =================== LIFECYCLE MANAGEMENT ===================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    # Startup
    logger.info("🚀 Starting Instant Media Release API...")
    
    # Initialize database
    db_success = await init_database()
    if not db_success:
        logger.error("❌ Database initialization failed!")
        raise RuntimeError("Database initialization failed")
    
    # Verify agent system
    if not agent_system:
        logger.error("❌ Agent system not available!")
        raise RuntimeError("Agent system initialization failed")
    
    logger.info("✅ API startup completed successfully!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Instant Media Release API...")

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

class ChatSession(BaseModel):
    """Chat session model"""
    session_id: str
    current_question: int = 1
    answers: Dict[str, Any] = {}
    status: str = "active"
    started_at: datetime
    completed_at: Optional[datetime] = None

class ChatQuestion(BaseModel):
    """Chat question model"""
    id: int
    question: str
    type: str  # choice, multiple_choice, text, file
    options: Optional[List[str]] = None
    placeholder: Optional[str] = None
    max_size: Optional[str] = None

class UserAnswer(BaseModel):
    """User answer model"""
    question_id: int
    answer: Any  # Can be string, list, etc.
    session_id: str

class ProcessingRequest(BaseModel):
    """Agent processing request"""
    session_id: str
    user_data: Dict[str, Any]
    budget: float = Field(default=30000000, description="Budget in VND")

class ProcessingResponse(BaseModel):
    """Agent processing response"""
    success: bool
    session_id: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    database_status: str
    agent_status: str

# =================== GLOBAL STATE ===================

# In-memory storage (use Redis in production)
chat_sessions: Dict[str, Dict] = {}
processing_results: Dict[str, Dict] = {}
active_websockets: Dict[str, WebSocket] = {}

# Chatbot conversation flow
CHATBOT_QUESTIONS = [
    {
        "id": 1,
        "question": "Xin chào! Tôi là ChiCom AI Assistant của Instant Media Release. Bạn đã có bài thông cáo báo chí sẵn sàng chưa?",
        "type": "choice",
        "options": ["Tôi có bản tiếng Việt", "Tôi có bản tiếng Anh", "Tôi chưa có, cần hỗ trợ viết"]
    },
    {
        "id": 2,
        "question": "Bạn có muốn phát triển thêm tài liệu hỗ trợ nào khác không?",
        "type": "choice",
        "options": ["Factsheet chi tiết", "Backgrounder", "Không cần thêm", "Theo đề xuất của chuyên gia", "Tài liệu khác"]
    },
    {
        "id": 3,
        "question": "Ngôn ngữ nào bạn muốn sử dụng cho chiến dịch truyền thông?",
        "type": "choice",
        "options": ["Chỉ tiếng Việt", "Chỉ tiếng Anh", "Song ngữ Việt-Anh", "Tùy theo từng báo"]
    },
    {
        "id": 4,
        "question": "Vui lòng mô tả chi tiết về dự án của bạn (bối cảnh, mục tiêu, đối tượng, sản phẩm/dịch vụ, thông điệp chính và kết quả mong đợi):",
        "type": "text",
        "placeholder": "Ví dụ: Công ty ABC vừa ra mắt ứng dụng fintech mới dành cho SME..."
    },
    {
        "id": 5,
        "question": "Nếu có, vui lòng đính kèm tài liệu bổ sung (tối đa 15MB):",
        "type": "file",
        "max_size": "15MB"
    },
    {
        "id": 6,
        "question": "Chọn các kênh truyền thông mong muốn (có thể chọn nhiều):",
        "type": "multiple_choice",
        "options": [
            "Báo chí tổng hợp (VnExpress, VietnamNet)",
            "Báo kinh doanh (CafeF, CafeBiz)",
            "Báo công nghệ (ICTNews, VnReview)",
            "Báo giải trí (Kenh14, ZNews)",
            "Báo tiếng Anh (Vietnam News, VnExpress International)",
            "Kênh truyền hình toàn quốc",
            "Kênh truyền hình địa phương",
            "Radio/Podcast"
        ]
    },
    {
        "id": 7,
        "question": "Ngân sách dự kiến cho chiến dịch truyền thông này (VND)?",
        "type": "choice",
        "options": [
            "Dưới 15 triệu (Gói Starter)",
            "15-35 triệu (Gói Standard)",
            "35-60 triệu (Gói Premium)",
            "Trên 60 triệu (Gói Enterprise)",
            "Chưa xác định, cần tư vấn"
        ]
    }
]

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
    """Serve demo chatbot interface"""
    try:
        return FileResponse("demo.html")
    except FileNotFoundError:
        return HTMLResponse("""
        <html>
            <head><title>Instant Media Release API</title></head>
            <body>
                <h1>🚀 Instant Media Release API</h1>
                <p>API is running successfully!</p>
                <ul>
                    <li><a href="/docs">API Documentation</a></li>
                    <li><a href="/health">Health Check</a></li>
                </ul>
            </body>
        </html>
        """)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check"""
    
    # Check database
    try:
        media_outlets = await media_db.get_all_media_outlets()
        db_status = f"OK - {len(media_outlets)} media outlets"
    except Exception as e:
        db_status = f"ERROR - {str(e)}"
    
    # Check agent system
    agent_status = "OK" if agent_system else "ERROR - Not initialized"
    
    return HealthResponse(
        status="healthy" if agent_system and "ERROR" not in db_status else "degraded",
        timestamp=datetime.utcnow(),
        version=settings.api_version,
        database_status=db_status,
        agent_status=agent_status
    )

# =================== CHATBOT ENDPOINTS ===================

@app.post("/api/chat/start")
async def start_chat_session():
    """Initialize new chatbot session"""
    try:
        session_id = str(uuid.uuid4())
        
        chat_sessions[session_id] = {
            "session_id": session_id,
            "current_question": 1,
            "answers": {},
            "status": "active",
            "started_at": datetime.utcnow()
        }
        
        first_question = CHATBOT_QUESTIONS[0]
        
        logger.info(f"💬 New chat session started: {session_id}")
        
        return {
            "session_id": session_id,
            "question": first_question,
            "progress": f"1/{len(CHATBOT_QUESTIONS)}",
            "total_questions": len(CHATBOT_QUESTIONS)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to start chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start chat session")

@app.post("/api/chat/answer")
async def submit_chat_answer(answer: UserAnswer):
    """Submit answer and get next question"""
    try:
        session = chat_sessions.get(answer.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Save answer
        session["answers"][str(answer.question_id)] = answer.answer
        
        # Get next question
        next_question_id = answer.question_id + 1
        
        if next_question_id <= len(CHATBOT_QUESTIONS):
            # More questions remaining
            session["current_question"] = next_question_id
            next_question = CHATBOT_QUESTIONS[next_question_id - 1]
            
            return {
                "session_id": answer.session_id,
                "question": next_question,
                "progress": f"{next_question_id}/{len(CHATBOT_QUESTIONS)}",
                "completed": False
            }
        else:
            # All questions completed
            session["status"] = "completed"
            session["completed_at"] = datetime.utcnow()
            
            logger.info(f"✅ Chat session completed: {answer.session_id}")
            
            return {
                "session_id": answer.session_id,
                "completed": True,
                "message": "Cảm ơn bạn! Đang khởi động AI Agents để phân tích yêu cầu...",
                "collected_data": session["answers"],
                "progress": f"{len(CHATBOT_QUESTIONS)}/{len(CHATBOT_QUESTIONS)}"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to submit answer: {e}")
        raise HTTPException(status_code=500, detail="Failed to process answer")

@app.get("/api/chat/session/{session_id}")
async def get_chat_session(session_id: str):
    """Get current session status and data"""
    try:
        session = chat_sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "status": session["status"],
            "current_question": session["current_question"],
            "progress": f"{session['current_question']}/{len(CHATBOT_QUESTIONS)}",
            "answers": session["answers"],
            "started_at": session["started_at"],
            "completed_at": session.get("completed_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get session: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session")

# =================== AI AGENTS ENDPOINTS ===================

@app.post("/api/agents/process", response_model=ProcessingResponse)
async def start_agent_processing(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks
):
    """Start AI agent processing in background"""
    try:
        session = chat_sessions.get(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not agent_system:
            raise HTTPException(status_code=503, detail="Agent system not available")
        
        # Convert chat answers to structured input
        user_input = _format_chat_data_to_text(request.user_data)
        
        # Start background processing
        background_tasks.add_task(
            process_with_agents_background,
            request.session_id,
            user_input,
            request.budget
        )
        
        logger.info(f"🤖 Agent processing started for session: {request.session_id}")
        
        return ProcessingResponse(
            success=True,
            session_id=request.session_id,
            data={
                "message": "AI Agents processing started",
                "estimated_time": "2-3 minutes",
                "status": "processing"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to start agent processing: {e}")
        return ProcessingResponse(
            success=False,
            session_id=request.session_id,
            error=str(e)
        )

async def process_with_agents_background(
    session_id: str,
    user_input: str,
    budget: float
):
    """Background task for agent processing"""
    try:
        start_time = datetime.utcnow()
        logger.info(f"🔄 Background agent processing started: {session_id}")
        
        # Process through agent system
        result = await agent_system.process_complete_request(
            user_input=user_input,
            budget=budget,
            session_id=session_id
        )
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        result["processing_time"] = processing_time
        
        # Store result
        processing_results[session_id] = {
            "status": "completed",
            "result": result,
            "completed_at": datetime.utcnow()
        }
        
        # Update chat session
        if session_id in chat_sessions:
            chat_sessions[session_id]["agent_processing"] = "completed"
            chat_sessions[session_id]["agent_result"] = result
        
        # Notify via WebSocket if connected
        if session_id in active_websockets:
            try:
                await active_websockets[session_id].send_text(json.dumps({
                    "type": "processing_completed",
                    "data": result,
                    "processing_time": processing_time
                }))
            except Exception as ws_error:
                logger.warning(f"WebSocket notification failed: {ws_error}")
        
        logger.info(f"✅ Background processing completed: {session_id} ({processing_time:.2f}s)")
        
    except Exception as e:
        logger.error(f"❌ Background processing failed: {session_id} - {e}")
        
        # Store error result
        processing_results[session_id] = {
            "status": "error",
            "error": str(e),
            "completed_at": datetime.utcnow()
        }
        
        # Notify error via WebSocket
        if session_id in active_websockets:
            try:
                await active_websockets[session_id].send_text(json.dumps({
                    "type": "processing_error",
                    "error": str(e)
                }))
            except:
                pass

@app.get("/api/agents/result/{session_id}")
async def get_agent_result(session_id: str):
    """Get agent processing result"""
    try:
        # Check processing results
        if session_id in processing_results:
            result_data = processing_results[session_id]
            return {
                "session_id": session_id,
                "status": result_data["status"],
                "result": result_data.get("result"),
                "error": result_data.get("error"),
                "completed_at": result_data["completed_at"]
            }
        
        # Check chat session for inline results
        session = chat_sessions.get(session_id)
        if session and "agent_result" in session:
            return {
                "session_id": session_id,
                "status": "completed",
                "result": session["agent_result"]
            }
        
        # Still processing or not found
        if session:
            return {
                "session_id": session_id,
                "status": "processing",
                "message": "AI Agents are still processing your request..."
            }
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get agent result: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve result")

# =================== WEBSOCKET ENDPOINT ===================

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_websockets[session_id] = websocket
    
    logger.info(f"🔌 WebSocket connected: {session_id}")
    
    try:
        while True:
            # Keep connection alive with ping/pong
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }))
            elif message.get("type") == "status_request":
                # Send current status
                status = "processing"
                if session_id in processing_results:
                    status = processing_results[session_id]["status"]
                
                await websocket.send_text(json.dumps({
                    "type": "status_update",
                    "status": status
                }))
                
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
    finally:
        if session_id in active_websockets:
            del active_websockets[session_id]

# =================== UTILITY ENDPOINTS ===================

@app.get("/api/media/search")
async def search_media_outlets(query: str, limit: int = 10):
    """Search media outlets using vector similarity"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        results = await media_db.search_media_by_vector(query, limit)
        
        return {
            "query": query,
            "results": results,
            "count": len(results.get("documents", [[]])[0]) if results else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Media search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@app.get("/api/media/list")
async def list_all_media_outlets():
    """Get all available media outlets"""
    try:
        media_outlets = await media_db.get_all_media_outlets()
        
        return {
            "media_outlets": [outlet.model_dump() for outlet in media_outlets],
            "count": len(media_outlets),
            "last_updated": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to list media outlets: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve media outlets")

@app.post("/api/demo/quick-test")
async def quick_demo_test():
    """Quick demo endpoint for testing the complete system"""
    try:
        if not agent_system:
            raise HTTPException(status_code=503, detail="Agent system not available")
        
        demo_input = """
        Công ty VietTech Solutions vừa hoàn thành phát triển nền tảng VietPay - 
        giải pháp thanh toán di động thế hệ mới dành riêng cho các doanh nghiệp SME tại Việt Nam.
        
        VietPay giúp các SME:
        - Nhận thanh toán từ khách hàng nhanh chóng và bảo mật
        - Quản lý dòng tiền hiệu quả 
        - Tích hợp với các hệ thống kế toán phổ biến
        
        Mục tiêu: Tăng nhận diện thương hiệu, thu hút đối tác và khách hàng SME.
        Target: Chủ doanh nghiệp nhỏ, quản lý tài chính, cộng đồng fintech.
        """
        
        result = await agent_system.process_complete_request(
            user_input=demo_input,
            budget=25000000,  # 25M VND
            session_id=f"demo_{uuid.uuid4().hex[:8]}"
        )
        
        return {
            "demo_input": demo_input,
            "budget": 25000000,
            "result": result,
            "message": "Demo completed successfully!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Demo test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")

# =================== ADMIN ENDPOINTS ===================

@app.get("/api/admin/stats")
async def get_system_stats():
    """Get system statistics (admin only)"""
    try:
        return {
            "active_sessions": len(chat_sessions),
            "processing_results": len(processing_results),
            "active_websockets": len(active_websockets),
            "system_uptime": datetime.utcnow(),
            "agent_system_status": "active" if agent_system else "inactive"
        }
    except Exception as e:
        logger.error(f"❌ Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve stats")

# =================== UTILITY FUNCTIONS ===================

def _format_chat_data_to_text(chat_data: Dict[str, Any]) -> str:
    """Convert chatbot answers to formatted text for AI agents"""
    
    formatted_input = "THÔNG TIN DỰ ÁN:\n\n"
    
    # Map question IDs to meaningful labels
    question_mapping = {
        "1": "Tình trạng bài PR",
        "2": "Tài liệu bổ sung",
        "3": "Ngôn ngữ sử dụng",
        "4": "Mô tả chi tiết dự án",
        "5": "Tài liệu đính kèm",
        "6": "Kênh truyền thông mong muốn",
        "7": "Ngân sách dự kiến"
    }
    
    for q_id, answer in chat_data.items():
        if q_id in question_mapping:
            label = question_mapping[q_id]
            
            # Format different answer types
            if isinstance(answer, list):
                answer_text = ", ".join(answer)
            else:
                answer_text = str(answer)
            
            formatted_input += f"{label}: {answer_text}\n"
    
    formatted_input += f"\nThời gian yêu cầu: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
    
    return formatted_input

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
        "logs/instant_media_release.log",
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
    
    logger.info("🚀 Starting Instant Media Release API Server...")
    logger.info(f"📱 Demo interface: http://{settings.host}:{settings.port}")
    logger.info(f"📚 API documentation: http://{settings.host}:{settings.port}/docs")
    logger.info(f"🔍 Health check: http://{settings.host}:{settings.port}/health")
    
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