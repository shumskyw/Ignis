"""
Custom Web UI for Ignis AI - iMessage-style interface.
Serves static HTML/CSS/JS files and integrates with Ignis API.
"""

import asyncio
import os
import time
import webbrowser
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from ...utils.logger import get_logger

logger = get_logger(__name__)


class CustomWebUI:
    """
    Custom web UI for Ignis AI with iMessage-style interface.
    """

    def __init__(self, ignis_ai, port: int = 7860):
        """
        Initialize custom web UI.

        Args:
            ignis_ai: IgnisAI instance
            port: Port to run the server on
        """
        self.ignis = ignis_ai
        self.port = port
        self.app = FastAPI(title="Ignis AI Chat", description="iMessage-style chat interface for Ignis AI")

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self._setup_routes()
        self._mount_static_files()

        logger.info("Custom web UI initialized")

    def _setup_routes(self):
        """Setup API routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def get_chat_interface():
            """Serve the main chat interface."""
            try:
                logger.info("Serving chat interface")
                html_path = Path(__file__).parent.parent.parent.parent / "web" / "html" / "chat.html"
                logger.info(f"HTML path: {html_path}")
                if html_path.exists():
                    logger.info("HTML file exists, reading...")
                    with open(html_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    logger.info(f"HTML content length: {len(content)}")
                    return content
                else:
                    logger.error("HTML file not found")
                    return "<h1>Ignis AI Chat</h1><p>Chat interface not found.</p>"
            except Exception as e:
                logger.error(f"Error serving chat interface: {e}")
                return f"<h1>Error</h1><p>{str(e)}</p>"

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "interface": "custom_web"}

        # @self.app.get("/api/status")
        # async def get_status():
        #     """Get system status."""
        #     try:
        #         # Simplified status for now
        #         return {
        #             "status": "operational",
        #             "version": "1.0.0",
        #             "interface": "custom_web"
        #         }
        #     except Exception as e:
        #         logger.error(f"Status error: {e}")
        #         raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/chat")
        async def chat(request: Request):
            """Chat endpoint."""
            try:
                data = await request.json()
                message = data.get('message', '')
                mode = data.get('mode', 'default')
                user_name = data.get('user_name', 'User')

                if not message:
                    raise HTTPException(status_code=400, detail="Message is required")

                import time
                start_time = time.time()

                # Process chat
                response = await self.ignis.chat(message, mode=mode, user_name=user_name)

                processing_time = time.time() - start_time

                return {
                    "response": response,
                    "mode": mode,
                    "processing_time": processing_time
                }

            except Exception as e:
                logger.error(f"Chat API error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/memory/status")
        async def get_memory_status():
            """Get memory status for the web interface."""
            try:
                # Use the existing memory status command
                status = self.ignis._handle_memory_status_command()
                return {"status": status}
            except Exception as e:
                logger.error(f"Memory status error: {e}")
                return {"status": "Unable to load memory status"}

        @self.app.get("/api/memory/status/indicator")
        async def get_memory_status_indicator():
            """Get simplified memory status for indicator dot."""
            try:
                stats = self.ignis.memory._get_memory_stats()
                learning_active = self.ignis.memory.conversation_saving_enabled

                # Determine status
                if learning_active and stats['atomic_facts'] > 0:
                    status = "remembering"  # Green
                elif not learning_active and stats['atomic_facts'] > 0:
                    status = "not-remembering"  # Yellow
                else:
                    status = "private"  # Red

                return {"status": status}
            except Exception as e:
                logger.error(f"Memory status indicator error: {e}")
                return {"status": "private"}  # Default to red on error

        @self.app.post("/api/user/name")
        async def update_user_name(request: Request):
            """Update the user's name in the web interface."""
            try:
                data = await request.json()
                new_name = data.get('name', '').strip()

                if not new_name:
                    raise HTTPException(status_code=400, detail="Name is required")

                # For now, we'll just validate the name
                # In a real implementation, this could store it in a database or file
                return {"success": True, "name": new_name}
            except Exception as e:
                logger.error(f"Update user name error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def _mount_static_files(self):
        """Mount static file directories."""
        web_root = Path(__file__).parent.parent.parent.parent / "web"

        # Mount CSS files
        css_path = web_root / "css"
        if css_path.exists():
            self.app.mount("/css", StaticFiles(directory=str(css_path)), name="css")

        # Mount JS files
        js_path = web_root / "script"
        if js_path.exists():
            self.app.mount("/script", StaticFiles(directory=str(js_path)), name="script")

        # Mount HTML files (fallback)
        html_path = web_root / "html"
        if html_path.exists():
            self.app.mount("/html", StaticFiles(directory=str(html_path)), name="html")

    def run(self):
        """Run the web server."""
        logger.info(f"Starting custom web UI on port {self.port}")
        url = f"http://localhost:{self.port}"
        logger.info(f"Opening {url} in your default browser")

        try:
            # Start server in a separate thread so we can open browser immediately
            import threading
            
            def start_server():
                uvicorn.run(
                    self.app,
                    host="0.0.0.0",
                    port=self.port,
                    log_level="info"
                )
            
            server_thread = threading.Thread(target=start_server, daemon=True)
            server_thread.start()
            
            # Give server a moment to start
            time.sleep(1)
            
            # Open browser
            webbrowser.open(url)
            
            logger.info("Browser opened successfully. Server is running in background.")
            logger.info("Press Ctrl+C to stop the server.")
            
            # Keep the main thread alive
            server_thread.join()
            
        except Exception as e:
            logger.error(f"Failed to start web UI: {e}")
            print(f"Error starting web UI: {e}")


def run_web(ignis_ai, port: int = 7860):
    """
    Run the custom web interface.

    Args:
        ignis_ai: IgnisAI instance
        port: Port to run on
    """
    ui = CustomWebUI(ignis_ai, port)
    ui.run()