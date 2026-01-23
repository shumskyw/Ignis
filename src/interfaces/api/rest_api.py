"""
REST API for Ignis AI using FastAPI.
Provides programmatic access to Ignis.
"""

import asyncio
import os
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ...utils.logger import get_logger

logger = get_logger(__name__)


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="User message")
    mode: str = Field("default", description="Response mode")
    stream: bool = Field(False, description="Enable streaming response")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="AI response")
    mode: str = Field(..., description="Response mode used")
    processing_time: float = Field(..., description="Processing time in seconds")


class StatusResponse(BaseModel):
    """Status response model."""
    status: str = Field(..., description="API status")
    version: str = Field(..., description="API version")
    system_status: Dict[str, Any] = Field(..., description="System component status")


class MemorySearchRequest(BaseModel):
    """Memory search request model."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Maximum results")
    user_id: Optional[str] = Field(None, description="User ID filter")
    include_metadata: bool = Field(True, description="Include metadata in results")


class MemoryAddRequest(BaseModel):
    """Memory add request model."""
    content: str = Field(..., min_length=1, max_length=5000, description="Content to store")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    user_id: Optional[str] = Field(None, description="User ID")


class MemoryResponse(BaseModel):
    """Memory response model."""
    memories: List[Dict[str, Any]] = Field(..., description="Memory results")
    count: int = Field(..., description="Total count")
    query: Optional[str] = Field(None, description="Search query used")
    processing_time: float = Field(..., description="Processing time")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    timestamp: str = Field(..., description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class APIApp:
    """
    FastAPI application for Ignis AI.
    """

    def __init__(self, ignis_ai):
        """
        Initialize API app.

        Args:
            ignis_ai: IgnisAI instance
        """
        self.ignis = ignis_ai
        self.app = FastAPI(
            title="Ignis AI API",
            description="REST API for Ignis AI - Offline AI with Memory",
            version="1.0.0"
        )

        self._setup_middleware()
        self._setup_routes()

        logger.info("API app initialized")

    def _setup_middleware(self):
        """Setup FastAPI middleware."""
        # CORS middleware for web access
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, restrict this
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """Setup API routes."""

        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {"message": "Ignis AI API", "status": "running"}

        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            return {"status": "healthy"}

        @self.app.get("/status", response_model=StatusResponse)
        async def get_status():
            """Get system status."""
            try:
                system_status = self.ignis.get_status()
                return StatusResponse(
                    status="operational",
                    version="1.0.0",
                    system_status=system_status
                )
            except Exception as e:
                logger.error(f"Status endpoint error: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get system status: {str(e)}"
                )

        @self.app.post("/chat", response_model=ChatResponse)
        async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
            """Chat endpoint with comprehensive error handling."""
            import time
            start_time = time.time()

            try:
                # Validate request
                if not request.message.strip():
                    raise HTTPException(
                        status_code=400,
                        detail="Message cannot be empty"
                    )

                # Process chat
                response = await self.ignis.chat(
                    request.message,
                    mode=request.mode
                )

                processing_time = time.time() - start_time

                logger.info(f"Chat processed in {processing_time:.2f}s")

                return ChatResponse(
                    response=response,
                    mode=request.mode,
                    processing_time=processing_time
                )

            except HTTPException:
                raise
            except Exception as e:
                processing_time = time.time() - start_time
                logger.error(f"Chat processing error after {processing_time:.2f}s: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to process chat: {str(e)}"
                )

        @self.app.post("/chat/stream")
        async def chat_stream(request: ChatRequest):
            """Streaming chat endpoint."""
            if not request.stream:
                # Redirect to regular chat
                response = await chat(request, BackgroundTasks())
                return {"response": response.response}

            # Streaming response
            async def generate():
                try:
                    async for chunk in self.ignis.chat_stream(
                        request.message,
                        mode=request.mode
                    ):
                        yield f"data: {chunk}\n\n"
                except Exception as e:
                    logger.error(f"Streaming chat error: {e}")
                    yield f"data: Error: {str(e)}\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache"}
            )

        @self.app.post("/memory/search", response_model=MemoryResponse)
        async def search_memory(request: MemorySearchRequest):
            """Search memory with advanced options."""
            import time
            start_time = time.time()

            try:
                memories = await self.ignis.memory.retrieve(
                    request.query,
                    user_id=request.user_id,
                    limit=request.limit
                )

                processing_time = time.time() - start_time
                memory_status = self.ignis.memory.get_status()

                logger.info(f"Memory search '{request.query}' returned {len(memories)} results in {processing_time:.2f}s")

                return MemoryResponse(
                    memories=memories,
                    count=memory_status.get('atomic_facts_stored', 0),
                    query=request.query,
                    processing_time=processing_time
                )

            except Exception as e:
                processing_time = time.time() - start_time
                logger.error(f"Memory search error after {processing_time:.2f}s: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to search memory: {str(e)}"
                )

        @self.app.post("/memory/add")
        async def add_memory(request: MemoryAddRequest):
            """Add information to memory."""
            try:
                if not request.content.strip():
                    raise HTTPException(
                        status_code=400,
                        detail="Content cannot be empty"
                    )

                fact_id = await self.ignis.memory.store_fact(
                    request.content,
                    request.metadata or {},
                    user_id=request.user_id
                )

                logger.info(f"Added memory: '{request.content[:50]}...' (ID: {fact_id})")

                return {
                    "status": "success",
                    "fact_id": fact_id,
                    "message": "Information added to memory"
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Memory add error: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to add to memory: {str(e)}"
                )

        @self.app.get("/memory/stats")
        async def get_memory_stats():
            """Get memory statistics."""
            try:
                stats = self.ignis.memory.get_status()
                return {
                    "total_memories": stats.get('atomic_facts_stored', 0),
                    "conversations_stored": stats.get('conversations_stored', 0),
                    "vector_db_available": stats.get('vector_db_available', False),
                    "short_term_memories": len(getattr(self.ignis.memory, 'short_term_memory', [])),
                    "goals_active": len(getattr(self.ignis.memory, 'goals_manager', {}).get('long_term_goals', [])) if hasattr(self.ignis.memory, 'goals_manager') else 0
                }
            except Exception as e:
                logger.error(f"Memory stats error: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get memory stats: {str(e)}"
                )

        @self.app.post("/persona")
        async def switch_persona(request: PersonaRequest):
            """Switch persona with validation."""
            try:
                if not request.persona.strip():
                    raise HTTPException(
                        status_code=400,
                        detail="Persona name cannot be empty"
                    )

                success = self.ignis.switch_persona(request.persona)
                if success:
                    logger.info(f"Switched to persona: {request.persona}")
                    return {"status": "success", "persona": request.persona}
                else:
                    logger.warning(f"Failed to switch to unknown persona: {request.persona}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unknown persona: {request.persona}"
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Persona switch error: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to switch persona: {str(e)}"
                )

        @self.app.get("/personas")
        async def get_personas():
            """Get available personas."""
            status = self.ignis.get_status()
            personas = status.get('personality', {}).get('available_personas', [])
            current = status.get('personality', {}).get('current_persona', 'default')
            return {
                "personas": personas,
                "current": current
            }

        @self.app.get("/modes")
        async def get_modes():
            """Get available modes."""
            modes = ["default", "coding", "creative", "analytical", "roleplay", "assistant"]
            return {"modes": modes}

        @self.app.post("/shutdown")
        async def shutdown(background_tasks: BackgroundTasks):
            """Shutdown the system."""
            background_tasks.add_task(self._shutdown_system)
            return {"status": "shutting_down"}

    async def _shutdown_system(self):
        """Shutdown the system gracefully."""
        logger.info("API shutdown requested")
        await self.ignis.shutdown()

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the API server."""
        logger.info(f"Starting API server on {host}:{port}")

        try:
            uvicorn.run(
                self.app,
                host=host,
                port=port,
                log_level="info"
            )
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            print(f"Error starting API server: {e}")


# Import here to avoid circular imports
try:
    from fastapi.responses import StreamingResponse
except ImportError:
    StreamingResponse = None


async def run_api(ignis_ai):
    """
    Run the API server.

    Args:
        ignis_ai: IgnisAI instance
    """
    api_app = APIApp(ignis_ai)
    port = int(os.getenv('IGNIS_API_PORT', '8000'))
    api_app.run(port=port)