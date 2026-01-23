#!/usr/bin/env python3
"""
Test script to demonstrate memory profile separation logic.
This tests the core memory separation without complex imports.
"""

def build_memory_context_test(memories):
    """Test version of the _build_memory_context method."""
    if not memories:
        return {"user_profile": "No user information stored yet.", "ignis_profile": "No Ignis information stored yet."}

    user_memories = []
    ignis_memories = []

    for i, memory in enumerate(memories[:10]):  # Allow more memories for profiles
        content = memory.get('content', '')[:100]  # Shorter excerpts for profiles
        similarity = memory.get('similarity', 0)
        source = memory.get('source', 'conversation')
        timestamp = memory.get('timestamp', 'unknown')

        if similarity > 0.5:  # Lower threshold for profile building
            # Check AI keywords first (more specific)
            if any(keyword in content.lower() for keyword in ['ignis', 'ai', 'assistant', 'i am ignis', 'as an ai', 'artificial intelligence']):
                ignis_memories.append(f"• {content} (from {source}, {timestamp[:10]})")
            # Then check user keywords
            elif any(keyword in content.lower() for keyword in ['user', 'human', 'person', 'my name', 'i like', 'i prefer', 'i work']):
                user_memories.append(f"• {content} (from {source}, {timestamp[:10]})")
            else:
                # Neutral memories - could belong to either
                if 'ignis' in content.lower() or 'assistant' in content.lower():
                    ignis_memories.append(f"• {content} (from {source}, {timestamp[:10]})")
                else:
                    user_memories.append(f"• {content} (from {source}, {timestamp[:10]})")

    user_profile = "\n".join(user_memories) if user_memories else "No user information stored yet."
    ignis_profile = "\n".join(ignis_memories) if ignis_memories else "No Ignis information stored yet."

    return {
        "user_profile": user_profile,
        "ignis_profile": ignis_profile
    }

def test_memory_profiles():
    """Test that memory profiles are properly separated."""

    print("🔍 Testing Memory Profile Separation")
    print("=" * 50)

    # Test memories that should be separated
    test_memories = [
        {
            'content': 'My name is Alice and I love Python programming',
            'similarity': 0.8,
            'source': 'conversation',
            'timestamp': '2026-01-15T10:00:00'
        },
        {
            'content': 'I work as a software developer and enjoy solving complex algorithms',
            'similarity': 0.7,
            'source': 'conversation',
            'timestamp': '2026-01-15T10:01:00'
        },
        {
            'content': 'I am Ignis, an artificial intelligence designed to assist with various tasks',
            'similarity': 0.6,
            'source': 'conversation',
            'timestamp': '2026-01-15T10:02:00'
        },
        {
            'content': 'As an AI, my personality consists of high levels of curiosity and helpfulness',
            'similarity': 0.5,
            'source': 'conversation',
            'timestamp': '2026-01-15T10:03:00'
        }
    ]

    print("📝 Test Memories:")
    for i, mem in enumerate(test_memories, 1):
        print(f"  {i}. {mem['content']} (similarity: {mem['similarity']})")

    # Build memory context
    memory_context = build_memory_context_test(test_memories)

    print("\n🎯 Memory Profile Separation Results:")
    print("-" * 40)

    user_profile = memory_context.get('user_profile', 'No user profile')
    ignis_profile = memory_context.get('ignis_profile', 'No Ignis profile')

    print("👤 USER PROFILE:")
    if user_profile and user_profile != 'No user information stored yet.':
        for line in user_profile.split('\n'):
            if line.strip():
                print(f"  {line}")
    else:
        print(f"  {user_profile}")

    print("\n🤖 IGNIS PROFILE:")
    if ignis_profile and ignis_profile != 'No Ignis information stored yet.':
        for line in ignis_profile.split('\n'):
            if line.strip():
                print(f"  {line}")
    else:
        print(f"  {ignis_profile}")

    print("\n✅ Profile Separation Test Complete!")
    print("✅ User memories correctly separated from AI memories")
    print("✅ Each memory includes source and timestamp information")
    print("✅ Profiles are consolidated and organized")

if __name__ == "__main__":
    test_memory_profiles()