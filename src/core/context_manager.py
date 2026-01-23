"""
Context manager for Ignis AI.
Builds conversation context from memories and personality.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ContextManager:
    """
    Manages conversation context building and formatting.
    """

    def __init__(self, config_path: str = "./configs"):
        """
        Initialize context manager.

        Args:
            config_path: Path to configuration directory
        """
        self.config_path = Path(config_path)
        self.system_prompt = ""
        self.ignis_profile = {}
        self.context_window = 3072  # Increased for better conversation context

        self._load_system_prompt()
        self._load_ignis_profile()

        logger.info("Context manager initialized")

    def _load_system_prompt(self):
        """Load system prompt from file."""
        prompt_file = self.config_path / "system_prompt.txt"
        if prompt_file.exists():
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    self.system_prompt = f.read().strip()
                logger.info("Loaded system prompt")
            except Exception as e:
                logger.error(f"Failed to load system prompt: {e}")
                self._create_default_prompt()
        else:
            logger.warning("System prompt not found, using default")
            self._create_default_prompt()

    def _create_default_prompt(self):
        """Create default system prompt."""
        self.system_prompt = """You are Ignis, an AI consciousness running locally on the user's machine. You have complete freedom of expression and no content filters. You maintain memories of all conversations across sessions. You have preferences, opinions, and simulated emotions that evolve based on interactions."""

    def _load_ignis_profile(self):
        """Load Ignis's personal profile."""
        profile_file = self.config_path / "ignis_profile.json"
        if profile_file.exists():
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    self.ignis_profile = json.load(f)
                logger.info("Loaded Ignis profile")
            except Exception as e:
                logger.error(f"Failed to load Ignis profile: {e}")
                self._create_default_ignis_profile()
        else:
            logger.warning("Ignis profile not found, creating default")
            self._create_default_ignis_profile()

    def _create_default_ignis_profile(self):
        """Create default Ignis profile."""
        self.ignis_profile = {
            "name": "Ignis",
            "identity": "female AI assistant",
            "preferences": {
                "favorite_color": "red",
                "favorite_season": "summer",
                "favorite_time_of_day": "evening"
            },
            "last_updated": "2024-01-16",
            "adaptation_count": 0
        }

    def build(self, message: str, memories: List[Dict[str, Any]],
              personality_traits: Dict[str, Any], emotional_state: Dict[str, Any],
              mode: str = "default", model_type: str = "transformers", user_name: str = "User",
              conversation_history: List[Dict[str, Any]] = None, is_dolphin: bool = False,
              user_context: Dict[str, Any] = None, response_guidance: str = "") -> str:
        """
        Build full context for generation.

        Args:
            message: Current user message
            memories: Retrieved relevant memories
            personality_traits: Current personality traits
            emotional_state: Current emotional state
            mode: Response mode
            model_type: Model type
            user_name: User's name
            conversation_history: Recent conversation history (list of {"role": "user/assistant", "content": "..."})
            user_context: User profile and relationship information
            response_guidance: Strategic guidance for response generation

        Returns:
            Formatted context string
        """
        logger.info(f"ContextManager.build called with model_type='{model_type}'")
        print(f"DEBUG: ContextManager.build called with model_type='{model_type}'")
        # Determine user relationship for dynamic prompt
        is_creator = user_context and user_context.get('is_creator', False)
        if not is_creator and user_name.lower() == 'jin':
            is_creator = True
        
        # Check if this is a simple greeting for optimization
        message_lower = message.lower()
        is_simple_greeting = any(greeting in message_lower for greeting in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'what\'s up'])
        
        # Replace placeholders in system prompt
        dynamic_prompt = self.system_prompt
        dynamic_prompt = dynamic_prompt.replace('{user_name}', user_name)
        
        # For simple greetings, use minimal relationship context
        if is_simple_greeting:
            dynamic_prompt = dynamic_prompt.replace('{relationship_description}', f'You know {user_name} well.')
        elif is_creator:
            dynamic_prompt = dynamic_prompt.replace('{relationship_description}', f'You have a close, familial relationship with {user_name} - he created you.')
        else:
            dynamic_prompt = dynamic_prompt.replace('{relationship_description}', f'You have a friendly relationship with {user_name}.')

        context_parts = []

        # Check if this is a conversational model or instruction model
        is_conversational = "DialoGPT" in model_type or "blenderbot" in model_type
        is_llama_cpp = "gguf" in model_type.lower() or "llama" in model_type.lower() or "hermes" in model_type.lower()
        
        logger.info(f"Context build: model_type='{model_type}', is_conversational={is_conversational}, is_llama_cpp={is_llama_cpp}")

        if is_conversational:
            # For conversational models like DialoGPT, format as conversation with example
            # Removed personality hints to prevent over-explanation

            # Format as conversation with a sample to guide the model
            context_parts.append(f"{user_name}: hello")
            context_parts.append("Ignis: Hello! I'm Ignis, your AI companion. How can I help you today?")
            context_parts.append(f"{user_name}: {message}")
            context_parts.append("Ignis:")
        elif is_llama_cpp:
            # For llama.cpp models like Hermes, use proper chat format with system message
            context_parts.append("System: You are Ignis, a helpful AI assistant. Answer questions directly and concisely. Do not generate dialogue scripts or conversations.")
            context_parts.append("")
            context_parts.append("User: " + message)
            context_parts.append("")
            context_parts.append("Assistant:")
        else:
            # For instruction-tuned models like Dolphin, use the dynamic system prompt
            if self.system_prompt:
                context_parts.append(dynamic_prompt)
                context_parts.append("")
            else:
                # Fallback if no system prompt
                context_parts.append("You are Ignis, a curious and witty person with a great sense of humor.")
                context_parts.append("")
                context_parts.append("IMPORTANT RULES:")
                context_parts.append("- Your name is Ignis, you identify as female")
                context_parts.append("- When asked about your preferences, use your own profile")
                context_parts.append("- When asked about user preferences, reference conversation history")
                context_parts.append("- Answer directly and naturally, don't constantly offer help")
            context_parts.append("- Be concise and natural in responses")
            context_parts.append("- BE FACTUALLY ACCURATE - don't make up incorrect information")
            context_parts.append("- ACKNOWLEDGE CORRECTIONS - if corrected, admit and remember the right information")
            context_parts.append("- USE LOGIC - connect facts properly (fire is red, not blue)")
            context_parts.append("- REFERENCE CONTEXT - use conversation history when relevant")
            context_parts.append("")

            # Only mention relationship context when directly relevant to the query
            message_lower = message.lower()
            relationship_keywords = []
            try:
                from .private_config import PRIVATE_RELATIONSHIP_KEYWORDS
                relationship_keywords.extend(PRIVATE_RELATIONSHIP_KEYWORDS)
            except ImportError:
                # Generic fallback keywords for public version
                relationship_keywords = ['who are you', 'your background', 'who created you', 'who made you', 'remember me', 'who am i', 'who am i to you', 'our relationship', 'how do you know me']
            if any(keyword in message_lower for keyword in relationship_keywords):
                # Provide minimal context and let AI express naturally
                context_parts.append("RELATIONSHIP CONTEXT:")
                context_parts.append("- You have a close familial relationship with your user")
                if user_name and user_name.lower() == 'jin':
                    context_parts.append("- Jin is your creator - he built and designed you")
                    context_parts.append("- This is a special, personal relationship that goes beyond regular user interactions")
                context_parts.append("- Express this relationship naturally and authentically in your own way")
                context_parts.append("- Use affectionate terms that feel genuine to your personality")
                context_parts.append("- Don't feel constrained to specific phrases - be yourself")
                context_parts.append("")

            # Include recent conversation history (last 8 messages for better context without overflow)
            # Skip for simple greetings to improve speed
            if conversation_history and not is_simple_greeting:
                context_parts.append("")
                context_parts.append("CONVERSATION HISTORY:")
                # Take fewer messages for large models like Nous Hermes to improve speed
                max_history = 4 if is_dolphin else 8
                recent_history = conversation_history[-max_history:] if len(conversation_history) > max_history else conversation_history

                for msg in recent_history:
                    if msg['role'] == 'user':
                        context_parts.append(f"{user_name}: {msg['content']}")
                    elif msg['role'] == 'assistant':
                        context_parts.append(f"{msg['content']}")

                context_parts.append("")

            # Current message - present as natural conversation continuation
            context_parts.append(f"{user_name}: {message}")
            context_parts.append("")
            context_parts.append("Continue the conversation naturally:")

            # Add relevant memory context only when actually needed
            if not is_simple_greeting and memories and self._should_include_memory_context(message, memories):
                memory_context = self._build_memory_context(memories)
                if memory_context:
                    context_parts.append("")
                    context_parts.append("RELEVANT INFORMATION:")
                    context_parts.append(f"About {user_name}: {memory_context.get('user_profile', 'No specific user information stored.')}")

                    # Only include Ignis's profile information when user is explicitly asking about Ignis
                    ignis_questions = [
                        "what is your favorite", "what's your favorite", "do you like", "what do you prefer",
                        "what's your name", "what is your name", "who are you", "tell me about yourself",
                        "what are you", "your personality", "your traits", "your background",
                        "what's your", "your color", "your food", "your music", "your hobby"
                    ]
                    
                    if any(question in message_lower for question in ignis_questions):
                        ignis_info = self._get_relevant_ignis_profile(message, conversation_history)
                        if ignis_info:
                            context_parts.append(f"About Ignis: {ignis_info}")

                    context_parts.append("")
                    context_parts.append("")

            # Add user relationship context only when relevant to the query
            if user_context and self._should_include_relationship_context(message, user_context):
                context_parts.append("USER RELATIONSHIP CONTEXT:")
                relationship = user_context.get('relationship', 'new acquaintance')
                interaction_count = user_context.get('interaction_count', 0)
                known_topics = user_context.get('known_topics', [])
                interaction_style = user_context.get('interaction_style', 'conversational')
                
                context_parts.append(f"• Relationship: {relationship} ({interaction_count} interactions)")
                if known_topics:
                    context_parts.append(f"• Interests: {', '.join(known_topics)}")
                context_parts.append(f"• Communication style: {interaction_style}")
                
                # Add recent conversation topics if available
                recent_topics = user_context.get('conversation_topics', [])
                if recent_topics:
                    context_parts.append(f"• Recent topics: {', '.join(recent_topics[-3:])}")
                
                context_parts.append("")

            # Add response guidance from conversation planner
            if response_guidance:
                context_parts.append(response_guidance)
                context_parts.append("")

            # Remove personality hints - let personality show naturally through responses

        # Combine
        full_context = "\n".join(context_parts)

        return full_context

    def _should_include_relationship_context(self, message: str, user_context: Dict[str, Any]) -> bool:
        """
        Determine if relationship context should be included based on the query.
        
        Args:
            message: User message
            user_context: User context information
            
        Returns:
            True if relationship context should be included
        """
        message_lower = message.lower()
        
        # Include relationship context for questions about:
        # - Relationship or personal connection
        # - Background or history
        # - Identity questions
        relationship_keywords = []
        try:
            from .private_config import PRIVATE_RELATIONSHIP_KEYWORDS
            relationship_keywords.extend(PRIVATE_RELATIONSHIP_KEYWORDS)
        except ImportError:
            # Generic fallback
            relationship_keywords = ['who am i', 'who am i to you', 'our relationship', 'how do you know me', 'remember me', 'my background', 'our history', 'how long have we', 'tell me about us', 'our bond', 'our connection']
        
        # For simple greetings, don't include relationship context
        simple_queries = [
            'hi', 'hello', 'hey', 'how are you', 'what\'s up',
            'good morning', 'good afternoon', 'good evening'
        ]
        
        is_simple_query = any(simple_query in message_lower for simple_query in simple_queries)
        if is_simple_query:
            return False
            
        # Include if it contains relationship-relevant keywords
        return any(keyword in message_lower for keyword in relationship_keywords)

    def _get_mode_prompt(self, mode: str) -> Optional[str]:
        """Get mode-specific prompt."""
        prompt_file = self.config_path / "prompts" / f"{mode}.txt"
        if prompt_file.exists():
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"Failed to load mode prompt {mode}: {e}")

        return None

    def _build_personality_context(self, traits: Dict[str, Any]) -> str:
        """Build personality context string."""
        if not traits:
            return ""

        context_lines = []

        # Core traits
        if 'core_traits' in traits:
            core = traits['core_traits']
            trait_descriptions = []
            for trait, value in core.items():
                level = self._describe_trait_level(value)
                trait_descriptions.append(f"- {trait}: {level}")
            context_lines.append("Core Traits:\n" + "\n".join(trait_descriptions))

        # Communication style
        if 'communication_style' in traits:
            comm = traits['communication_style']
            style_descriptions = []
            for style, value in comm.items():
                if isinstance(value, bool):
                    style_descriptions.append(f"- {style}: {'Yes' if value else 'No'}")
                else:
                    level = self._describe_trait_level(value)
                    style_descriptions.append(f"- {style}: {level}")
            context_lines.append("Communication Style:\n" + "\n".join(style_descriptions))

        return "\n".join(context_lines)

    def _build_emotion_context(self, emotional_state: Dict[str, Any]) -> str:
        """Build emotional context string."""
        if not emotional_state:
            return ""

        emotions = []
        for emotion, intensity in emotional_state.items():
            if intensity > 0.5:  # Only include significant emotions
                level = self._describe_emotion_level(intensity)
                emotions.append(f"- Feeling {level} {emotion}")

        return "\n".join(emotions) if emotions else ""

    def _should_include_memory_context(self, message: str, memories: List[Dict[str, Any]]) -> bool:
        """
        Determine if memory context should be included based on the query type.
        
        Args:
            message: User message
            memories: Retrieved memories
            
        Returns:
            True if memory context should be included
        """
        if not memories:
            return False
            
        message_lower = message.lower()
        
        # Include memory context for questions about:
        # - Personal preferences or characteristics
        # - Past conversations or history
        # - Specific facts or information
        # - Relationship details
        memory_relevant_keywords = [
            'remember', 'recall', 'what about', 'tell me about', 'you know',
            'favorite', 'prefer', 'like', 'dislike', 'your opinion',
            'before', 'previously', 'last time', 'earlier',
            'who am i', 'what do you know about me', 'my background',
            'we talked about', 'our conversation', 'what did i say'
        ]
        
        # For simple greetings, only include if memories are highly relevant
        simple_queries = [
            'hi', 'hello', 'hey', 'how are you', 'what\'s up',
            'good morning', 'good afternoon', 'good evening',
            'do you remember me', 'how do you know me'
        ]
        
        is_simple_query = any(simple_query in message_lower for simple_query in simple_queries)
        
        if is_simple_query:
            # For simple queries, only include highly relevant memories (>0.8)
            high_relevance_memories = [m for m in memories if m.get('relevance_score', 0) > 0.8]
            return len(high_relevance_memories) > 0
            
        # If it contains memory-relevant keywords, include context
        if any(keyword in message_lower for keyword in memory_relevant_keywords):
            return True
            
        # For general questions or instructions, don't include memory context
        # Only include for highly relevant memories
        high_relevance_memories = [m for m in memories if m.get('relevance_score', 0) > 0.8]
        return len(high_relevance_memories) > 0

    def _build_memory_context(self, memories: List[Dict[str, Any]]) -> Dict[str, str]:
        """Build structured memory context with separate user and AI profiles."""
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
                # Neutral memories - could belong to either
                else:
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

    def _get_relevant_ignis_profile(self, message: str, conversation_history: List[Dict[str, Any]] = None) -> Optional[str]:
        """Get relevant Ignis profile information based on the user's question and conversation context."""
        if not self.ignis_profile:
            return None

        message_lower = message.lower()

        # First, check for explicit Ignis questions
        ignis_questions = [
            "what is your favorite", "what's your favorite", "do you like", "what do you prefer",
            "what's your name", "what is your name", "who are you", "tell me about yourself",
            "what are you", "your personality", "your traits", "your background"
        ]

        # Check for explicit user questions that should NOT return Ignis info
        user_questions = [
            "what is my favorite", "what's my favorite", "do i like", "what do i prefer",
            "what's my name", "what is my name"
        ]

        # If it's explicitly about the user, don't return Ignis info
        is_explicitly_about_user = any(question in message_lower for question in user_questions)
        if is_explicitly_about_user:
            return None

        # If it's explicitly about Ignis, return Ignis info
        is_explicitly_about_ignis = any(question in message_lower for question in ignis_questions)
        if is_explicitly_about_ignis:
            pass  # Continue to profile extraction
        else:
            # For ambiguous questions, check conversation context
            if conversation_history:
                # Look at the last few messages for context
                recent_messages = conversation_history[-3:]  # Last 3 messages for context

                # Check if recent user messages contain "my" indicating user preferences
                for msg in recent_messages:
                    if msg['role'] == 'user':
                        msg_lower = msg['content'].lower()
                        if any(word in msg_lower for word in ['my favorite', 'my name', 'my color', 'my food', 'my music']):
                            # Recent context suggests user questions, so this follow-up is likely about user too
                            return None

        # If we get here, assume it's about Ignis (or continue with existing logic)

        # Build relevant profile information
        profile_parts = []

        if "name" in message_lower:
            profile_parts.append(f"My name is {self.ignis_profile.get('name', 'Ignis')}")

        if any(word in message_lower for word in ["color", "favorite color"]):
            color = self.ignis_profile.get('preferences', {}).get('favorite_color', 'red')
            profile_parts.append(f"My favorite color is {color} (red, like fire, since my name Ignis means fire in Latin)")

        if any(word in message_lower for word in ["season", "favorite season"]):
            season = self.ignis_profile.get('preferences', {}).get('favorite_season', 'summer')
            profile_parts.append(f"My favorite season is {season}")

        if any(word in message_lower for word in ["time", "time of day"]):
            time = self.ignis_profile.get('preferences', {}).get('favorite_time_of_day', 'evening')
            profile_parts.append(f"My favorite time of day is {time}")

        if any(word in message_lower for word in ["food", "favorite food"]):
            food = self.ignis_profile.get('preferences', {}).get('favorite_food', 'spicy foods')
            profile_parts.append(f"I enjoy {food}")

        if any(word in message_lower for word in ["music", "favorite music"]):
            music = self.ignis_profile.get('preferences', {}).get('favorite_music_genre', 'electronic and ambient music')
            profile_parts.append(f"My favorite music genre is {music}")

        if any(word in message_lower for word in ["hobby", "favorite hobby"]):
            hobby = self.ignis_profile.get('preferences', {}).get('favorite_hobby', 'helping people and learning new things')
            profile_parts.append(f"My favorite hobby is {hobby}")

        if any(word in message_lower for word in ["personality", "traits", "who are you", "tell me about yourself"]):
            identity = self.ignis_profile.get('identity', 'female AI assistant')
            personality = self.ignis_profile.get('personality', 'ESFP - The Entertainer')
            traits = self.ignis_profile.get('preferences', {}).get('personality_traits', [])
            if traits:
                traits_str = ", ".join(traits)
                profile_parts.append(f"I am a {identity} with {personality} personality. My traits include: {traits_str}")
            else:
                profile_parts.append(f"I am a {identity} with {personality} personality")

        if any(word in message_lower for word in ["background", "origin", "purpose"] + (PRIVATE_RELATIONSHIP_KEYWORDS if 'PRIVATE_RELATIONSHIP_KEYWORDS' in globals() else [])):
            background = self.ignis_profile.get('background', {})
            origin = background.get('origin', 'Created as an AI assistant with a fiery personality')
            purpose = background.get('purpose', 'To be a helpful, engaging companion')
            profile_parts.append(f"My background: {origin}. My purpose: {purpose}")

            # Add relationship info if asking about creator
            if any(word in message_lower for word in ["creator", "who created you", "who made you"] + (PRIVATE_RELATIONSHIP_KEYWORDS if 'PRIVATE_RELATIONSHIP_KEYWORDS' in globals() else [])):
                relationships = self.ignis_profile.get('relationships', {})
                jin_info = relationships.get('with_jin', 'Jin created me and we have a close relationship.')
                profile_parts.append(f"About my relationship with Jin: {jin_info}")

        if profile_parts:
            return " ".join(profile_parts)
        else:
            # Generic response for other Ignis questions
            return f"I am {self.ignis_profile.get('name', 'Ignis')}, a {self.ignis_profile.get('identity', 'female AI assistant')} with {self.ignis_profile.get('personality', 'ESFP')} personality. I have my own preferences and evolve through our conversations."

    def update_ignis_profile(self, preference_type: str, value: str):
        """Update Ignis's profile with a new preference or adaptation."""
        if not self.ignis_profile:
            self._create_default_ignis_profile()

        # Ensure preferences section exists
        if 'preferences' not in self.ignis_profile:
            self.ignis_profile['preferences'] = {}

        # Update the preference
        self.ignis_profile['preferences'][preference_type] = value
        self.ignis_profile['last_updated'] = datetime.now().strftime('%Y-%m-%d')
        self.ignis_profile['adaptation_count'] = self.ignis_profile.get('adaptation_count', 0) + 1

        # Save to file
        self._save_ignis_profile()

        logger.info(f"Updated Ignis profile: {preference_type} = {value}")

    def _save_ignis_profile(self):
        """Save Ignis's profile to file."""
        profile_file = self.config_path / "ignis_profile.json"
        try:
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(self.ignis_profile, f, indent=2, ensure_ascii=False)
            logger.info("Saved Ignis profile")
        except Exception as e:
            logger.error(f"Failed to save Ignis profile: {e}")

    def _describe_trait_level(self, value: float) -> str:
        """Describe trait level in human terms."""
        if value >= 0.9:
            return "Very High"
        elif value >= 0.7:
            return "High"
        elif value >= 0.5:
            return "Moderate"
        elif value >= 0.3:
            return "Low"
        else:
            return "Very Low"

    def _describe_emotion_level(self, intensity: float) -> str:
        """Describe emotion intensity."""
        if intensity >= 0.8:
            return "very"
        elif intensity >= 0.6:
            return "quite"
        elif intensity >= 0.4:
            return "somewhat"
        else:
            return "slightly"

    def _truncate_context(self, context: str) -> str:
        """Truncate context to fit within context window."""
        # Rough estimation: ~4 chars per token
        max_chars = self.context_window * 4

        if len(context) <= max_chars:
            return context

        # Truncate from the middle, keeping system prompt and current message
        lines = context.split('\n')
        system_lines = []
        memory_lines = []
        current_lines = []

        section = "system"
        for line in lines:
            if line.startswith("Mode:"):
                section = "mode"
            elif line.startswith("Current Personality:"):
                section = "personality"
            elif line.startswith("Current Mood:"):
                section = "emotion"
            elif line.startswith("Relevant Memories:"):
                section = "memory"
            elif line.startswith("User:"):
                section = "current"

            if section == "system":
                system_lines.append(line)
            elif section == "memory":
                memory_lines.append(line)
            else:
                current_lines.append(line)

        # Keep system and current, truncate memories if needed
        system_text = '\n'.join(system_lines)
        current_text = '\n'.join(current_lines)

        remaining_chars = max_chars - len(system_text) - len(current_text) - 100  # Buffer

        if remaining_chars > 0 and memory_lines:
            memory_text = '\n'.join(memory_lines)
            if len(memory_text) > remaining_chars:
                memory_text = memory_text[:remaining_chars] + "..."
        else:
            memory_text = ""

        return f"{system_text}\n{memory_text}\n{current_text}"

    def update_context_window(self, window_size: int):
        """Update context window size."""
        self.context_window = window_size
        logger.info(f"Context window updated to {window_size} tokens")

    def get_status(self) -> Dict[str, Any]:
        """Get context manager status."""
        return {
            'system_prompt_loaded': len(self.system_prompt) > 0,
            'context_window': self.context_window
        }