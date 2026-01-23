#!/usr/bin/env python3
"""
Test script for assumption detection functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.core.ignis import IgnisAI


def test_assumption_detection():
    """Test that assumption detection works correctly."""

    # Create a minimal IgnisAI instance for testing
    ai = IgnisAI()

    # Mock context with user name
    class MockContext:
        def __init__(self):
            self._current_user_name = "Jin"

    mock_context = MockContext()
    ai.context = mock_context

    test_cases = [
        # Should trigger assumption detection
        ("Your favorite color is blue", True, "Direct assumption about favorite color"),
        ("I think your favorite food is pizza", True, "Qualified assumption that should still be flagged"),
        ("Jin prefers tea over coffee", True, "Assumption using user's name"),
        ("It's definitely your favorite", True, "Definite statement about preference"),

        # Should NOT trigger (has qualifiers)
        ("I don't know your favorite color", False, "Properly admits ignorance"),
        ("I'm not sure what you prefer", False, "Expresses uncertainty"),
        ("You haven't told me your favorite", False, "Acknowledges lack of information"),

        # Should NOT trigger (not about preferences)
        ("The sky is blue", False, "Not about user preferences"),
        ("I like programming", False, "AI expressing its own preference"),
    ]

    print("🧪 Testing Assumption Detection")
    print("=" * 50)

    for test_response, should_detect, description in test_cases:
        # Test the validation method
        validated_response = ai._validate_core_identity(test_response)

        # Check if assumption was detected (response should be different if detected)
        assumption_detected = validated_response != test_response

        status = "✅ PASS" if assumption_detected == should_detect else "❌ FAIL"
        print(f"{status} {description}")
        print(f"   Input: '{test_response}'")
        print(f"   Expected detection: {should_detect}, Got: {assumption_detected}")
        if assumption_detected:
            print(f"   Corrected to: '{validated_response}'")
        print()

if __name__ == "__main__":
    test_assumption_detection()