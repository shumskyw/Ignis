#!/usr/bin/env python3
"""
Test script to check context building for verbosity issues
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Direct import to avoid relative import issues
import importlib.util

spec = importlib.util.spec_from_file_location("context_manager", os.path.join(os.path.dirname(__file__), 'src', 'core', 'context_manager.py'))
context_module = importlib.util.module_from_spec(spec)
sys.modules["context_manager"] = context_module
spec.loader.exec_module(context_module)

ContextManager = context_module.ContextManager

def test_context_building():
    # Create context manager
    context_manager = ContextManager("./configs")

    # Test simple greeting
    message = "Hello Ignis"
    memories = []
    personality_traits = {}
    emotional_state = {}
    user_name = "Jin"
    user_context = {
        'relationship': 'creator-user',
        'interaction_count': 10,
        'is_creator': True
    }
    conversation_history = []

    context = context_manager.build(
        message=message,
        memories=memories,
        personality_traits=personality_traits,
        emotional_state=emotional_state,
        user_name=user_name,
        user_context=user_context,
        conversation_history=conversation_history
    )

    print("Context for 'Hello Ignis':")
    print("=" * 50)
    print(context)
    print("=" * 50)

    # Check if Ignis profile info is included
    if "About Ignis:" in context:
        print("❌ IGNIS PROFILE INCLUDED IN CONTEXT (should not be for simple greeting)")
    else:
        print("✅ No Ignis profile in context")

    if "USER RELATIONSHIP CONTEXT:" in context:
        print("❌ USER RELATIONSHIP CONTEXT INCLUDED (should not be for simple greeting)")
    else:
        print("✅ No user relationship context")

if __name__ == "__main__":
    test_context_building()