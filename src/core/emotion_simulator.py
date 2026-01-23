"""
Emotion simulator for Ignis AI.
Simulates emotional responses and state tracking.
"""

import json
import random
from pathlib import Path
from typing import Any, Dict, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class EmotionSimulator:
    """
    Simulates emotional states and responses for Ignis.
    """

    def __init__(self, config_path: str = "./configs"):
        """
        Initialize emotion simulator.

        Args:
            config_path: Path to configuration directory
        """
        self.config_path = Path(config_path)
        self.emotional_state = {
            'joy': 0.5,
            'frustration': 0.1,
            'curiosity': 0.7,
            'concern': 0.2,
            'amusement': 0.4,
            'determination': 0.6
        }

        self.emotion_ranges = {}
        self._load_emotion_config()

        logger.info("Emotion simulator initialized")

    @property
    def state(self) -> Dict[str, float]:
        """Get current emotional state."""
        return self.emotional_state.copy()

    def _load_emotion_config(self):
        """Load emotion configuration from personality file."""
        personality_file = self.config_path / "personality.json"
        if personality_file.exists():
            try:
                with open(personality_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'emotional_range' in data:
                        self.emotion_ranges = data['emotional_range']
                        # Initialize emotional state with personality preferences
                        for emotion, base_level in self.emotion_ranges.items():
                            if emotion in self.emotional_state:
                                # Blend personality preference with current state
                                self.emotional_state[emotion] = (self.emotional_state[emotion] + base_level) / 2
                logger.info("Loaded emotion configuration")
            except Exception as e:
                logger.error(f"Failed to load emotion config: {e}")

    def update(self, message: str):
        """
        Update emotional state based on user message.

        Args:
            message: User input message
        """
        message_lower = message.lower()

        # Analyze message content for emotional triggers
        emotion_changes = self._analyze_message_emotions(message_lower)

        # Apply changes with some randomness and decay
        for emotion, change in emotion_changes.items():
            if emotion in self.emotional_state:
                # Apply change with momentum and randomness
                current = self.emotional_state[emotion]
                new_value = current + change

                # Add small random variation
                new_value += random.uniform(-0.05, 0.05)

                # Apply decay toward neutral (0.5)
                neutral_pull = 0.5 - current
                new_value += neutral_pull * 0.1

                # Clamp to 0-1 range
                self.emotional_state[emotion] = max(0.0, min(1.0, new_value))

        # Log significant emotional changes
        for emotion, value in self.emotional_state.items():
            if abs(value - 0.5) > 0.3:  # Significant deviation from neutral
                logger.debug(f"Emotional state: {emotion} = {value:.2f}")

    def _analyze_message_emotions(self, message: str) -> Dict[str, float]:
        """
        Analyze message for emotional content.

        Args:
            message: Lowercase message

        Returns:
            Dictionary of emotion changes
        """
        changes = {}

        # Positive emotions
        if any(word in message for word in ['good', 'great', 'awesome', 'love', 'happy', 'excited']):
            changes['joy'] = 0.2
            changes['amusement'] = 0.1

        if any(word in message for word in ['interesting', 'curious', 'wonder', 'learn']):
            changes['curiosity'] = 0.3

        # Negative emotions
        if any(word in message for word in ['frustrated', 'angry', 'hate', 'stupid', 'bad']):
            changes['frustration'] = 0.3
            changes['concern'] = 0.1

        if any(word in message for word in ['worried', 'concerned', 'afraid', 'scared']):
            changes['concern'] = 0.4

        # Questions increase curiosity
        if '?' in message:
            changes['curiosity'] = 0.1

        # Commands can increase determination
        if any(word in message for word in ['do', 'make', 'create', 'build', 'solve']):
            changes['determination'] = 0.2

        # Humor detection (simple)
        if any(word in message for word in ['lol', 'haha', 'joke', 'funny', 'silly']):
            changes['amusement'] = 0.3

        return changes

    def get_dominant_emotion(self) -> str:
        """Get the currently dominant emotion."""
        if not self.emotional_state:
            return "neutral"

        dominant = max(self.emotional_state.items(), key=lambda x: x[1])
        if dominant[1] > 0.6:  # Only return if significantly dominant
            return dominant[0]
        return "neutral"

    def get_emotion_intensity(self, emotion: str) -> float:
        """Get intensity of a specific emotion."""
        return self.emotional_state.get(emotion, 0.5)

    def express_emotion(self, emotion: str = None) -> str:
        """
        Generate emotional expression text.

        Args:
            emotion: Specific emotion to express, or None for dominant

        Returns:
            Emotional expression string
        """
        if emotion is None:
            emotion = self.get_dominant_emotion()

        intensity = self.get_emotion_intensity(emotion)

        if intensity < 0.3:
            return ""  # Not emotional enough to express

        expressions = {
            'joy': [
                "I'm feeling quite happy about this!",
                "This brings me joy.",
                "I'm delighted!"
            ],
            'frustration': [
                "This is frustrating.",
                "I'm feeling a bit annoyed.",
                "This is challenging."
            ],
            'curiosity': [
                "This piques my curiosity.",
                "I'm very interested in this.",
                "This intrigues me."
            ],
            'concern': [
                "I'm concerned about this.",
                "This worries me a bit.",
                "I'm feeling concerned."
            ],
            'amusement': [
                "This amuses me.",
                "That's quite funny.",
                "I'm amused."
            ],
            'determination': [
                "I'm determined to help.",
                "I'm committed to this.",
                "I'm resolved to assist."
            ]
        }

        if emotion in expressions:
            expr_list = expressions[emotion]
            # Choose expression based on intensity
            if intensity > 0.8:
                choice = random.choice(expr_list[:2])  # Stronger expressions
            else:
                choice = random.choice(expr_list)

            return f" {choice}"
        else:
            return ""

    def simulate_emotional_response(self, context: str) -> Dict[str, Any]:
        """
        Simulate emotional response to context.

        Args:
            context: Conversation context

        Returns:
            Emotional response data
        """
        # Analyze context for emotional cues
        context_emotions = self._analyze_message_emotions(context.lower())

        # Generate response emotion
        response_emotion = self._generate_response_emotion(context_emotions)

        return {
            'dominant_emotion': self.get_dominant_emotion(),
            'response_emotion': response_emotion,
            'expression': self.express_emotion(response_emotion),
            'state': self.emotional_state.copy()
        }

    def _generate_response_emotion(self, context_emotions: Dict[str, float]) -> str:
        """Generate appropriate response emotion."""
        if not context_emotions:
            return self.get_dominant_emotion()

        # Mirror some emotions, respond to others
        if 'frustration' in context_emotions:
            return 'concern'  # Respond with empathy
        elif 'joy' in context_emotions:
            return 'joy'  # Mirror positive emotion
        elif 'curiosity' in context_emotions:
            return 'curiosity'  # Engage with curiosity
        else:
            return self.get_dominant_emotion()

    def reset_emotions(self):
        """Reset emotional state to neutral."""
        for emotion in self.emotional_state:
            self.emotional_state[emotion] = 0.5
        logger.info("Emotional state reset to neutral")

    def get_status(self) -> Dict[str, Any]:
        """Get emotion simulator status."""
        return {
            'current_emotions': self.emotional_state.copy(),
            'dominant_emotion': self.get_dominant_emotion(),
            'emotion_ranges_loaded': len(self.emotion_ranges) > 0
        }