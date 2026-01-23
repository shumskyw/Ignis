#!/usr/bin/env python3
"""
Test script for improved conversation reasoning logic.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.core.ignis import ConversationPlanner


def test_improved_reasoning():
    planner = ConversationPlanner()

    # Test scenarios that were previously problematic
    test_cases = [
        # Intent detection improvements
        ('I disagree with that approach', 'feedback', 'Intent should detect disagreement'),
        ('Tell me about yourself', 'request_introduction', 'Should detect introduction request'),
        ('That\'s absolutely amazing!', 'emotional', 'Should detect strong positive emotion'),
        ('I\'m really frustrated with this', 'feedback', 'Should detect frustration as feedback'),

        # Phase transition improvements
        ('Hello, how are you?', 'greeting', 'Should recognize greeting'),
        ('That\'s interesting, tell me more', 'request_explanation', 'Should detect explanation request'),
        ('Thanks for the help!', 'emotional', 'Should recognize thanks as emotional'),

        # Emotion detection improvements
        ('This is really cool!', 'positive', 'Should detect positive emotion'),
        ('I\'m a bit worried about that', 'mildly_negative', 'Should detect mild negative'),
        ('Sure, that makes total sense', 'sarcastic', 'Should detect potential sarcasm'),
        ('I\'m curious about how this works', 'analytical', 'Should detect analytical interest'),
    ]

    history = []

    print('🧠 Testing Improved Conversation Reasoning Logic')
    print('=' * 60)

    for message, expected_intent, description in test_cases:
        analysis = planner.analyze_conversation_state(message, history)

        actual_intent = analysis["intent"]
        actual_emotion = analysis["user_emotion"]
        actual_phase = analysis["conversation_phase"]
        strategy = analysis["strategy"]

        print(f'\nTest: {description}')
        print(f'Message: "{message}"')
        print(f'  Intent: {actual_intent} (expected: {expected_intent}) {"✅" if actual_intent == expected_intent else "❌"}')
        print(f'  Emotion: {actual_emotion}')
        print(f'  Phase: {actual_phase}')
        print(f'  Strategy: {strategy["engagement_style"]} / {strategy["tone"]} / {strategy.get("communication_mode", "direct")}')

        # Add to history for context
        history.append({'role': 'user', 'content': message})
        history.append({'role': 'assistant', 'content': 'Sample response'})

    print('\n' + '=' * 60)
    print('✅ Improved Reasoning Logic Test Complete')

if __name__ == '__main__':
    test_improved_reasoning()