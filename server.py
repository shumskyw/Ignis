#!/usr/bin/env python3
"""
Ignis AI Web Server
Serves the chat interface from the web folder and provides API endpoints.
"""

import asyncio
import json
import os
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
import time
from datetime import datetime

# Set working directory to script location
os.chdir(Path(__file__).parent)

# Add src to path
sys.path.insert(0, "src")

from src.core.ignis import IgnisAI
from src.utils.logger import get_logger


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    user_name: str = Field("User", min_length=1, max_length=50, description="User name")
    mode: str = Field("default", description="Response mode")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI response")
    user_name: str = Field(..., description="User name")
    timestamp: str = Field(..., description="Response timestamp")
    memory_count: int = Field(..., description="Current memory count")
    processing_time: float = Field(..., description="Processing time in seconds")
    mode: str = Field("default", description="Response mode used")

class StatusResponse(BaseModel):
    status: str = Field(..., description="Server status")
    memory_count: int = Field(..., description="Number of stored memories")
    conversations_stored: int = Field(..., description="Number of stored conversations")
    user_name: str = Field(..., description="Current user name")
    timestamp: str = Field(..., description="Status timestamp")
    system_info: Dict[str, Any] = Field(..., description="System information")

class MemoryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Memory search query")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")
    user_id: Optional[str] = Field(None, description="User ID filter")

class MemoryResponse(BaseModel):
    memories: List[Dict[str, Any]] = Field(..., description="Retrieved memories")
    count: int = Field(..., description="Total memory count")
    query: str = Field(..., description="Search query used")
    processing_time: float = Field(..., description="Processing time in seconds")

app = FastAPI(title="Ignis AI Web Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global AI instance (initialized in main)
ai = None

# Mount static files from web folder
app.mount("/css", StaticFiles(directory="web/css"), name="css")
app.mount("/script", StaticFiles(directory="web/script"), name="script")

@app.get("/")
async def root():
    """Serve the main chat interface from web folder"""
    return FileResponse("web/html/chat.html", media_type="text/html")

@app.get("/status", response_model=StatusResponse)
async def status():
    """Get server status"""
    try:
        memory_status = ai.memory.get_status()
        system_info = {
            "memory_system": "operational" if memory_status.get('vector_db_available', False) else "degraded",
            "inference_engine": "operational",  # Assume operational if server is running
            "personality_engine": "operational",
            "plugins_loaded": len(ai.plugins.plugins) if hasattr(ai, 'plugins') and hasattr(ai.plugins, 'plugins') else 0
        }

        return StatusResponse(
            status="healthy",
            memory_count=memory_status.get('atomic_facts_stored', 0),
            conversations_stored=memory_status.get('conversations_stored', 0),
            user_name="Jin",  # Default user
            timestamp=datetime.now().isoformat(),
            system_info=system_info
        )
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Status endpoint error: {e}", exc_info=True)

        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "memory_count": 0,
                "conversations_stored": 0,
                "user_name": "Unknown",
                "timestamp": datetime.now().isoformat(),
                "system_info": {"error": str(e)},
                "error": "System status unavailable"
            }
        )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat messages"""
    start_time = time.time()
    logger = get_logger(__name__)

    logger.info(f"Chat request from {request.user_name}: '{request.message[:50]}{'...' if len(request.message) > 50 else ''}'")

    try:
        # Validate request
        if not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )

        # Process chat
        response = await ai.chat(request.message, user_name=request.user_name)

        logger.info(f"AI response: '{response[:100] if response else 'None'}{'...' if response and len(response) > 100 else ''}'")

        elapsed_time = time.time() - start_time
        memory_status = ai.memory.get_status()

        logger.info(".2f")

        return ChatResponse(
            response=response,
            user_name=request.user_name,
            timestamp=datetime.now().isoformat(),
            memory_count=memory_status.get('atomic_facts_stored', 0),
            processing_time=round(elapsed_time, 2),
            mode=request.mode
        )

    except HTTPException:
        raise
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Chat processing error: {e}", exc_info=True)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}"
        )

@app.get("/memory", response_model=MemoryResponse)
async def get_memory(query: str = "", limit: int = 10):
    """Get memory contents with optional search"""
    start_time = time.time()
    logger = get_logger(__name__)

    try:
        if query.strip():
            # Search memories
            memories = await ai.memory.retrieve(query, limit=limit)
            logger.info(f"Memory search: '{query}' returned {len(memories)} results")
        else:
            # Get recent memories (simplified)
            memories = []  # Could implement recent memory retrieval

        memory_status = ai.memory.get_status()
        elapsed_time = time.time() - start_time

        return MemoryResponse(
            memories=memories,
            count=memory_status.get('atomic_facts_stored', 0),
            query=query,
            processing_time=round(elapsed_time, 2)
        )

    except Exception as e:
        logger.error(f"Memory retrieval error: {e}", exc_info=True)
        elapsed_time = time.time() - start_time

        return JSONResponse(
            status_code=500,
            content={
                "memories": [],
                "count": 0,
                "query": query,
                "processing_time": round(elapsed_time, 2),
                "error": str(e)
            }
        )

@app.post("/memory/search", response_model=MemoryResponse)
async def search_memory(request: MemoryRequest):
    """Advanced memory search"""
    start_time = time.time()
    logger = get_logger(__name__)

    try:
        memories = await ai.memory.retrieve(
            request.query,
            user_id=request.user_id,
            limit=request.limit
        )

        memory_status = ai.memory.get_status()
        elapsed_time = time.time() - start_time

        logger.info(f"Advanced memory search: '{request.query}' returned {len(memories)} results")

        return MemoryResponse(
            memories=memories,
            count=memory_status.get('atomic_facts_stored', 0),
            query=request.query,
            processing_time=round(elapsed_time, 2)
        )

    except Exception as e:
        logger.error(f"Memory search error: {e}", exc_info=True)
        elapsed_time = time.time() - start_time

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search memory: {str(e)}"
        )

@app.post("/memory/add")
async def add_memory(content: str, metadata: Optional[Dict[str, Any]] = None):
    """Add information to memory"""
    logger = get_logger(__name__)

    try:
        if not content.strip():
            raise HTTPException(
                status_code=400,
                detail="Content cannot be empty"
            )

        # Store in memory
        fact_id = await ai.memory.store_fact(content, metadata or {})
        logger.info(f"Added to memory: '{content[:50]}...' (ID: {fact_id})")

        return {
            "status": "success",
            "fact_id": fact_id,
            "message": "Information added to memory"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory storage error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add to memory: {str(e)}"
        )

@app.get("/settings")
async def get_settings():
    """Get current settings"""
    try:
        from src.core.config import get_config
        config = get_config()
        return {
            "generation": config.generation.dict(),
            "memory": config.memory.dict(),
            "personality": config.personality.dict(),
            "user": config.user.dict()
        }
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get settings: {str(e)}"
        )

@app.post("/settings")
async def update_settings(settings: Dict[str, Any]):
    """Update user settings"""
    try:
        from src.core.config import get_config, reload_config
        config = get_config()
        
        # Update config with new settings
        if "generation" in settings:
            for key, value in settings["generation"].items():
                if hasattr(config.generation, key):
                    setattr(config.generation, key, value)
        
        if "memory" in settings:
            for key, value in settings["memory"].items():
                if hasattr(config.memory, key):
                    setattr(config.memory, key, value)
        
        # Save to files
        config.save_to_files()
        
        # Reload config to apply changes
        reload_config()
        
        return {"status": "settings_updated"}
    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update settings: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        memory_status = ai.memory.get_status()
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "memory_system": "healthy" if memory_status.get('vector_db_available', False) else "degraded",
                "inference_engine": "healthy",  # Assume healthy if server is running
                "personality_engine": "healthy",
                "api_server": "healthy"
            },
            "metrics": {
                "memory_count": memory_status.get('atomic_facts_stored', 0),
                "conversations_stored": memory_status.get('conversations_stored', 0),
                "uptime_seconds": time.time() - getattr(ai, '_start_time', time.time())
            }
        }

        # Check if any component is unhealthy
        if any(status != "healthy" for status in health_status["components"].values()):
            health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Health check error: {e}", exc_info=True)

        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "components": {"all": "unknown"}
            }
        )

@app.get("/system/info")
async def system_info():
    """Get system information"""
    try:
        import platform
        import psutil

        memory_status = ai.memory.get_status()

        return {
            "system": {
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available
            },
            "ignis": {
                "version": "1.0.0",
                "memory_system": "modular" if hasattr(ai.memory, 'storage') else "legacy",
                "inference_backend": "llama.cpp",
                "personas_available": len(ai.personality.personas) if hasattr(ai, 'personality') else 0,
                "plugins_loaded": len(ai.plugins) if hasattr(ai, 'plugins') else 0
            },
            "memory_stats": memory_status
        }

    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"System info error: {e}", exc_info=True)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to get system information: {str(e)}"
        )
if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    import uvicorn
    
    parser = argparse.ArgumentParser(description='Ignis AI Web Server')
    parser.add_argument('--no-browser', action='store_true', help='Skip automatic browser opening')
    args = parser.parse_args()
    
    # Initialize AI here
    ai = IgnisAI("./configs")
    
    print("Starting Ignis AI Web Server...")
    print()
    print("To run without opening browser automatically:")
    print("  python server.py --no-browser")
    print()
    print("API Endpoints:")
    print("  GET  /           - Chat interface")
    print("  POST /chat       - Send chat message")
    print("  GET  /status     - Server status")
    print("  GET  /memory     - View memory contents")
    print("  POST /memory/search - Advanced memory search")
    print("  POST /memory/add - Add information to memory")
    print("  GET  /settings   - Get current settings")
    print("  POST /settings   - Update settings")
    print("Press Ctrl+C to stop the server")
    print()

    # Store start time for uptime tracking
    ai._start_time = time.time()

    logger = get_logger(__name__)
    logger.info("Ignis AI Web Server starting up")
    
    # Open browser automatically (unless disabled)
    if not args.no_browser:
        print("Opening chat interface in your default browser...")
        url = "http://127.0.0.1:8000"
        try:
            import os
            import subprocess
            
            browser_opened = False
            
            # Try Windows start command first (more reliable for visibility)
            if os.name == 'nt':
                try:
                    subprocess.run(['start', url], shell=True, check=True)
                    browser_opened = True
                    print("Browser opened with Windows start command")
                except Exception as e:
                    print(f"Windows start command failed: {e}")
            
            # Fallback to webbrowser.open
            if not browser_opened:
                try:
                    import webbrowser
                    result = webbrowser.open(url)
                    if result:
                        browser_opened = True
                        print("Browser opened with webbrowser.open")
                    else:
                        print("⚠️  Could not open browser automatically.")
                        print(f"Please manually open: {url}")
                except Exception as e:
                    print(f"Error opening browser: {e}")
                    print(f"Please manually open: {url}")
        except Exception as e:
            print(f"Error opening browser: {e}")
            print(f"Please manually open: {url}")
    else:
        print(f"Browser opening disabled. Please manually open: http://127.0.0.1:8000")
    
    # Start server directly in main thread
    print("Starting FastAPI server...")
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()
        raise