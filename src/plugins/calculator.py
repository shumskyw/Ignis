"""
Calculator plugin for Ignis AI.
Provides mathematical calculation capabilities.
"""

import math
import re
from typing import Any, Dict, List, Optional

from .base_plugin import BasePlugin


class CalculatorPlugin(BasePlugin):
    """
    Plugin that provides mathematical calculation capabilities.
    """

    def __init__(self):
        super().__init__(
            name="calculator",
            description="Provides mathematical calculation capabilities"
        )

        # Math expression patterns
        self.calc_patterns = [
            re.compile(r'calculate\s+(.+?)(?:\?|$)', re.IGNORECASE),
            re.compile(r'what\s+is\s+(.+?)(?:\?|$)', re.IGNORECASE),
            re.compile(r'compute\s+(.+?)(?:\?|$)', re.IGNORECASE),
            re.compile(r'solve\s+(.+?)(?:\?|$)', re.IGNORECASE),
        ]

        # Safe math functions
        self.safe_functions = {
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'sqrt': math.sqrt,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'pi': math.pi,
            'e': math.e,
            'abs': abs,
            'round': round,
            'max': max,
            'min': min,
        }

    async def process_message(self, message: str) -> Optional[str]:
        """
        Process user message for math expressions.

        Args:
            message: User message

        Returns:
            Modified message with calculation result or None
        """
        # Check if message contains math
        if self._is_math_message(message):
            result = self._calculate_expression(message)
            if result is not None:
                # Add calculation result to message
                enhanced_message = f"{message}\n\n[MATHEMATICAL CONTEXT: {result}]"
                return enhanced_message

        return None

    async def process_response(self, message: str, response: str) -> str:
        """
        Process AI response (no changes for calculator).

        Args:
            message: Original user message
            response: AI response

        Returns:
            Unmodified response
        """
        return response

    def _is_math_message(self, message: str) -> bool:
        """
        Determine if a message contains mathematical expressions.

        Args:
            message: Message to check

        Returns:
            True if math-related
        """
        message_lower = message.lower()

        # Check for calculation keywords
        calc_keywords = ['calculate', 'compute', 'solve', 'what is', 'math']
        if any(keyword in message_lower for keyword in calc_keywords):
            return True

        # Check for mathematical operators
        math_ops = ['+', '-', '*', '/', '^', 'sqrt', 'sin', 'cos', 'tan', 'log']
        if any(op in message for op in math_ops):
            return True

        # Check for numbers
        if re.search(r'\d', message):
            return True

        return False

    def _calculate_expression(self, message: str) -> Optional[str]:
        """
        Extract and calculate mathematical expression from message.

        Args:
            message: Message containing math

        Returns:
            Calculation result or None
        """
        # Try to extract expression from patterns
        for pattern in self.calc_patterns:
            match = pattern.search(message)
            if match:
                expression = match.group(1).strip()
                result = self._evaluate_expression(expression)
                if result is not None:
                    return f"{expression} = {result}"

        # Try to find any mathematical expression
        # Look for patterns like "2 + 2", "sqrt(16)", etc.
        expr_patterns = [
            re.compile(r'(\d+(?:\.\d+)?\s*[\+\-\*\/\^]\s*\d+(?:\.\d+)?)'),  # Basic ops
            re.compile(r'(sqrt|sin|cos|tan|log)\s*\(\s*[\d\.]+\s*\)'),  # Functions
        ]

        for pattern in expr_patterns:
            matches = pattern.findall(message)
            if matches:
                results = []
                for expr in matches:
                    result = self._evaluate_expression(expr)
                    if result is not None:
                        results.append(f"{expr} = {result}")

                if results:
                    return "; ".join(results)

        return None

    def _evaluate_expression(self, expression: str) -> Optional[float]:
        """
        Safely evaluate a mathematical expression.

        Args:
            expression: Math expression to evaluate

        Returns:
            Result or None if invalid
        """
        try:
            # Replace ^ with ** for exponentiation
            expression = expression.replace('^', '**')

            # Create safe evaluation environment
            safe_dict = self.safe_functions.copy()

            # Evaluate expression
            result = eval(expression, {"__builtins__": {}}, safe_dict)

            # Ensure result is a number
            if isinstance(result, (int, float)) and not math.isnan(result) and not math.isinf(result):
                return round(result, 6)  # Round to reasonable precision
            else:
                return None

        except (SyntaxError, NameError, TypeError, ZeroDivisionError, ValueError):
            return None
        except Exception:
            return None

    def get_status(self) -> Dict[str, Any]:
        """Get plugin status."""
        status = super().get_status()
        status.update({
            'features': [
                'basic arithmetic',
                'trigonometric functions',
                'logarithmic functions',
                'safe expression evaluation'
            ],
            'supported_functions': list(self.safe_functions.keys())
        })
        return status