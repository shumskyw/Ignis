"""
Terminal UI for Ignis AI.
Provides command-line interface with rich formatting.
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Optional

from ...utils.logger import get_logger

logger = get_logger(__name__)


class TerminalUI:
    """
    Terminal-based user interface for Ignis AI.
    """

    def __init__(self, ignis_ai):
        """
        Initialize terminal UI.

        Args:
            ignis_ai: IgnisAI instance
        """
        self.ignis = ignis_ai
        self.rich_available = self._check_rich_availability()
        self.current_mode = "default"
        self.user_name = "User"  # Default
        self.conversation_history = []  # Store conversation for display

        # Load user config
        self._load_user_config()

        if self.rich_available:
            from rich.console import Console
            from rich.layout import Layout
            from rich.live import Live
            from rich.panel import Panel
            from rich.prompt import Prompt
            from rich.spinner import Spinner
            from rich.text import Text

            self.console = Console()
            self.prompt = Prompt
            self.panel = Panel
            self.text = Text
            self.live = Live
            self.spinner = Spinner
            self.layout = Layout
        else:
            # Fallback without rich
            self.console = None

    def _check_rich_availability(self) -> bool:
        """Check if rich library is available."""
        try:
            import rich
            return True
        except ImportError:
            logger.warning("Rich library not available, using basic terminal interface")
            return False

    def _load_user_config(self):
        """Load user configuration."""
        try:
            import json
            config_path = Path("./configs/user_config.json")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.user_name = config.get('user_name', 'User')
                    logger.info(f"Loaded user name: {self.user_name}")
            else:
                logger.info("User config not found, using defaults")
        except Exception as e:
            logger.error(f"Failed to load user config: {e}")
            self.user_name = "User"

    def print_welcome(self):
        """Print welcome message."""
        welcome_text = """
██╗░██████╗░███╗░░██╗██╗░██████╗
██║██╔════╝░████╗░██║██║██╔════╝
██║██║░░██╗░██╔██╗██║██║╚█████╗░
██║██║░░╚██╗██║╚████║██║░╚═══██╗
██║╚██████╔╝██║░╚███║██║██████╔╝
╚═╝░╚═════╝░╚═╝░░╚══╝╚═╝╚═════╝░

Welcome to Ignis AI - Your Offline AI Companion
Start chatting!
"""

        if self.rich_available:
            try:
                panel = self.panel(welcome_text, title="Ignis AI", border_style="blue")
                self.console.print(panel)
            except UnicodeEncodeError:
                # Fallback to simple print if encoding fails
                print("=================================")
                print("         Ignis AI")
                print("=================================")
                print(welcome_text)
        else:
            print(welcome_text)

    def print_response(self, response: str, mode: str = "default"):
        """Print AI response with formatting."""
        if self.rich_available:
            # Color code based on mode
            colors = {
                "default": "white",
                "coding": "green",
                "creative": "magenta",
                "analytical": "yellow",
                "roleplay": "cyan"
            }
            color = colors.get(mode, "white")

            response_text = self.text(response, style=color)
            self.console.print(f"\nIgnis ({mode}): ", end="")
            self.console.print(response_text)
        else:
            print(f"\nIgnis ({mode}): {response}")

    def get_user_input(self) -> Optional[str]:
        """Get user input with prompt."""
        try:
            if self.rich_available:
                return self.prompt.ask("\n[bold blue]You[/bold blue]")
            else:
                return input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            return None

    def handle_command(self, command: str) -> bool:
        """
        Handle special commands.

        Args:
            command: User command

        Returns:
            True if command was handled, False if it's a regular message
        """
        cmd = command.lower().strip()

        if cmd in ['quit', 'exit', 'q']:
            self.print_goodbye()
            return True

        elif cmd == 'goodbye ignis':
            self.print_goodbye()
            return True

        elif cmd in ['help', 'h', '?']:
            self.print_help()
            return True

        elif cmd.startswith('mode '):
            mode = cmd.split(' ', 1)[1]
            if self.set_mode(mode):
                self.print_message(f"Switched to {mode} mode")
            else:
                self.print_error(f"Unknown mode: {mode}")
            return True

        elif cmd == 'status':
            self.print_status()
            return True

        elif cmd.startswith('persona '):
            persona = cmd.split(' ', 1)[1]
            if self.ignis.switch_persona(persona):
                self.print_message(f"Switched to persona: {persona}")
            else:
                self.print_error(f"Failed to switch to persona: {persona}")
            return True

        elif cmd == 'clear':
            self.clear_screen()
            return True

        return False

    def set_mode(self, mode: str) -> bool:
        """Set response mode."""
        valid_modes = ['default', 'coding', 'creative', 'analytical', 'roleplay', 'assistant']
        if mode in valid_modes:
            self.current_mode = mode
            return True
        return False

    def print_help(self):
        """Print help information."""
        help_text = """
Available Commands:
  help, h, ?           - Show this help
  quit, exit, q        - Exit Ignis
  goodbye ignis        - Say goodbye to Ignis
  mode <type>          - Switch mode (default, coding, creative, analytical, roleplay, assistant)
  persona <name>       - Switch persona (default, sarcastic, professional, therapist)
  status               - Show system status
  clear                - Clear screen

User Configuration:
  Edit configs/user_config.json to set your name (default: "User")

Modes:
  default  - Standard conversation
  coding   - Programming assistance
  creative - Artistic and imaginative responses
  analytical - Logical analysis and reasoning
  roleplay - Character roleplay
  assistant - Helpful assistant mode

Just type your message for regular conversation.
"""

        if self.rich_available:
            panel = self.panel(help_text, title="Help", border_style="green")
            self.console.print(panel)
        else:
            print(help_text)

    def print_status(self):
        """Print system status."""
        status = self.ignis.get_status()

        status_text = f"""
System Status:
  Personality: {'Loaded' if status.get('personality', {}).get('traits_loaded') else 'Not loaded'}
  Memory: {'Available' if status.get('memory', {}).get('conversations_stored') is not None else 'Unavailable'}
  Inference: {'Ready' if status.get('inference', {}).get('model_loaded') else 'No model'}
  Current Mode: {self.current_mode}
  Current Persona: {status.get('personality', {}).get('current_persona', 'unknown')}
"""

        if self.rich_available:
            panel = self.panel(status_text, title="Status", border_style="yellow")
            self.console.print(panel)
        else:
            print(status_text)

    def print_message(self, message: str):
        """Print informational message."""
        if self.rich_available:
            self.console.print(f"[green]✓[/green] {message}")
        else:
            print(f"✓ {message}")

    def print_error(self, error: str):
        """Print error message."""
        if self.rich_available:
            self.console.print(f"[red]✗[/red] {error}")
        else:
            print(f"✗ {error}")

    def print_goodbye(self):
        """Print goodbye message."""
        goodbye_text = "\nGoodbye! Ignis will remember our conversation."

        if self.rich_available:
            self.console.print(self.text(goodbye_text, style="blue"))
        else:
            print(goodbye_text)

    async def _collect_response(self, message: str) -> str:
        """Collect the full response from streaming."""
        response_chunks = []
        async for chunk in self.ignis.chat_stream(message, mode=self.current_mode, user_name=self.user_name):
            response_chunks.append(chunk)
        return "".join(response_chunks)

    def _display_message(self, message: str, role: str):
        """Display a message in the conversation."""
        if self.rich_available:
            if role == "user":
                title = f"{self.user_name}"
                border_color = "green"
            else:
                title = "Ignis"
                border_color = "blue"

            panel = self.panel(message, title=title, border_style=border_color)
            self.console.print(panel)
        else:
            print(f"{role.title()}: {message}")

    def _display_conversation(self):
        """Display the full conversation history."""
        if not self.rich_available:
            return

        # Only clear and show welcome on first run
        if not hasattr(self, '_welcome_shown'):
            self.console.clear()
            self.print_welcome()
            self._welcome_shown = True
        else:
            self.console.clear()

        for msg in self.conversation_history:
            role = msg["role"]
            content = msg["content"]
            self._display_message(content, role)

    async def run_streaming_response(self, message: str, message_start_time: float):
        """Run streaming response display with live timer."""
        if not self.rich_available:
            # Fallback to simple streaming
            print(f"\nIgnis: ", end="", flush=True)
            response_chunks = []
            async for chunk in self.ignis.chat_stream(message, mode=self.current_mode, user_name=self.user_name):
                print(chunk, end="", flush=True)
                response_chunks.append(chunk)
            print()
            full_response = "".join(response_chunks)
            self.conversation_history.append({"role": "assistant", "content": full_response})
            return

        # Rich streaming with live timer
        import asyncio
        import time

        response_chunks = []
        full_response = ""

        def create_loading_display():
            elapsed = time.time() - message_start_time
            spinner_text = f"Ignis is thinking... ({elapsed:.1f}s)"
            return self.spinner("dots", text=spinner_text)

        def create_response_display():
            elapsed = time.time() - message_start_time
            current_text = "".join(response_chunks)
            response_display = self.text(current_text, style="white")
            return self.panel(response_display, title=f"Ignis - {elapsed:.1f}s", border_style="blue")

        # Start generation in background
        generation_task = asyncio.create_task(self._collect_response(message))

        # Show loading animation with live timer while generating
        with self.live(console=self.console, refresh_per_second=4) as live:
            start_display = time.time()
            while not generation_task.done():
                live.update(create_loading_display())
                await asyncio.sleep(0.1)

            # Generation complete, show final response
            full_response = await generation_task
            final_panel = self.panel(full_response, title="Ignis", border_style="blue")
            live.update(final_panel)

        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": full_response})

    async def run(self):
        """Run the terminal UI main loop."""
        self.print_welcome()
        self._welcome_shown = True

        while True:
            try:
                user_input = self.get_user_input()

                if user_input is None:  # EOF or interrupt
                    break

                if not user_input.strip():
                    continue

                # Check for commands first
                if self.handle_command(user_input):
                    continue

                # Start timer immediately when user sends message
                message_start_time = time.time()

                # Regular message - get response
                # Add user message to conversation history
                self.conversation_history.append({"role": "user", "content": user_input})

                # Display user message
                self._display_message(user_input, "user")

                # Use streaming if available
                await self.run_streaming_response(user_input, message_start_time)

            except Exception as e:
                self.print_error(f"An error occurred: {e}")
                logger.error(f"Terminal UI error: {e}")

        # Cleanup
        await self.ignis.shutdown()


async def run_cli(ignis_ai):
    """
    Run the CLI interface.

    Args:
        ignis_ai: IgnisAI instance
    """
    ui = TerminalUI(ignis_ai)
    await ui.run()