#!/usr/bin/env python3
"""
Test Phase 2 Memory Safeguards Implementation
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path - handle running from tests/ or project root
project_root = Path(__file__).parent
if str(project_root.name) == 'tests':
    # If run from tests/ directory, go up one level
    project_root = project_root.parent

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

def test_phase2_safeguards():
    """Test all Phase 2 memory safeguard methods."""
    print("🛡️  Testing Phase 2 Memory Safeguards")
    print("=" * 50)

    try:
        from src.core.memory_system import EnhancedMemorySystem
        memory = EnhancedMemorySystem("../configs")
    except Exception as e:
        print(f"❌ Failed to initialize memory system: {e}")
        return False

    tests_passed = 0
    total_tests = 9  # Updated to match actual number of sub-tests

    # Test with normal fact
    normal_fact = "The capital of France is Paris."
    result = memory.validate_memory(normal_fact, "reliable_source")
    print(f"   Normal fact validation: confidence={result['confidence']:.2f}, valid={result['is_valid']}")
    if result['is_valid'] and result['confidence'] > 0.7:
        tests_passed += 1
        print("   ✅ PASSED")
    else:
        print("   ❌ FAILED")

    # Test with hallucination pattern
    hallucination_fact = "The moon is made of green cheese and has cities on it."
    result = memory.validate_memory(hallucination_fact, "ai_generated")
    print(f"   Hallucination fact validation: confidence={result['confidence']:.2f}, valid={result['is_valid']}")
    if not result['is_valid'] or result['confidence'] < 0.5:
        tests_passed += 1
        print("   ✅ PASSED")
    else:
        print("   ❌ FAILED")

    # Test 2: detect_contradictions
    print("\n2. Testing detect_contradictions")

    # Add a fact to the system first
    memory.fact_confidence["test_fact_1"] = 0.9
    memory.fact_metadata["test_fact_1"] = {"content": "The sky is blue."}

    # Test contradiction detection
    contradictory_fact = "The sky is green."
    contradictions = memory.detect_contradictions(contradictory_fact)
    print(f"   Detected {len(contradictions)} contradictions")
    if len(contradictions) > 0:
        tests_passed += 1
        print("   ✅ PASSED")
    else:
        print("   ❌ FAILED")

    # Test 3: verify_sources
    print("\n3. Testing verify_sources")

    fact = "Water boils at 100 degrees Celsius."
    result = memory.verify_sources(fact, "scientific_source", ["scientific_source", "reliable_news"])
    print(f"   Source verification: verified={result['is_verified']}, confidence={result['confidence']:.2f}")
    if result['is_verified'] and result['confidence'] > 0.8:
        tests_passed += 1
        print("   ✅ PASSED")
    else:
        print("   ❌ FAILED")

    # Test with unreliable source
    result = memory.verify_sources(fact, "unknown_blog", ["scientific_source", "reliable_news"])
    print(f"   Unreliable source verification: verified={result['is_verified']}, confidence={result['confidence']:.2f}")
    if not result['is_verified'] or result['confidence'] < 0.7:
        tests_passed += 1
        print("   ✅ PASSED")
    else:
        print("   ❌ FAILED")

    # Test 4: check_temporal_consistency
    print("\n4. Testing check_temporal_consistency")

    # Test with temporally consistent fact
    consistent_fact = "The meeting is scheduled for tomorrow."
    result = memory.check_temporal_consistency(consistent_fact)
    print(f"   Temporal consistency check: consistent={result['is_consistent']}, confidence={result['confidence']:.2f}")
    if result['is_consistent']:
        tests_passed += 1
        print("   ✅ PASSED")
    else:
        print("   ❌ FAILED")

    # Test 5: rule_based_validation
    print("\n5. Testing rule_based_validation")

    # Test with valid fact
    valid_fact = "Machine learning is a subset of artificial intelligence."
    result = memory.rule_based_validation(valid_fact)
    print(f"   Rule-based validation: valid={result['is_valid']}, confidence={result['overall_confidence']:.2f}")
    if result['is_valid'] and result['overall_confidence'] > 0.8:
        tests_passed += 1
        print("   ✅ PASSED")
    else:
        print("   ❌ FAILED")

    # Test with invalid fact (too short)
    invalid_fact = "Hi."
    result = memory.rule_based_validation(invalid_fact)
    print(f"   Invalid fact validation: valid={result['is_valid']}, failed_rules={len(result['failed_rules'])}")
    if not result['is_valid'] or len(result['failed_rules']) > 0:
        tests_passed += 1
        print("   ✅ PASSED")
    else:
        print("   ❌ FAILED")

    # Test 6: apply_memory_decay
    print("\n6. Testing apply_memory_decay")

    # Add some test facts with different ages
    test_facts = ["decay_fact_1", "decay_fact_2", "decay_fact_3"]
    for fact_id in test_facts:
        memory.fact_confidence[fact_id] = 0.9
        memory.fact_metadata[fact_id] = {
            "content": f"Test fact {fact_id}",
            "created_at": (datetime.now() - timedelta(days=30)).isoformat()
        }

    # Apply memory decay
    decay_result = memory.apply_memory_decay(test_facts, "natural")
    print(f"   Memory decay applied: processed={decay_result['facts_processed']}, decayed={decay_result['facts_decayed']}")
    if decay_result['facts_processed'] == len(test_facts) and decay_result['facts_decayed'] > 0:
        tests_passed += 1
        print("   ✅ PASSED")
    else:
        print("   ❌ FAILED")

    # Summary
    print("\n" + "=" * 50)
    print("🛡️  PHASE 2 SAFEGUARDS TEST SUMMARY")
    print("=" * 50)
    print(f"Tests Passed: {tests_passed}/{total_tests} ({tests_passed/total_tests*100:.1f}%)")

    if tests_passed == total_tests:
        print("🎉 ALL PHASE 2 SAFEGUARDS TESTS PASSED!")
        print("✅ Memory validation system working")
        print("✅ Contradiction detection functional")
        print("✅ Source verification operational")
        print("✅ Temporal consistency checking active")
        print("✅ Rule-based validation implemented")
        print("✅ Memory decay simulation applied")
        return True
    else:
        print("⚠️  SOME PHASE 2 TESTS FAILED")
        print("❌ Review safeguard implementations")
        return False

if __name__ == "__main__":
    success = test_phase2_safeguards()
    sys.exit(0 if success else 1)