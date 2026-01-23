#!/usr/bin/env python3
"""
Simple test script to check hallucination detection logic
"""

def test_assumption_detection():
    """Test the assumption detection logic directly"""

    # Test response that should be flagged
    response = "Your favorite color is blue, right?"
    response_lower = response.lower()
    user_name = "User"

    preference_assumptions = [
        "your favorite color is",
        "you prefer",
        "you like",
        "your favorite",
        f"{user_name.lower()}'s favorite",
        f"{user_name.lower()} is a",
        f"{user_name.lower()} prefers",
        f"{user_name.lower()} likes",
        f"{user_name.lower()}'s favorite color",
        "i believe it's",
        "i think it's",
        "it's definitely",
        "it's probably"
    ]

    assumption_errors = []

    for assumption in preference_assumptions:
        if assumption in response_lower and not any(word in response_lower for word in ["i don't know", "i'm not sure", "you haven't told me", "i recall", "as i remember"]):
            # Only flag if it's a definitive statement without qualifiers
            if not any(qualifier in response_lower for qualifier in ["maybe", "perhaps", "could be", "might be", "i'm guessing"]):
                # Exclude self-referential statements (e.g., "your favorite AI" when referring to itself)
                if not any(self_ref in response_lower for self_ref in ["your favorite ai", "your favorite assistant", "your favorite ignis", "as your favorite"]):
                    assumption_errors.append(f"Incorrect assumption about user preferences: '{assumption}'")

    print(f"Test 1 - Response: {response}")
    print(f"Assumption errors: {assumption_errors}")
    print(f"Should be flagged: {len(assumption_errors) > 0}")

    # Test response that should NOT be flagged (self-referential)
    response2 = "As your favorite AI, I'm here to help!"
    response_lower2 = response2.lower()

    assumption_errors2 = []

    for assumption in preference_assumptions:
        if assumption in response_lower2 and not any(word in response_lower2 for word in ["i don't know", "i'm not sure", "you haven't told me", "i recall", "as i remember"]):
            # Only flag if it's a definitive statement without qualifiers
            if not any(qualifier in response_lower2 for qualifier in ["maybe", "perhaps", "could be", "might be", "i'm guessing"]):
                # Exclude self-referential statements (e.g., "your favorite AI" when referring to itself)
                if not any(self_ref in response_lower2 for self_ref in ["your favorite ai", "your favorite assistant", "your favorite ignis", "as your favorite"]):
                    assumption_errors2.append(f"Incorrect assumption about user preferences: '{assumption}'")

    print(f"\nTest 2 - Response: {response2}")
    print(f"Assumption errors: {assumption_errors2}")
    print(f"Should be flagged: {len(assumption_errors2) > 0}")

    # Test the actual response we're getting
    response3 = "I'm sorry, but I don't actually know your personal preferences. I shouldn't make assumptions about things you haven't told me. Could you share that information with me?"
    response_lower3 = response3.lower()

    assumption_errors3 = []

    for assumption in preference_assumptions:
        if assumption in response_lower3 and not any(word in response_lower3 for word in ["i don't know", "i'm not sure", "you haven't told me", "i recall", "as i remember"]):
            # Only flag if it's a definitive statement without qualifiers
            if not any(qualifier in response_lower3 for qualifier in ["maybe", "perhaps", "could be", "might be", "i'm guessing"]):
                # Exclude self-referential statements (e.g., "your favorite AI" when referring to itself)
                if not any(self_ref in response_lower3 for self_ref in ["your favorite ai", "your favorite assistant", "your favorite ignis", "as your favorite"]):
                    assumption_errors3.append(f"Incorrect assumption about user preferences: '{assumption}'")

    print(f"\nTest 3 - Response: {response3[:50]}...")
    print(f"Assumption errors: {assumption_errors3}")
    print(f"Should be flagged: {len(assumption_errors3) > 0}")

if __name__ == "__main__":
    test_assumption_detection()