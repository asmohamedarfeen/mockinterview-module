"""
Qrow IQ - FastAPI Application Entry Point
AI HR Mock Interview Platform
"""
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse

from app.core.config import settings
from app.websocket.manager import manager
from app.websocket.handlers import handle_websocket_message
from app.report.pdf_generator import pdf_generator
from app.report.dashboard_data import dashboard_data_preparer

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI HR Mock Interview Platform - Voice-only interview system with Gemini 2.0 Flash"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "websocket_endpoint": "/ws/interview/{session_id}"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "active_sessions": len(manager.active_connections),
        "total_sessions": len(manager.sessions)
    }


@app.get("/api/reports/{session_id}/pdf")
async def get_pdf_report(session_id: str):
    """
    Generate and download PDF report for interview session
    
    Args:
        session_id: Interview session ID
        
    Returns:
        PDF file as download
    """
    try:
        session = manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Generate PDF
        pdf_buffer = pdf_generator.generate_pdf(session)
        
        # Return as downloadable file
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=qrow-iq-report-{session_id}.pdf"
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to generate PDF for {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")


@app.get("/api/reports/{session_id}/dashboard")
async def get_dashboard_data(session_id: str):
    """
    Get dashboard data for interview session
    
    Args:
        session_id: Interview session ID
        
    Returns:
        JSON data for dashboard visualization
    """
    try:
        session = manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Prepare dashboard data
        dashboard_data = dashboard_data_preparer.prepare_dashboard_data(session)
        
        return JSONResponse(content=dashboard_data)
    
    except Exception as e:
        logger.error(f"Failed to prepare dashboard data for {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to prepare dashboard data: {str(e)}")


@app.websocket("/ws/interview/{session_id}")
async def websocket_interview_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for interview sessions
    
    Connection URL: ws://localhost:8000/ws/interview/{session_id}
    
    Message Protocol:
    - Client sends: {"type": "START_INTERVIEW", "job_role": "...", ...}
    - Server responds: {"type": "QUESTION_READY", "question": "...", ...}
    """
    # Accept connection
    connected = await manager.connect(websocket, session_id)
    if not connected:
        await websocket.close(code=1008, reason="Connection failed")
        return
    
    logger.info(f"WebSocket connection established: {session_id}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse JSON message
                message = json.loads(data)
                logger.debug(f"Received message from {session_id}: {message.get('type')}")
                
                # Route message to appropriate handler
                await handle_websocket_message(websocket, session_id, message)
            
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from {session_id}: {e}")
                await manager.send_personal_message({
                    "type": "ERROR",
                    "session_id": session_id,
                    "error_code": "INVALID_JSON",
                    "error_message": "Invalid JSON format"
                }, session_id)
            
            except Exception as e:
                logger.error(f"Error processing message from {session_id}: {e}", exc_info=True)
                await manager.send_personal_message({
                    "type": "ERROR",
                    "session_id": session_id,
                    "error_code": "PROCESSING_ERROR",
                    "error_message": str(e)
                }, session_id)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
        manager.disconnect(session_id)
    
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}", exc_info=True)
        manager.disconnect(session_id)


@app.on_event("startup")
async def startup_event():
    """
    Application startup event
    """
    logger.info(f"{settings.app_name} v{settings.app_version} starting up...")
    logger.info(f"Backend running on port {settings.backend_port}")
    logger.info(f"Frontend URL: {settings.frontend_url}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event - cleanup
    """
    logger.info(f"{settings.app_name} shutting down...")
    # Close all WebSocket connections
    for session_id in list(manager.active_connections.keys()):
        manager.disconnect(session_id)
