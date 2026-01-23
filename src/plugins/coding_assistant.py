"""
Coding assistant plugin for Ignis AI.
Provides programming help and code analysis.
"""

import re
from typing import Any, Dict, List, Optional

from .base_plugin import BasePlugin


class CodingAssistantPlugin(BasePlugin):
    """
    Plugin that provides coding assistance features.
    """

    def __init__(self):
        super().__init__(
            name="coding_assistant",
            description="Provides programming help and code analysis"
        )

        # Code patterns to detect
        self.code_patterns = {
            'python': re.compile(r'```python\s*\n(.*?)\n```', re.DOTALL),
            'javascript': re.compile(r'```javascript\s*\n(.*?)\n```', re.DOTALL),
            'java': re.compile(r'```java\s*\n(.*?)\n```', re.DOTALL),
            'cpp': re.compile(r'```cpp\s*\n(.*?)\n```', re.DOTALL),
            'c': re.compile(r'```c\s*\n(.*?)\n```', re.DOTALL),
        }

        # Programming keywords
        self.programming_keywords = [
            'function', 'class', 'def', 'import', 'from', 'if', 'for', 'while',
            'try', 'except', 'return', 'print', 'console.log', 'int', 'string',
            'public', 'private', 'void', 'main', 'include', 'using'
        ]

    async def process_message(self, message: str) -> Optional[str]:
        """
        Process user message for coding assistance.

        Args:
            message: User message

        Returns:
            Modified message or None
        """
        # Detect if this is a coding-related message
        if self._is_coding_message(message):
            # Add coding context to the message
            enhanced_message = f"[CODING CONTEXT] {message}"
            return enhanced_message

        return None

    async def process_response(self, message: str, response: str) -> str:
        """
        Process AI response for coding assistance.

        Args:
            message: Original user message
            response: AI response

        Returns:
            Enhanced response
        """
        if not self._is_coding_message(message):
            return response

        # Enhance response with coding features
        enhanced_response = self._enhance_coding_response(response)

        return enhanced_response

    def _is_coding_message(self, message: str) -> bool:
        """
        Determine if a message is coding-related.

        Args:
            message: Message to check

        Returns:
            True if coding-related
        """
        message_lower = message.lower()

        # Check for code blocks
        for pattern in self.code_patterns.values():
            if pattern.search(message):
                return True

        # Check for programming keywords
        for keyword in self.programming_keywords:
            if keyword in message_lower:
                return True

        # Check for coding-related phrases
        coding_phrases = [
            'code', 'program', 'function', 'class', 'bug', 'error', 'debug',
            'compile', 'syntax', 'algorithm', 'data structure', 'api', 'library'
        ]

        for phrase in coding_phrases:
            if phrase in message_lower:
                return True

        return False

    def _enhance_coding_response(self, response: str) -> str:
        """
        Enhance response with coding-specific features.

        Args:
            response: Original response

        Returns:
            Enhanced response
        """
        enhanced = response

        # Add code quality tips if code is present
        if self._contains_code(response):
            tips = self._generate_code_tips(response)
            if tips:
                enhanced += f"\n\n💡 **Code Tips:**\n{tips}"

        # Add debugging suggestions for error messages
        if self._contains_error_message(response):
            debug_help = self._generate_debug_help(response)
            if debug_help:
                enhanced += f"\n\n🔧 **Debug Help:**\n{debug_help}"

        return enhanced

    def _contains_code(self, text: str) -> bool:
        """Check if text contains code blocks."""
        for pattern in self.code_patterns.values():
            if pattern.search(text):
                return True
        return False

    def _contains_error_message(self, text: str) -> bool:
        """Check if text contains error messages."""
        error_indicators = [
            'error', 'exception', 'traceback', 'syntaxerror', 'nameerror',
            'typeerror', 'valueerror', 'importerror', 'indentationerror'
        ]

        text_lower = text.lower()
        return any(indicator in text_lower for indicator in error_indicators)

    def _generate_code_tips(self, response: str) -> str:
        """Generate code quality tips."""
        tips = []

        # Extract code from response
        code_blocks = []
        for pattern in self.code_patterns.values():
            matches = pattern.findall(response)
            code_blocks.extend(matches)

        if not code_blocks:
            return ""

        # Analyze code for common issues
        for code in code_blocks:
            # Check for basic Python issues (simplified)
            if 'def ' in code and 'return' not in code:
                tips.append("• Consider adding a return statement to your function")
            if 'import' in code and 'as' not in code:
                tips.append("• Use 'import module as alias' for better readability")
            if 'print(' in code:
                tips.append("• Consider using logging instead of print for production code")

        return '\n'.join(tips) if tips else ""

    def _generate_debug_help(self, response: str) -> str:
        """Generate debugging help."""
        help_text = []

        response_lower = response.lower()

        if 'syntaxerror' in response_lower:
            help_text.append("• Check for missing colons, parentheses, or quotes")
            help_text.append("• Verify indentation is consistent")
        elif 'nameerror' in response_lower:
            help_text.append("• Make sure the variable is defined before use")
            help_text.append("• Check for typos in variable names")
        elif 'typeerror' in response_lower:
            help_text.append("• Verify you're using the correct data types")
            help_text.append("• Check function arguments match expected types")
        elif 'importerror' in response_lower:
            help_text.append("• Ensure the module is installed: pip install <module>")
            help_text.append("• Check the module name spelling")

        return '\n'.join(help_text) if help_text else ""

    def get_status(self) -> Dict[str, Any]:
        """Get plugin status."""
        status = super().get_status()
        status.update({
            'features': [
                'code detection',
                'code quality tips',
                'debugging assistance'
            ]
        })
        return status