#!/usr/bin/env python3
"""
Test script for conversation continuity and interview mode.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.core.ignis import ConversationPlanner


def test_conversation_continuity():
    """Test that conversation mode detection works."""

    # Initialize planner
    planner = ConversationPlanner()

    # Simulate the user's conversation scenario
    test_messages = [
        "But enough about us, how about your own favorites? Do you prefer coffee or tea, vinyl records or digital music, or perhaps cats or dogs? There's no wrong answer here – just the opportunity to learn more about each other in this interview-like conversation we find ourselves having.",
        "Haha I prefer coffee over any drink, I love digital music, and am a cat person"
    ]

    conversation_history = []

    print("🧪 Testing Conversation Continuity and Interview Mode")
    print("=" * 60)

    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Message {i} ---")
        print(f"User: {message}")

        # Add to history
        conversation_history.append({"role": "user", "content": message})

        # Analyze conversation state
        analysis = planner.analyze_conversation_state(message, conversation_history)
        guidance = planner.get_response_guidance(analysis['strategy'])

        print(f"Intent: {analysis['intent']}")
        print(f"Conversation Mode: {planner.conversation_state['conversation_mode']}")
        print(f"Conversation Phase: {planner.conversation_state['conversation_phase']}")
        print(f"Response Guidance: {guidance[:200]}...")

    print("\n" + "=" * 60)
    print("Test completed. Check if:")
    print("1. Conversation mode was detected as 'interview'")
    print("2. Response guidance includes INTERVIEW MODE instructions")
    print("3. Guidance emphasizes conciseness")