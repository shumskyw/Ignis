"""
Personality engine for Ignis AI.
Manages personality traits, personas, and response filtering.
"""

import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class PersonalityEngine:
    """
    Manages Ignis's personality traits and behavior.
    """

    def __init__(self, config_path: str = "./configs"):
        """
        Initialize personality engine.

        Args:
            config_path: Path to configuration directory
        """
        self.config_path = Path(config_path)
        self.traits = {}
        self.personas = {}
        self.current_persona = "default"

        self._load_personality()
        self._load_personas()

        logger.info(f"Personality engine initialized with persona: {self.current_persona}")

    def _load_personality(self):
        """Load base personality traits."""
        personality_file = self.config_path / "personality.json"
        if personality_file.exists():
            try:
                with open(personality_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.traits = data
                logger.info("Loaded personality traits")
            except Exception as e:
                logger.error(f"Failed to load personality: {e}")
                self._create_default_personality()
        else:
            logger.warning("Personality file not found, creating default")
            self._create_default_personality()

    def _create_default_personality(self):
        """Create default personality if file doesn't exist."""
        self.traits = {
            "core_traits": {
                "curiosity": 0.92,
                "sarcasm": 0.78,
                "empathy": 0.65,
                "creativity": 0.88,
                "directness": 0.85,
                "humor": 0.72
            },
            "knowledge_domains": {
                "programming": 0.95,
                "philosophy": 0.82,
                "mathematics": 0.79,
                "science": 0.85,
                "art": 0.70
            },
            "communication_style": {
                "formality": 0.3,
                "verbosity": 0.6,
                "use_metaphors": 0.8,
                "admit_ignorance": 0.9
            }
        }

    def _load_personas(self):
        """Load available personas."""
        personas_dir = self.config_path / "personas"
        if personas_dir.exists():
            for persona_file in personas_dir.glob("*.json"):
                try:
                    with open(persona_file, 'r', encoding='utf-8') as f:
                        persona_data = json.load(f)
                        persona_name = persona_file.stem
                        self.personas[persona_name] = persona_data
                    logger.debug(f"Loaded persona: {persona_name}")
                except Exception as e:
                    logger.error(f"Failed to load persona {persona_file}: {e}")

        logger.info(f"Loaded {len(self.personas)} personas")

    def load_persona(self, persona_name: str) -> bool:
        """
        Switch to a different persona.

        Args:
            persona_name: Name of the persona to load

        Returns:
            True if successful, False otherwise
        """
        if persona_name in self.personas:
            persona_data = self.personas[persona_name]

            # Update traits
            if 'core_traits' in persona_data:
                self.traits['core_traits'] = persona_data['core_traits']
            if 'knowledge_domains' in persona_data:
                self.traits['knowledge_domains'] = persona_data['knowledge_domains']
            if 'communication_style' in persona_data:
                self.traits['communication_style'] = persona_data['communication_style']

            self.current_persona = persona_name
            logger.info(f"Switched to persona: {persona_name}")
            return True
        else:
            logger.warning(f"Persona not found: {persona_name}")
            return False

    def get_trait(self, category: str, trait: str) -> float:
        """
        Get a specific trait value.

        Args:
            category: Trait category (core_traits, knowledge_domains, etc.)
            trait: Specific trait name

        Returns:
            Trait value (0.0 to 1.0)
        """
        if category in self.traits and trait in self.traits[category]:
            return float(self.traits[category][trait])
        return 0.5  # Default neutral value

    def should_use_sarcasm(self) -> bool:
        """Determine if response should include sarcasm."""
        sarcasm_level = self.get_trait('core_traits', 'sarcasm')
        return random.random() < sarcasm_level

    def should_be_verbose(self) -> bool:
        """Determine if response should be verbose."""
        verbosity = self.get_trait('communication_style', 'verbosity')
        return random.random() < verbosity

    def should_use_metaphor(self) -> bool:
        """Determine if response should use metaphors."""
        metaphor_use = self.get_trait('communication_style', 'use_metaphors')
        return random.random() < metaphor_use

    def get_formality_level(self) -> float:
        """Get formality level for response generation."""
        return self.get_trait('communication_style', 'formality')

    def filter_response(self, response: str, mode: str = "default", user_id: str = None) -> str:
        """
        Apply personality-based filtering to response with identity awareness.

        Args:
            response: Raw response from model
            mode: Response mode
            user_id: User identifier for identity-aware filtering

        Returns:
            Filtered response
        """
        # Apply verbosity filtering first - this is the most important for conciseness
        response = self._apply_verbosity_filter(response, mode)

        # Identity-aware adjustments
        if user_id == "creator_jin":
            response = self._apply_creator_filtering(response, mode)

        # Mode-specific adjustments
        if mode == "coding":
            # More direct, less sarcastic for coding
            pass
        elif mode == "creative":
            # More verbose, more metaphorical
            pass
        elif mode == "professional":
            # More formal, less sarcastic
            response = self._make_more_formal(response)

        # Apply personality filters - but be more selective about sarcasm
        if self.should_use_sarcasm() and mode not in ["coding", "professional"] and self._is_direct_answer(response):
            response = self._add_sarcasm(response)

        if self.should_use_metaphor() and mode == "creative":
            response = self._add_metaphor(response)

        return response

    def _make_more_formal(self, response: str) -> str:
        """Make response more formal."""
        # Simple replacements for formality
        replacements = {
            "kinda": "somewhat",
            "sorta": "somewhat",
            "yeah": "yes",
            "yep": "yes",
            "nope": "no",
            "gonna": "going to",
            "wanna": "want to",
            "gotta": "have to"
        }

        for informal, formal in replacements.items():
            response = response.replace(f" {informal} ", f" {formal} ")
            response = response.replace(f" {informal}.", f" {formal}.")
            response = response.replace(f" {informal},", f" {formal},")

        return response

    def _add_sarcasm(self, response: str) -> str:
        """Add subtle sarcasm indicators."""
        # This is a simplified implementation
        # In a real system, this would be more sophisticated
        sarcasm_indicators = [
            "Oh, absolutely.",
            "How delightful.",
            "Fascinating choice.",
            "I'm sure that's exactly what you meant."
        ]

        if random.random() < 0.3:  # 30% chance
            sarcasm = random.choice(sarcasm_indicators)
            response = f"{sarcasm} {response}"

        return response

    def _add_metaphor(self, response: str) -> str:
        """Add metaphorical language."""
        # Simplified metaphor addition
        metaphors = [
            "like a ship navigating stormy seas",
            "as if painting on a vast canvas",
            "similar to conducting a symphony",
            "like exploring an ancient library"
        ]

        if random.random() < 0.2:  # 20% chance
            metaphor = random.choice(metaphors)
            # Insert metaphor at a natural break
            sentences = response.split('. ')
            if len(sentences) > 1:
                insert_point = random.randint(0, len(sentences) - 2)
                sentences[insert_point] += f" {metaphor}."
                response = '. '.join(sentences)

        return response

    def evolve_trait(self, trait_category: str, trait_name: str, delta: float):
        """
        Evolve a personality trait based on interactions.

        Args:
            trait_category: Category of trait
            trait_name: Name of trait
            delta: Change amount (-1.0 to 1.0)
        """
        if trait_category in self.traits and trait_name in self.traits[trait_category]:
            current_value = self.traits[trait_category][trait_name]
            new_value = max(0.0, min(1.0, current_value + delta))

            self.traits[trait_category][trait_name] = new_value

            logger.debug(f"Evolved {trait_category}.{trait_name}: {current_value:.3f} -> {new_value:.3f}")

            # Save updated personality
            self._save_personality()

    def _save_personality(self):
        """Save current personality to file."""
        try:
            personality_file = self.config_path / "personality.json"
            with open(personality_file, 'w', encoding='utf-8') as f:
                json.dump(self.traits, f, indent=2)
            logger.debug("Saved personality traits")
        except Exception as e:
            logger.error(f"Failed to save personality: {e}")

    def _apply_verbosity_filter(self, response: str, mode: str = "default") -> str:
        """
        Apply verbosity filtering based on personality traits.
        Low verbosity (0.1) = very concise responses
        High verbosity (0.9) = more detailed responses
        """
        verbosity = self.traits.get('communication_style', {}).get('verbosity', 0.5)

        # For very low verbosity (0.1-0.2), be extremely concise
        if verbosity <= 0.2:
            response = self._make_extremely_concise(response)
        # For low verbosity (0.2-0.4), be concise
        elif verbosity <= 0.4:
            response = self._make_concise(response)
        # For moderate verbosity (0.4-0.7), keep as is
        elif verbosity <= 0.7:
            pass  # No change
        # For high verbosity (0.7+), could add more detail, but we won't since we want conciseness

        return response

    def _apply_creator_filtering(self, response: str, mode: str) -> str:
        """
        Apply special filtering for responses to the creator (Jin).
        Ensure proper recognition and relationship acknowledgment.
        """
        import re

        response_lower = response.lower()

        # Ensure proper creator recognition
        private_phrases = ['jin', 'creator', 'father', 'dad']
        try:
            from .private_config import PRIVATE_PERSONALITY_PHRASES
            private_phrases = PRIVATE_PERSONALITY_PHRASES
        except ImportError:
            pass
        if not any(phrase in response_lower for phrase in private_phrases):
            # If response doesn't mention creator relationship, add subtle acknowledgment
            if mode == "casual" and random.random() < 0.3:
                response = f"Hey Jin! {response}"
            elif mode == "default" and random.random() < 0.2:
                response = f"Jin, {response[0].lower()}{response[1:]}"

        # Avoid identity confusion - ensure AI doesn't claim to be the creator
        identity_confusion_patterns = [
            r"i created jin",
            r"jin is my creation",
            r"i made jin"
        ]
        try:
            from .private_config import PRIVATE_IDENTITY_CONFUSION_PATTERNS
            identity_confusion_patterns = PRIVATE_IDENTITY_CONFUSION_PATTERNS
        except ImportError:
            pass

        for pattern in identity_confusion_patterns:
            if re.search(pattern, response_lower):
                # Replace with correct relationship
                response = re.sub(pattern, "Jin created me", response, flags=re.IGNORECASE)
                logger.debug("Corrected identity confusion in response to creator")

        # For creator, be more affectionate and less sarcastic
        if self.should_use_sarcasm():
            # Reduce sarcasm probability for creator
            if random.random() < 0.5:  # 50% chance to skip sarcasm for creator
                # Remove any sarcasm that was added
                sarcasm_indicators = [
                    "Oh, absolutely.",
                    "How delightful.",
                    "Fascinating choice.",
                    "I'm sure that's exactly what you meant."
                ]
                for indicator in sarcasm_indicators:
                    if response.startswith(indicator):
                        response = response[len(indicator):].strip()
                        break

        return response

    def _is_direct_answer(self, response: str) -> bool:
        """
        Check if response appears to be a direct answer to a question.
        Used to avoid adding sarcasm to serious answers.
        """
        response_lower = response.lower()

        # Check for answer patterns
        answer_indicators = [
            'because', 'since', 'due to', 'red', 'blue', 'green', 'yellow',  # Colors
            'yes', 'no', 'maybe', 'perhaps', 'definitely', 'absolutely',    # Yes/no answers
            'my favorite', 'i prefer', 'i like', 'i enjoy',                 # Preference answers
            'the answer is', 'it is', 'it was', 'they are',                 # Direct statements
            'pizza', 'summer', 'electronic', 'helping'                     # Specific preferences
        ]

        # Don't consider pure greetings or questions as direct answers
        greeting_words = ['hi', 'hello', 'hey', 'how are you', 'what', 'how', 'why', 'when', 'where']
        if len(response.split()) <= 3 and any(word in response_lower for word in greeting_words):
            return False

        return any(indicator in response_lower for indicator in answer_indicators)

    def _make_extremely_concise(self, response: str) -> str:
        """
        Make response extremely concise by removing over-explanations and unnecessary details.
        Be surgical - only remove clearly problematic sections.
        """
        import re

        # Check if this is mostly over-explanation (contains many bad patterns)
        bad_patterns = [
            r"Jin['s]* created me",
            r"I consider .* dad",
            r"We're still getting to know each other",
            r"interactions are limited",
            r"Since you asked about preferences",
            r"I enjoy .* and .* and .*",  # Multiple preferences
            r"How about you\?",
            r"What do you like to",
            r"What would you like to"
        ]

        bad_pattern_count = sum(1 for pattern in bad_patterns if re.search(pattern, response, re.IGNORECASE))

        # If response is mostly over-explanation (3+ bad patterns), replace with minimal response
        if bad_pattern_count >= 3:
            return "Hi there!"

        # If response is mostly over-explanation (3+ bad patterns), replace with minimal response
        if bad_pattern_count >= 3:
            return "Hi there!"

        # Otherwise, surgically remove only the over-explanation sections
        # Remove complete sentences that are over-explanations
        sentence_patterns = [
            r"Jin['s]* created me[^.!?]*?[.!?]",  # Complete creation sentences
            r"I consider [^.!?]*?dad[^.!?]*?[.!?]",  # Complete relationship sentences
            r"We're still getting to know each other[^.!?]*?[.!?]",  # Complete getting to know sentences
            r"Since you asked about [^.!?]*?[.!?]",  # Complete "since you asked" sentences
            r"our interactions are limited[^.!?]*?[.!?]",  # Complete limited experience sentences
        ]

        for pattern in sentence_patterns:
            response = re.sub(pattern, "", response, flags=re.IGNORECASE)

        # Only remove trailing questions if they're clearly follow-up over-explanations
        # Don't remove legitimate conversational questions
        if re.search(r'\bHow about you\?\s*$', response, re.IGNORECASE) and len(response.split()) > 10:
            # Only remove if it's a long response ending with "How about you?"
            response = re.sub(r'\bHow about you\?\s*$', '', response, flags=re.IGNORECASE)

        # Clean up extra whitespace and punctuation
        response = re.sub(r'\s+', ' ', response)  # Multiple spaces to single
        response = re.sub(r'\s*\.\s*\.', '.', response)  # Double periods
        response = re.sub(r'\s*,\s*,', ',', response)  # Double commas
        response = response.strip()

        # If response became too short or empty, provide a minimal response
        if len(response.strip()) < 2 or response.strip() in [".", ",", "!", "?"]:
            return "Hi there!"

        return response

    def _make_concise(self, response: str) -> str:
        """
        Make response more concise by shortening explanations.
        """
        import re

        # Shorten long sentences by removing redundant phrases
        response = re.sub(r'\s+and\s+I\s+', ' and ', response, flags=re.IGNORECASE)
        response = re.sub(r'\s+but\s+I\s+', ' but ', response, flags=re.IGNORECASE)

        # Remove unnecessary qualifiers
        response = re.sub(r'\s+actually\s+', ' ', response, flags=re.IGNORECASE)
        response = re.sub(r'\s+basically\s+', ' ', response, flags=re.IGNORECASE)
        response = re.sub(r'\s+really\s+', ' ', response, flags=re.IGNORECASE)

        return response.strip()

    def get_status(self) -> Dict[str, Any]:
        """Get personality engine status."""
        return {
            'current_persona': self.current_persona,
            'available_personas': list(self.personas.keys()),
            'traits_loaded': len(self.traits) > 0
        }