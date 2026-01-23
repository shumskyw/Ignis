"""
Web UI for Ignis AI using Gradio.
Provides browser-based chat interface.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import List, Optional, Tuple

from ...utils.logger import get_logger

logger = get_logger(__name__)


class WebUI:
    """
    Web-based user interface for Ignis AI using Gradio.
    """

    def __init__(self, ignis_ai):
        """
        Initialize web UI.

        Args:
            ignis_ai: IgnisAI instance
        """
        self.ignis = ignis_ai
        self.gradio_available = self._check_gradio_availability()
        self.interface = None
        self.current_mode = "default"
        self.chat_history = []

        if not self.gradio_available:
            logger.error("Gradio not available. Install with: pip install gradio")
            return

        import gradio as gr

        self.gr = gr
        self._create_interface()

    def _check_gradio_availability(self) -> bool:
        """Check if Gradio is available."""
        try:
            import gradio
            return True
        except ImportError:
            return False

    def _create_interface(self):
        """Create the Gradio interface."""
        with self.gr.Blocks(
            title="Ignis AI",
            theme=self.gr.themes.Soft(),
            css=self._get_css()
        ) as self.interface:

            # Title
            self.gr.Markdown("# 🔥 Ignis AI")
            self.gr.Markdown("*Your offline AI companion with memory and personality*")

            # Status indicator
            status = self.gr.Textbox(
                label="System Status",
                value=self._get_status_text(),
                interactive=False
            )

            # Mode selector
            mode_selector = self.gr.Dropdown(
                choices=["default", "coding", "creative", "analytical", "roleplay", "assistant"],
                value="default",
                label="Response Mode",
                info="Choose how Ignis responds"
            )

            # Persona selector
            persona_selector = self.gr.Dropdown(
                choices=self._get_persona_choices(),
                value="default",
                label="Persona",
                info="Choose Ignis's personality"
            )

            # Chatbot
            chatbot = self.gr.Chatbot(
                height=400,
                show_label=False,
                container=True
            )

            # Message input
            msg = self.gr.Textbox(
                label="Your Message",
                placeholder="Type your message here...",
                lines=3
            )

            # Buttons
            with self.gr.Row():
                submit_btn = self.gr.Button("Send", variant="primary")
                clear_btn = self.gr.Button("Clear Chat")
                refresh_btn = self.gr.Button("Refresh Status")

            # Event handlers
            mode_selector.change(
                fn=self._change_mode,
                inputs=[mode_selector],
                outputs=[]
            )

            persona_selector.change(
                fn=self._change_persona,
                inputs=[persona_selector],
                outputs=[]
            )

            submit_btn.click(
                fn=self._chat_response,
                inputs=[msg, chatbot, mode_selector],
                outputs=[msg, chatbot]
            )

            msg.submit(
                fn=self._chat_response,
                inputs=[msg, chatbot, mode_selector],
                outputs=[msg, chatbot]
            )

            clear_btn.click(
                fn=self._clear_chat,
                inputs=[],
                outputs=[chatbot]
            )

            refresh_btn.click(
                fn=self._refresh_status,
                inputs=[],
                outputs=[status]
            )

    def _get_css(self) -> str:
        """Get custom CSS for the interface."""
        return """
        .gradio-container {
            max-width: 900px !important;
        }
        .chatbot {
            border-radius: 10px;
        }
        """

    def _get_status_text(self) -> str:
        """Get status text for display."""
        status = self.ignis.get_status()
        status_lines = []

        if status.get('inference', {}).get('model_loaded'):
            status_lines.append("✓ Model loaded")
        else:
            status_lines.append("✗ No model loaded")

        if status.get('memory', {}).get('vector_db_available'):
            status_lines.append("✓ Memory system active")
        else:
            status_lines.append("⚠ Memory using fallback storage")

        persona = status.get('personality', {}).get('current_persona', 'unknown')
        status_lines.append(f"Current persona: {persona}")

        return " | ".join(status_lines)

    def _get_persona_choices(self) -> List[str]:
        """Get available persona choices."""
        status = self.ignis.get_status()
        personas = status.get('personality', {}).get('available_personas', [])
        return personas if personas else ['default']

    def _change_mode(self, mode: str):
        """Change response mode."""
        self.current_mode = mode
        logger.info(f"Web UI mode changed to: {mode}")

    def _change_persona(self, persona: str):
        """Change persona."""
        if self.ignis.switch_persona(persona):
            logger.info(f"Web UI persona changed to: {persona}")
        else:
            logger.warning(f"Failed to change persona to: {persona}")

    async def _chat_response(self, message: str, history: List[List[str]], mode: str) -> Tuple[str, List[List[str]]]:
        """Handle chat response."""
        if not message.strip():
            return "", history

        try:
            # Get AI response
            response = await self.ignis.chat(message, mode=mode)

            # Add to history
            history = history + [[message, response]]

            return "", history

        except Exception as e:
            error_msg = f"I encountered an error: {str(e)}"
            history = history + [[message, error_msg]]
            return "", history

    def _clear_chat(self) -> List[List[str]]:
        """Clear chat history."""
        self.chat_history = []
        return []

    def _refresh_status(self) -> str:
        """Refresh status display."""
        return self._get_status_text()

    def launch(self, **kwargs):
        """Launch the web interface."""
        if not self.interface:
            logger.error("Web interface not initialized")
            return

        # Default kwargs
        launch_kwargs = {
            'server_name': '0.0.0.0',
            'server_port': int(os.getenv('IGNIS_WEB_PORT', '7860')),
            'share': False,  # No public sharing for privacy
            'show_error': True,
            'favicon_path': None
        }
        launch_kwargs.update(kwargs)

        logger.info(f"Launching web UI on port {launch_kwargs['server_port']}")

        try:
            self.interface.launch(**launch_kwargs)
        except Exception as e:
            logger.error(f"Failed to launch web UI: {e}")
            print(f"Error launching web UI: {e}")


async def run_web(ignis_ai):
    """
    Run the web interface.

    Args:
        ignis_ai: IgnisAI instance
    """
    ui = WebUI(ignis_ai)
    ui.launch()