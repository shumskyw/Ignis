#!/usr/bin/env python3
"""
Test script for expanded negative emotion range.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.core.ignis import ConversationPlanner


def test_expanded_negative_emotions():
    # Test the expanded negative emotion range
    planner = ConversationPlanner()

    test_cases = [
        'I hate this so much!',  # very_negative
        'This is absolutely terrible',  # very_negative
        'I\'m really frustrated',  # negative
        'This is disappointing',  # negative
        'I\'m a bit worried',  # mildly_negative
        'Whatever, it doesn\'t matter',  # dismissive
        'Prove it then!',  # confrontational
        'I seriously doubt that',  # skeptical
        'This is ridiculous',  # skeptical
    ]

    print('🌓 Testing Expanded Negative Emotion Range')
    print('=' * 50)

    for msg in test_cases:
        analysis = planner.analyze_conversation_state(msg, [])
        emotion = analysis['user_emotion']
        strategy = analysis['strategy']

        print(f'"{msg}" → Emotion: {emotion}')
        print(f'    Strategy: {strategy["engagement_style"]} / {strategy["tone"]} / {strategy.get("communication_mode", "direct")}')
        print()

    print('✅ Expanded negative emotion range test complete')

if __name__ == '__main__':
    test_expanded_negative_emotions()