#!/usr/bin/env python3
"""
Test script for conversation reasoning logic.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.core.ignis import ConversationPlanner


def test_reasoning():
    planner = ConversationPlanner()

    # Test various conversation scenarios
    scenarios = [
        ('Hello, how are you?', 'greeting'),
        ('Tell me about yourself', 'introduction'),
        ('That\'s interesting, tell me more', 'deep_dive'),
        ('Why do you think that?', 'question'),
        ('I disagree with that', 'feedback'),
        ('Thanks for the help!', 'conclusion')
    ]

    history = []

    print('🧠 Testing Conversation Reasoning Logic')
    print('=' * 50)

    for message, expected_phase in scenarios:
        analysis = planner.analyze_conversation_state(message, history)

        print(f'\nMessage: "{message}"')
        print(f'  Intent: {analysis["intent"]}')
        print(f'  Emotion: {analysis["user_emotion"]}')
        print(f'  Phase: {analysis["conversation_phase"]} (expected: {expected_phase})')
        print(f'  Strategy: {analysis["strategy"]["engagement_style"]} tone')

        # Add to history
        history.append({'role': 'user', 'content': message})
        history.append({'role': 'assistant', 'content': 'Sample response'})

    print('\n✅ Reasoning Logic Test Complete')

if __name__ == '__main__':
    test_reasoning()