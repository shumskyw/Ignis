"""
Document reader plugin for Ignis AI.
Allows reading and processing local documents.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_plugin import BasePlugin


class DocumentReaderPlugin(BasePlugin):
    """
    Plugin that allows reading local documents for context.
    """

    def __init__(self):
        super().__init__(
            name="document_reader",
            description="Reads and processes local documents for context"
        )

        # Supported file types
        self.supported_extensions = {
            '.txt': self._read_text_file,
            '.md': self._read_text_file,
            '.pdf': self._read_pdf_file,
            '.html': self._read_html_file,
            '.htm': self._read_html_file,
        }

        # Document cache
        self.document_cache: Dict[str, Dict[str, Any]] = {}

    async def process_message(self, message: str) -> Optional[str]:
        """
        Process user message for document references.

        Args:
            message: User message

        Returns:
            Modified message with document content or None
        """
        # Check for document read commands
        doc_commands = self._extract_document_commands(message)
        if doc_commands:
            enhanced_message = await self._process_document_commands(message, doc_commands)
            return enhanced_message

        return None

    async def process_response(self, message: str, response: str) -> str:
        """
        Process AI response (no changes for document reader).

        Args:
            message: Original user message
            response: AI response

        Returns:
            Unmodified response
        """
        return response

    def _extract_document_commands(self, message: str) -> List[Dict[str, Any]]:
        """
        Extract document read commands from message.

        Args:
            message: User message

        Returns:
            List of document commands
        """
        commands = []

        # Pattern: read file "path/to/file.txt"
        read_pattern = re.compile(r'read\s+(?:file|document)\s+["\']([^"\']+)["\']', re.IGNORECASE)
        matches = read_pattern.findall(message)

        for file_path in matches:
            commands.append({
                'type': 'read',
                'path': file_path,
                'action': 'read_full'
            })

        # Pattern: summarize "path/to/file.txt"
        summarize_pattern = re.compile(r'summarize\s+["\']([^"\']+)["\']', re.IGNORECASE)
        matches = summarize_pattern.findall(message)

        for file_path in matches:
            commands.append({
                'type': 'read',
                'path': file_path,
                'action': 'summarize'
            })

        return commands

    async def _process_document_commands(self, message: str, commands: List[Dict[str, Any]]) -> str:
        """
        Process document commands and enhance message.

        Args:
            message: Original message
            commands: Document commands

        Returns:
            Enhanced message with document content
        """
        document_contents = []

        for command in commands:
            file_path = command['path']
            action = command['action']

            try:
                content = await self._read_document(file_path, action)
                if content:
                    document_contents.append(f"Document: {file_path}\n{content}")
                else:
                    document_contents.append(f"Document: {file_path}\n[Could not read document]")

            except Exception as e:
                self.logger.error(f"Failed to read document {file_path}: {e}")
                document_contents.append(f"Document: {file_path}\n[Error reading document: {str(e)}]")

        if document_contents:
            # Add document content to message
            doc_section = "\n\n[DOCUMENT CONTEXT]\n" + "\n\n".join(document_contents)
            enhanced_message = message + doc_section
            return enhanced_message

        return message

    async def _read_document(self, file_path: str, action: str = 'read_full') -> Optional[str]:
        """
        Read a document from file path.

        Args:
            file_path: Path to document
            action: Action to perform ('read_full' or 'summarize')

        Returns:
            Document content or None
        """
        # Resolve path (relative to current directory or absolute)
        try:
            path = Path(file_path).resolve()

            # Security check - only allow reading from current directory and subdirs
            current_dir = Path.cwd()
            if not str(path).startswith(str(current_dir)):
                # Allow reading from user documents directory
                documents_dir = Path.home() / "Documents"
                if not str(path).startswith(str(documents_dir)):
                    self.logger.warning(f"Access denied to file outside allowed directories: {path}")
                    return None

            if not path.exists():
                return f"[File not found: {file_path}]"

            if not path.is_file():
                return f"[Path is not a file: {file_path}]"

            # Check if supported file type
            if path.suffix.lower() not in self.supported_extensions:
                return f"[Unsupported file type: {path.suffix}]"

            # Read file
            reader_func = self.supported_extensions[path.suffix.lower()]
            content = await reader_func(path)

            if action == 'summarize':
                content = self._summarize_content(content, max_length=500)

            return content

        except Exception as e:
            self.logger.error(f"Error reading document {file_path}: {e}")
            return f"[Error reading document: {str(e)}]"

    async def _read_text_file(self, path: Path) -> str:
        """Read text/markdown file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            # Try with different encoding
            with open(path, 'r', encoding='latin-1') as f:
                content = f.read()
            return content

    async def _read_pdf_file(self, path: Path) -> str:
        """Read PDF file."""
        try:
            import pypdf2
            with open(path, 'rb') as f:
                pdf_reader = pypdf2.PdfReader(f)
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text() + "\n"
            return content
        except ImportError:
            return "[PDF reading not available - install pypdf2]"
        except Exception as e:
            return f"[Error reading PDF: {str(e)}]"

    async def _read_html_file(self, path: Path) -> str:
        """Read HTML file."""
        try:
            from bs4 import BeautifulSoup
            with open(path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                # Extract text content
                text = soup.get_text(separator='\n', strip=True)
            return text
        except ImportError:
            return "[HTML reading not available - install beautifulsoup4]"
        except Exception as e:
            return f"[Error reading HTML: {str(e)}]"

    def _summarize_content(self, content: str, max_length: int = 500) -> str:
        """
        Create a simple summary of content.

        Args:
            content: Full content
            max_length: Maximum summary length

        Returns:
            Summarized content
        """
        if len(content) <= max_length:
            return content

        # Simple truncation with ellipsis
        summary = content[:max_length - 3] + "..."
        return summary

    def get_status(self) -> Dict[str, Any]:
        """Get plugin status."""
        status = super().get_status()
        status.update({
            'supported_formats': list(self.supported_extensions.keys()),
            'cached_documents': len(self.document_cache)
        })
        return status