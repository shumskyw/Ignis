#!/usr/bin/env python3
"""
Test Phase 3 Integration with Memory System
"""

import json
import os
import sys
from pathlib import Path

# Add src to path - handle running from tests/ or project root
project_root = Path(__file__).parent
if str(project_root.name) == 'tests':
    # If run from tests/ directory, go up one level
    project_root = project_root.parent

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

try:
    from src.core.memory_system import EnhancedMemorySystem
except ImportError:
    print("Error: Run this test from the project root directory")
    sys.exit(1)

def test_phase3_integration():
    """Test that Phase 3 features are properly integrated."""
    print('🔗 Testing Phase 3 Integration with Memory System')
    print('=' * 50)

    # Load config
    config_path = project_root / 'configs' / 'memory_config.json'
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False

    # Create memory system instance
    try:
        memory = EnhancedMemorySystem("../configs")
    except Exception as e:
        print(f"❌ Failed to create memory system: {e}")
        return False

    # Test Phase 3 features
    print('Testing Phase 3 feature availability:')
    try:
        spaced_enabled = config["phase3_advanced_memory"]["spaced_repetition"]["enabled"]
        forgetting_enabled = config["phase3_advanced_memory"]["forgetting_curves"]["enabled"]
        interference_enabled = config["phase3_advanced_memory"]["memory_interference"]["enabled"]

        print(f'  Spaced repetition enabled: {spaced_enabled}')
        print(f'  Forgetting curves enabled: {forgetting_enabled}')
        print(f'  Memory interference enabled: {interference_enabled}')
    except KeyError as e:
        print(f"❌ Config structure error: {e}")
        return False

    # Test basic Phase 3 methods exist
    methods_to_check = [
        'calculate_review_interval',
        'schedule_memory_review',
        'process_memory_reviews',
        'update_memory_strength',
        'apply_forgetting_curves',
        'prevent_memory_interference',
        'get_pending_memory_reviews',
        'submit_memory_review_result'
    ]

    print('\nTesting Phase 3 method availability:')
    all_methods_present = True
    for method in methods_to_check:
        has_method = hasattr(memory, method)
        status = "✅" if has_method else "❌"
        print(f'  {method}: {status}')
        if not has_method:
            all_methods_present = False

    # Test Phase 3 instance variables
    vars_to_check = [
        'memory_review_queue',
        'memory_access_history',
        'memory_strength_scores',
        'memory_interference_map',
        'conversation_threads',
        'topic_threads',
        'session_summaries',
        'context_reconstruction_cache'
    ]

    print('\nTesting Phase 3 instance variables:')
    all_vars_present = True
    for var in vars_to_check:
        has_var = hasattr(memory, var)
        status = "✅" if has_var else "❌"
        print(f'  {var}: {status}')
        if not has_var:
            all_vars_present = False

    success = all_methods_present and all_vars_present
    if success:
        print('\n🎉 Phase 3 Integration Test PASSED!')
        print('✅ All Phase 3 features properly integrated')
    else:
        print('\n❌ Phase 3 Integration Test FAILED!')
        print('Some Phase 3 components missing')

    return success

if __name__ == "__main__":
    success = test_phase3_integration()
    sys.exit(0 if success else 1)