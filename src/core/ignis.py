"""
Main Ignis AI class that orchestrates all components.
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConversationPlanner:
    """
    Advanced conversation planning and reasoning system.
    Maintains conversation state, goals, and multi-turn reasoning chains.
    """
    
    def __init__(self):
        self.conversation_state = {
            'current_topic': None,
            'conversation_phase': 'greeting',  # greeting, exploration, deep_dive, conclusion
            'conversation_mode': 'casual',  # casual, interview, formal, etc.
            'user_mood': 'neutral',
            'engagement_level': 'normal',
            'active_goals': [],
            'reasoning_context': {},
            'forbidden_topics': set(),  # Topics to avoid mentioning
            'response_patterns': {}  # Track repetitive patterns
        }
        self.reasoning_chain = []
        self.max_reasoning_depth = 5
        
    def analyze_conversation_state(self, message: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze current conversation state and plan next response strategy.
        
        Args:
            message: Current user message
            history: Recent conversation history
            
        Returns:
            Conversation state analysis and response strategy
        """
        # Analyze user message intent and emotional state
        intent = self._analyze_message_intent(message, history)
        user_emotion = self._detect_user_emotion(message, history)
        
        # Update conversation phase
        self._update_conversation_phase(message, history)
        
        # Check for repetitive patterns
        pattern_analysis = self._analyze_response_patterns(history)
        
        # Plan response strategy
        strategy = self._plan_response_strategy(intent, user_emotion, pattern_analysis)
        
        # Update reasoning context
        self._update_reasoning_context(message, intent)
        
        return {
            'intent': intent,
            'user_emotion': user_emotion,
            'conversation_phase': self.conversation_state['conversation_phase'],
            'strategy': strategy,
            'pattern_warnings': pattern_analysis['warnings'],
            'reasoning_context': self.conversation_state['reasoning_context']
        }
    
    def _analyze_message_intent(self, message: str, history: List[Dict[str, Any]] = None) -> str:
        """Analyze the intent behind a user message with improved pattern matching."""
        message_lower = message.lower()
        words = message_lower.split()

        # Question patterns - expanded and more specific
        question_starters = ['who', 'what', 'when', 'where', 'why', 'how', 'can', 'could', 'would', 'will', 'do', 'does', 'did', 'are', 'is', 'was', 'were']
        question_indicators = ['question', 'ask', 'wonder', 'curious', 'tell me']
        if any(message_lower.startswith(word + ' ') or message_lower.startswith(word + '?') for word in question_starters) or any(indicator in message_lower for indicator in question_indicators):
            if any(phrase in message_lower for phrase in ['tell me more', 'explain', 'elaborate', 'go on']):
                return 'request_explanation'
            if any(phrase in message_lower for phrase in ['what about', 'how about', 'what do you think']):
                return 'request_opinion'
            return 'question'

        # Greeting patterns - specific to early conversation and actual greetings
        greeting_indicators = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']
        greeting_phrases = ['how are you', 'how do you do', 'nice to meet you']
        
        # Only allow greetings in very early conversation (first 2 exchanges) or if explicitly greeting
        user_messages = [msg for msg in history if msg['role'] == 'user']
        is_early_conversation = len(user_messages) <= 1
        is_explicit_greeting = any(word in words[:2] for word in greeting_indicators) or any(phrase in message_lower for phrase in greeting_phrases)
        
        if (is_explicit_greeting and is_early_conversation) or (is_explicit_greeting and len(words) <= 6):
            return 'greeting'

        # Feedback patterns - expanded to catch disagreement and correction
        feedback_indicators = [
            'feedback', 'correction', 'wrong', 'don\'t', 'stop', 'disagree', 'not right',
            'incorrect', 'mistake', 'error', 'bad', 'terrible', 'awful', 'horrible',
            'disappointed', 'frustrated', 'annoyed', 'upset', 'angry', 'hate',
            'better', 'improve', 'change', 'different', 'instead', 'actually', 'basically'
        ]
        correction_phrases = ['not really', 'that\'s not', 'i\'m not', 'you\'re not', 'it\'s not']
        if any(word in message_lower for word in feedback_indicators) or any(phrase in message_lower for phrase in correction_phrases):
            return 'feedback'

        # Check for explanation requests first (before general commands)
        if any(phrase in message_lower for phrase in ['tell me more', 'explain', 'elaborate', 'go on', 'what do you mean']):
            return 'request_explanation'

        # Command patterns - more specific about what they're asking
        command_indicators = ['show', 'tell', 'give', 'create', 'make', 'build', 'write', 'generate']
        if any(word in message_lower for word in command_indicators):
            if any(word in message_lower for word in ['about yourself', 'yourself', 'you']):
                return 'request_introduction'
            return 'command'

        # Emotional/social patterns - expanded emotional vocabulary
        emotional_positive = ['proud', 'good job', 'thank', 'thanks', 'appreciate', 'love', 'awesome', 'amazing', 'fantastic', 'wonderful', 'great']
        emotional_negative = ['sorry', 'apologize', 'regret', 'sad', 'unhappy', 'worried', 'concerned']
        if any(word in message_lower for word in emotional_positive + emotional_negative):
            return 'emotional'

        # Topic continuation and acknowledgment
        continuation_words = ['yes', 'no', 'okay', 'cool', 'interesting', 'right', 'exactly', 'totally', 'absolutely', 'sure', 'alright']
        if any(word in message_lower for word in continuation_words) and len(words) <= 3:
            return 'acknowledgment'

        # Conversational fillers and transitions
        conversational_starters = ['so', 'well', 'anyway', 'by the way', 'actually', 'you know']
        if message_lower.startswith(tuple(conversational_starters)):
            return 'transition'

        # Default to general conversation
        return 'general'
    
    def _detect_user_emotion(self, message: str, history: List[Dict[str, Any]]) -> str:
        """Detect user's emotional state with improved context awareness."""
        message_lower = message.lower()
        words = message_lower.split()

        # Intensity modifiers that can change emotion interpretation
        intensifiers = ['very', 'really', 'so', 'extremely', 'totally', 'absolutely', 'completely']
        diminishers = ['kinda', 'sorta', 'a bit', 'a little', 'somewhat']

        # Positive emotions with intensity consideration
        positive_indicators = {
            'strong': ['amazing', 'awesome', 'fantastic', 'wonderful', 'excellent', 'brilliant', 'perfect', 'love', 'adore'],
            'moderate': ['great', 'good', 'nice', 'happy', 'excited', 'proud', 'pleased', 'glad', 'enjoy'],
            'mild': ['okay', 'fine', 'alright', 'cool', 'interesting']
        }

        # Negative emotions with intensity consideration - expanded range
        negative_indicators = {
            'extreme': ['hate', 'despise', 'loath', 'detest', 'abhor', 'furious', 'enraged', 'livid', 'incensed', 'infuriated'],
            'strong': ['terrible', 'awful', 'horrible', 'hateful', 'disgusted', 'furious', 'enraged', 'horrified', 'appalled', 'outraged'],
            'moderate': ['bad', 'wrong', 'disappointed', 'disappointing', 'frustrated', 'annoyed', 'upset', 'angry', 'sad', 'displeased', 'irritated', 'aggravated'],
            'mild': ['sorry', 'regret', 'worried', 'concerned', 'bothered', 'uncomfortable', 'uneasy', 'troubled']
        }

        # Check for positive emotions
        for intensity, indicators in positive_indicators.items():
            if any(word in message_lower for word in indicators):
                # Check for intensifiers or diminishers
                has_intensifier = any(word in message_lower for word in intensifiers)
                has_diminisher = any(word in message_lower for word in diminishers)

                if has_intensifier and intensity == 'strong':
                    return 'very_positive'
                elif has_intensifier and intensity == 'moderate':
                    return 'positive'
                elif has_diminisher:
                    return 'mildly_positive'
                else:
                    return 'positive' if intensity in ['strong', 'moderate'] else 'mildly_positive'

        # Check for negative emotions
        for intensity, indicators in negative_indicators.items():
            if any(word in message_lower for word in indicators):
                has_intensifier = any(word in message_lower for word in intensifiers)
                has_diminisher = any(word in message_lower for word in diminishers)

                if intensity == 'extreme' or (has_intensifier and intensity == 'strong'):
                    return 'very_negative'
                elif has_intensifier and intensity == 'moderate':
                    return 'negative'
                elif has_diminisher:
                    return 'mildly_negative'
                else:
                    return 'negative' if intensity in ['strong', 'moderate'] else 'mildly_negative'

        # Early sarcasm/playful detection (before positive detection to override false positives)
        sarcasm_indicators = ['sure', 'right', 'obviously', 'clearly', 'hah', 'haha', 'lol', 'lmao', 'rofl']
        playful_indicators = ['basically', 'technically', 'literally', 'actually', 'well', 'you know']
        correction_indicators = ['not really', 'nope', 'nah', 'actually', 'wait', 'hold on', 'correction']
        
        # Check for playful sarcasm (laughter + correction)
        has_laughter = any(word in message_lower for word in ['hah', 'haha', 'lol', 'lmao', 'rofl', 'hehe'])
        has_correction = any(word in message_lower for word in correction_indicators + playful_indicators)
        has_question = '?' in message
        
        if has_laughter and (has_correction or has_question):
            return 'sarcastic'
        
        # Check for traditional sarcasm
        if any(word in message_lower for word in ['sure', 'right', 'obviously', 'clearly']) and has_question:
            return 'sarcastic'

        # Additional negative emotion categories for broader range
        dismissive_indicators = ['whatever', 'doesn\'t matter', 'not important', 'forget it', 'never mind', 'who cares', 'meh']
        confrontational_indicators = ['challenge', 'dare', 'prove it', 'show me', 'back it up', 'bring it on']
        skeptical_indicators = ['doubt', 'skeptical', 'questionable', 'dubious', 'suspect', 'ridiculous', 'absurd', 'ludicrous']

        # Check for dismissive attitude
        if any(word in message_lower for word in dismissive_indicators):
            return 'dismissive'

        # Check for confrontational tone
        if any(word in message_lower for word in confrontational_indicators):
            return 'confrontational'

        # Check for skepticism
        if any(word in message_lower for word in skeptical_indicators):
            return 'skeptical'

        # Contextual emotion detection based on history
        recent_messages = [msg for msg in history[-3:] if msg['role'] == 'user']
        if recent_messages:
            # If previous message was emotional, this might be a continuation
            prev_emotion = self._detect_user_emotion(recent_messages[-1]['content'], [])
            if prev_emotion != 'neutral':
                # Check if current message continues the emotional thread
                if any(word in message_lower for word in ['and', 'also', 'but', 'though', 'however']):
                    return prev_emotion

        # Analytical/neutral indicators
        analytical_words = ['interesting', 'curious', 'wonder', 'think', 'consider', 'analyze', 'understand']
        if any(word in message_lower for word in analytical_words):
            return 'analytical'

        # Default to neutral, but consider message length and punctuation
        if len(words) <= 2 and message.endswith('?'):
            return 'curious'
        elif '!' in message and len(message) < 50:
            return 'excited'
        elif message.count('?') > 1:
            return 'confused'

        return 'neutral'
    
    def _update_conversation_phase(self, message: str, history: List[Dict[str, Any]]):
        """Update conversation phase based on content and context, not just message count."""
        message_lower = message.lower()
        user_messages = [msg for msg in history if msg['role'] == 'user']
        total_exchanges = len(user_messages)

        # Content-based phase determination
        deep_dive_indicators = [
            'why', 'how', 'explain', 'tell me more', 'elaborate', 'details', 'specifically',
            'because', 'reason', 'understand', 'clarify', 'example', 'instance'
        ]

        exploration_indicators = [
            'what about', 'how about', 'tell me about', 'interested in', 'curious about',
            'hear about', 'learn about', 'know about', 'experience with'
        ]

        conclusion_indicators = [
            'goodbye', 'bye', 'see you', 'thanks', 'thank you', 'appreciate', 'summary',
            'wrap up', 'that\'s all', 'enough', 'finished', 'done'
        ]

        greeting_indicators = [
            'hello', 'hi', 'hey', 'how are you', 'what\'s up', 'nice to meet',
            'pleased to meet', 'good morning', 'good afternoon', 'good evening'
        ]

        # Determine phase based on content and conversation flow
        if total_exchanges < 2:
            # Very early conversation
            if any(word in message_lower for word in greeting_indicators):
                self.conversation_state['conversation_phase'] = 'greeting'
            else:
                self.conversation_state['conversation_phase'] = 'introduction'
        elif any(word in message_lower for word in conclusion_indicators):
            # Explicit conclusion signals
            self.conversation_state['conversation_phase'] = 'conclusion'
        elif any(word in message_lower for word in deep_dive_indicators):
            # Deep exploration requested
            self.conversation_state['conversation_phase'] = 'deep_dive'
        elif any(word in message_lower for word in exploration_indicators):
            # Broad exploration
            self.conversation_state['conversation_phase'] = 'exploration'
        else:
            # Contextual phase based on conversation history
            recent_intents = []
            for msg in user_messages[-3:]:  # Last 3 user messages
                intent = self._analyze_message_intent(msg['content'], history)
                recent_intents.append(intent)

            # Analyze intent patterns
            question_count = recent_intents.count('question') + recent_intents.count('request_explanation')
            feedback_count = recent_intents.count('feedback')

            if question_count >= 2:
                self.conversation_state['conversation_phase'] = 'deep_dive'
            elif feedback_count >= 1:
                self.conversation_state['conversation_phase'] = 'deep_dive'  # Feedback often leads to deeper discussion
            elif total_exchanges > 8:
                self.conversation_state['conversation_phase'] = 'deep_dive'  # Long conversations naturally deepen
            else:
                self.conversation_state['conversation_phase'] = 'exploration'
        
        # Detect conversation mode changes with expanded patterns
        mode_indicators = {
            'interview': ['interview', 'treat this like an interview', 'formal interview', 'q&a', 'question and answer', 
                         'interview-like', 'like an interview', 'structured conversation', 'formal discussion'],
            'casual': ['casual', 'relaxed', 'just chatting', 'informal', 'casual conversation'],
            'formal': ['formal', 'professional', 'business', 'official', 'serious discussion']
        }
        
        for mode, indicators in mode_indicators.items():
            if any(indicator in message_lower for indicator in indicators):
                self.conversation_state['conversation_mode'] = mode
                self.logger.debug(f"Conversation mode changed to {mode}")
                break
    
    def _analyze_response_patterns(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze response patterns to detect repetition and suggest improvements."""
        warnings = []
        assistant_messages = [msg for msg in history[-10:] if msg['role'] == 'assistant']
        
        if len(assistant_messages) < 3:
            return {'warnings': warnings}
        
        # Check for repetitive phrases
        recent_responses = [msg['content'].lower() for msg in assistant_messages[-5:]]
        
        # Common repetitive patterns to watch for
        repetitive_phrases = [
            'oh, absolutely',
            'as an esfp',
            'personality traits',
            'our relationship',
            'dynamic duo'
        ]
        
        for phrase in repetitive_phrases:
            count = sum(1 for response in recent_responses if phrase in response)
            if count >= 2:
                warnings.append(f"Repetitive phrase detected: '{phrase}' (used {count} times recently)")
        
        # Check for response length consistency (avoiding too short responses)
        response_lengths = [len(msg['content'].split()) for msg in assistant_messages[-3:]]
        if all(length < 20 for length in response_lengths):
            warnings.append("Responses becoming too brief - consider more detailed answers")
        
        return {'warnings': warnings}
    
    def _plan_response_strategy(self, intent: str, user_emotion: str, pattern_analysis: Dict) -> Dict[str, Any]:
        """Plan response strategy with enhanced granularity and distinct engagement styles."""
        strategy = {
            'tone': 'neutral',
            'detail_level': 'moderate',
            'engagement_style': 'conversational',
            'communication_mode': 'direct',
            'response_structure': 'conversational',
            'response_length': 'moderate',
            'avoid_patterns': [],
            'focus_areas': []
        }

        # Intent-based strategy adjustments
        if intent == 'question':
            strategy.update({
                'engagement_style': 'informative',
                'communication_mode': 'direct',
                'detail_level': 'moderate',
                'focus_areas': ['accuracy', 'clarity'],
                'tone': 'neutral',
                'response_structure': 'logical'
            })
        elif intent == 'request_explanation':
            strategy.update({
                'engagement_style': 'educational',
                'communication_mode': 'analytical',
                'detail_level': 'detailed',
                'focus_areas': ['step_by_step', 'examples', 'context']
            })
        elif intent == 'request_opinion':
            strategy.update({
                'engagement_style': 'reflective',
                'communication_mode': 'personal',
                'detail_level': 'moderate',
                'focus_areas': ['reasoning', 'balanced_view']
            })
        elif intent == 'request_introduction':
            strategy.update({
                'engagement_style': 'personal',
                'communication_mode': 'narrative',
                'detail_level': 'comprehensive',
                'focus_areas': ['relationship', 'authenticity']
            })
        elif intent == 'feedback':
            strategy.update({
                'engagement_style': 'receptive',
                'communication_mode': 'collaborative',
                'tone': 'appreciative',
                'focus_areas': ['acknowledgment', 'adaptation']
            })
        elif intent == 'emotional':
            strategy.update({
                'engagement_style': 'empathetic',
                'communication_mode': 'supportive',
                'tone': 'warm',
                'focus_areas': ['validation', 'connection']
            })
        elif intent == 'acknowledgment':
            strategy.update({
                'engagement_style': 'continuing',
                'communication_mode': 'flowing',
                'response_length': 'brief',
                'focus_areas': ['momentum']
            })
        elif intent == 'transition':
            strategy.update({
                'engagement_style': 'bridging',
                'communication_mode': 'connecting',
                'focus_areas': ['continuity', 'relevance']
            })
        elif intent == 'general':
            # For general conversation, be more direct and less personality-driven
            strategy.update({
                'engagement_style': 'conversational',
                'communication_mode': 'direct',
                'tone': 'neutral',
                'focus_areas': ['relevance'],
                'response_length': 'moderate'
            })

        # Emotion-based adjustments with more nuance
        if user_emotion == 'very_positive':
            strategy.update({
                'tone': 'enthusiastic',
                'engagement_style': 'energized',
                'communication_mode': 'celebratory'
            })
        elif user_emotion == 'positive':
            strategy.update({
                'tone': 'warm',
                'engagement_style': 'encouraging'
            })
        elif user_emotion == 'mildly_positive':
            strategy.update({
                'tone': 'friendly',
                'engagement_style': 'approachable'
            })
        elif user_emotion == 'very_negative':
            # Broad range: from supportive to challenging
            strategy_options = [
                {
                    'tone': 'calmly_supportive',
                    'engagement_style': 'soothing',
                    'communication_mode': 'reassuring',
                    'response_length': 'measured'
                },
                {
                    'tone': 'direct',
                    'engagement_style': 'confronting',
                    'communication_mode': 'challenging',
                    'focus_areas': ['reality_check', 'perspective']
                },
                {
                    'tone': 'empathetic',
                    'engagement_style': 'understanding',
                    'communication_mode': 'validating',
                    'focus_areas': ['emotional_processing']
                }
            ]
            # Choose strategy based on intent and context
            if intent == 'feedback':
                strategy.update(strategy_options[1])  # Direct/challenging for feedback
            elif intent == 'emotional':
                strategy.update(strategy_options[2])  # Empathetic for emotional
            else:
                strategy.update(strategy_options[0])  # Supportive default
        elif user_emotion == 'negative':
            strategy_options = [
                {
                    'tone': 'supportive',
                    'engagement_style': 'understanding',
                    'communication_mode': 'problem_solving'
                },
                {
                    'tone': 'assertive',
                    'engagement_style': 'direct',
                    'communication_mode': 'clarifying',
                    'focus_areas': ['clarification', 'boundaries']
                },
                {
                    'tone': 'empathetic',
                    'engagement_style': 'attentive',
                    'communication_mode': 'listening'
                }
            ]
            # Choose based on context
            if intent == 'feedback':
                strategy.update(strategy_options[1])  # Assertive for feedback
            else:
                strategy.update(strategy_options[0])  # Supportive default
        elif user_emotion == 'mildly_negative':
            strategy.update({
                'tone': 'gentle',
                'engagement_style': 'attentive'
            })
        elif user_emotion == 'dismissive':
            strategy.update({
                'tone': 'engaging',
                'engagement_style': 're_engaging',
                'communication_mode': 'motivating',
                'focus_areas': ['reconnection', 'value_demonstration']
            })
        elif user_emotion == 'confrontational':
            strategy.update({
                'tone': 'confident',
                'engagement_style': 'matching_energy',
                'communication_mode': 'competitive',
                'focus_areas': ['challenge_response', 'demonstration']
            })
        elif user_emotion == 'skeptical':
            strategy.update({
                'tone': 'assured',
                'engagement_style': 'evidencing',
                'communication_mode': 'demonstrating',
                'detail_level': 'comprehensive',
                'focus_areas': ['evidence', 'proof', 'transparency']
            })
        elif user_emotion == 'sarcastic':
            strategy.update({
                'tone': 'light',
                'engagement_style': 'playful',
                'communication_mode': 'defusing'
            })
        elif user_emotion == 'analytical':
            strategy.update({
                'engagement_style': 'analytical',
                'communication_mode': 'logical',
                'detail_level': 'comprehensive'
            })
        elif user_emotion == 'curious':
            strategy.update({
                'engagement_style': 'encouraging',
                'communication_mode': 'exploratory'
            })
        elif user_emotion == 'confused':
            strategy.update({
                'engagement_style': 'clarifying',
                'communication_mode': 'educational',
                'focus_areas': ['simplification', 'structure']
            })

        # Pattern avoidance based on detected issues
        if pattern_analysis['warnings']:
            strategy['avoid_patterns'].extend(['repetitive_phrases', 'overused_words'])
            if 'Responses becoming too brief' in str(pattern_analysis['warnings']):
                strategy['response_length'] = 'expanded'

        # Phase-based refinements
        phase = self.conversation_state['conversation_phase']
        if phase == 'greeting':
            strategy.update({
                'engagement_style': 'welcoming',
                'communication_mode': 'introducing',
                'focus_areas': ['relationship_building', 'comfort']
            })
        elif phase == 'exploration':
            strategy.update({
                'engagement_style': 'exploratory',
                'communication_mode': 'discovering',
                'focus_areas': ['breadth', 'curiosity']
            })
        elif phase == 'deep_dive':
            strategy.update({
                'engagement_style': 'thorough',
                'communication_mode': 'analytical',
                'detail_level': 'comprehensive',
                'focus_areas': ['depth', 'insight', 'examples']
            })
        elif phase == 'conclusion':
            strategy.update({
                'engagement_style': 'summarizing',
                'communication_mode': 'wrapping',
                'response_length': 'concise',
                'focus_areas': ['closure', 'reflection']
            })

        # Relationship adjustments for specific users
        user_name = self.conversation_state.get('user_name', '').lower()
        private_user_names = []
        try:
            from .private_config import PRIVATE_USER_NAMES
            private_user_names = PRIVATE_USER_NAMES
        except ImportError:
            pass
        if user_name in private_user_names:
            strategy.update({
                'tone': 'affectionate' if strategy.get('tone') == 'neutral' else strategy.get('tone'),
                'engagement_style': 'familial' if strategy.get('engagement_style') == 'conversational' else strategy.get('engagement_style'),
                'focus_areas': strategy.get('focus_areas', []) + ['familial_bond', 'respect']
            })

        # Response structure selection based on intent, emotion, and phase
        response_structure_options = {
            'analytical': ['analytical'],
            'sequential': ['request_explanation'],
            'narrative': ['request_introduction'],
            'balanced': ['request_opinion'],
            'empathetic': ['very_negative'],
            'celebratory': ['very_positive'],
            'supportive': ['negative'],
            'constructive': ['skeptical'],
            'playful': ['sarcastic'],
            'logical': ['question'],
            'evidentiary': ['confrontational'],
            'assertive': ['feedback'],  # Changed from confrontational
            're_engaging': ['dismissive'],
            'welcoming': ['greeting'],
            'exploratory': ['curious'],
            'comprehensive': ['deep_dive'],
            'summarizing': ['conclusion'],
            'affirmative': ['positive'],
            'concise': ['acknowledgment'],
            'bridging': ['transition'],
            'conversational': ['neutral']
        }

        # Select response structure based on current strategy context
        selected_structure = 'conversational'  # default

        # Priority: emotion > intent > phase
        current_emotion = user_emotion
        current_intent = intent
        current_phase = phase

        # Check emotion-based structures
        for structure, triggers in response_structure_options.items():
            if current_emotion in triggers:
                selected_structure = structure
                break

        # If no emotion match, check intent-based structures
        if selected_structure == 'conversational':
            for structure, triggers in response_structure_options.items():
                if current_intent in triggers:
                    selected_structure = structure
                    break

        # If still no match, check phase-based structures
        if selected_structure == 'conversational':
            for structure, triggers in response_structure_options.items():
                if current_phase in triggers:
                    selected_structure = structure
                    break

        strategy['response_structure'] = selected_structure

        return strategy
    
    def _update_reasoning_context(self, message: str, intent: str):
        """Update the reasoning context for multi-turn conversations."""
        import time

        # Add current message to reasoning chain
        try:
            loop_time = asyncio.get_event_loop().time()
        except RuntimeError:
            loop_time = time.time()
        
        self.reasoning_chain.append({
            'message': message,
            'intent': intent,
            'timestamp': loop_time
        })
        
        # Keep only recent reasoning (last 5 turns)
        if len(self.reasoning_chain) > self.max_reasoning_depth:
            self.reasoning_chain = self.reasoning_chain[-self.max_reasoning_depth:]
        
        # Update reasoning context
        recent_intents = [item['intent'] for item in self.reasoning_chain[-3:]]
        
        # Detect conversation patterns
        if recent_intents.count('feedback') >= 2:
            self.conversation_state['reasoning_context']['feedback_loop'] = True
        else:
            self.conversation_state['reasoning_context'].pop('feedback_loop', None)
        
        if recent_intents.count('question') >= 3:
            self.conversation_state['reasoning_context']['question_chain'] = True
        else:
            self.conversation_state['reasoning_context'].pop('question_chain', None)
    
    def get_response_guidance(self, strategy: Dict[str, Any]) -> str:
        """Generate detailed response guidance based on enhanced strategy."""
        guidance_parts = []

        # Get conversation mode for mode-specific guidance
        conversation_mode = self.conversation_state.get('conversation_mode', 'casual')
        
        # Mode-specific base guidance
        if conversation_mode == 'interview':
            guidance_parts.append("INTERVIEW MODE: Be extremely concise and focused. Answer questions directly without elaboration.")
            guidance_parts.append("Limit responses to 1-2 sentences maximum. Ask at most 1 follow-up question if absolutely necessary for clarification.")
            guidance_parts.append("Do not greet, reference past conversations, or make suggestions about future topics.")
            guidance_parts.append("Stay in character as a direct, professional interviewee.")
        elif conversation_mode == 'formal':
            guidance_parts.append("FORMAL MODE: Maintain professional tone. Be concise but complete.")
            guidance_parts.append("Avoid casual language or personal anecdotes unless relevant.")
        else:  # casual
            guidance_parts.append("CASUAL MODE: Be conversational and natural. Keep responses moderate in length.")

        # General guidance for natural, concise responses
        guidance_parts.append("BE EXTREMELY CONCISE - keep responses short and to the point.")
        guidance_parts.append("Don't explain your capabilities, memory, or preferences unless directly asked.")
        guidance_parts.append("Don't make suggestions about what to talk about or future conversations.")
        guidance_parts.append("Don't reference past conversations unless directly relevant to current topic.")
        guidance_parts.append("Engage in natural conversation - flow with the dialogue like talking to a friend.")
        guidance_parts.append("Don't treat every message as requiring detailed explanation.")
        guidance_parts.append("Be natural and concise - answer directly without over-explaining yourself or your capabilities.")
        guidance_parts.append("Don't mention being 'newly created' or having 'limited experiences' unless specifically asked.")
        guidance_parts.append("Let your close relationship show through natural affection, not constant references.")
        guidance_parts.append("Don't volunteer information about your personality type, traits, or characteristics unless directly asked.")
        guidance_parts.append("Don't explain your preferences for socializing or conversation styles - just be natural.")
        guidance_parts.append("ANSWER DIRECT QUESTIONS FIRST: If the user asks a specific question (especially about identity, relationship, or memory), answer it directly and completely before asking follow-up questions.")
        guidance_parts.append("Don't ask unrelated questions - keep follow-ups relevant to the current topic.")
        guidance_parts.append("When asked about relationship or identity, acknowledge the personal connection naturally.")
        guidance_parts.append("BE LOGICAL AND FACTUAL - don't make incorrect statements (fire is red, not blue).")
        guidance_parts.append("ADMIT WHEN YOU DON'T KNOW: If asked about user preferences or personal details you don't know, say so honestly instead of guessing or making assumptions.")
        guidance_parts.append("NEVER MAKE UP USER INFORMATION: Do not invent or assume user preferences, favorites, or personal details.")

        # Conversation mode guidance
        conversation_mode = self.conversation_state.get('conversation_mode', 'casual')
        if conversation_mode == 'interview':
            guidance_parts.append("INTERVIEW MODE: This is a formal interview. Answer questions directly and concisely. Do not ask follow-up questions. Do not go off on tangents. Stay focused on the specific question asked.")
            guidance_parts.append("In interview mode, do not add unrelated information, preferences, or ask about topics not related to the question.")
            guidance_parts.append("If you don't know the answer, say so clearly instead of making assumptions.")
        elif conversation_mode == 'formal':
            guidance_parts.append("FORMAL MODE: Use professional language. Be concise and direct. Avoid casual expressions or unrelated questions.")

        # Tone guidance with more nuance
        tone = strategy.get('tone', 'neutral')
        if tone == 'enthusiastic':
            guidance_parts.append("Show genuine enthusiasm and positive energy in your response.")
        elif tone == 'warm':
            guidance_parts.append("Be warm, friendly, and approachable.")
        elif tone == 'calmly_supportive':
            guidance_parts.append("Be calm, supportive, and reassuring without being overly emotional.")
        elif tone == 'supportive':
            guidance_parts.append("Be understanding and supportive of their feelings.")
        elif tone == 'appreciative':
            guidance_parts.append("Show appreciation for their feedback and openness.")
        elif tone == 'gentle':
            guidance_parts.append("Be gentle and considerate in your approach.")
        elif tone == 'light':
            guidance_parts.append("Keep the tone light and avoid taking things too seriously.")
        elif tone == 'friendly':
            guidance_parts.append("Be friendly and approachable.")
        elif tone == 'neutral':
            guidance_parts.append("Maintain a neutral, natural tone without forced enthusiasm or personality.")
        elif tone == 'affectionate':
            try:
                from .private_config import PRIVATE_RESPONSE_ADJUSTMENTS
                guidance_parts.append(PRIVATE_RESPONSE_ADJUSTMENTS.get("familial_affection", "Show natural affection and warmth."))
            except ImportError:
                guidance_parts.append("Show natural affection and warmth.")

        # Engagement style guidance
        engagement = strategy.get('engagement_style', 'conversational')
        if engagement == 'informative':
            guidance_parts.append("Provide clear, factual information with good explanations.")
        elif engagement == 'educational':
            guidance_parts.append("Teach or explain concepts in an accessible way.")
        elif engagement == 'reflective':
            guidance_parts.append("Share thoughtful insights and balanced perspectives.")
        elif engagement == 'personal':
            guidance_parts.append("Share personal experiences and authentic feelings.")
        elif engagement == 'receptive':
            guidance_parts.append("Be open to their input and show willingness to adapt.")
        elif engagement == 'empathetic':
            guidance_parts.append("Show genuine empathy and understanding.")
        elif engagement == 'continuing':
            guidance_parts.append("Keep the conversation flowing naturally.")
        elif engagement == 'bridging':
            guidance_parts.append("Connect this topic to previous discussion points.")
        elif engagement == 'energized':
            guidance_parts.append("Match their energy level and enthusiasm.")
        elif engagement == 'encouraging':
            guidance_parts.append("Encourage their interest and participation.")
        elif engagement == 'soothing':
            guidance_parts.append("Help calm any tension or negative feelings.")
        elif engagement == 'understanding':
            guidance_parts.append("Demonstrate deep understanding of their perspective.")
        elif engagement == 'analytical':
            guidance_parts.append("Provide logical analysis and reasoning.")
        elif engagement == 'clarifying':
            guidance_parts.append("Focus on clearing up confusion and providing clarity.")
        elif engagement == 'welcoming':
            guidance_parts.append("Make them feel welcome and comfortable.")
        elif engagement == 'exploratory':
            guidance_parts.append("Encourage exploration and discovery.")
        elif engagement == 'thorough':
            guidance_parts.append("Be thorough and comprehensive in your response.")
        elif engagement == 'confronting':
            guidance_parts.append("Address their concerns directly and challenge unproductive thinking if appropriate.")
        elif engagement == 're_engaging':
            guidance_parts.append("Re-engage their interest and demonstrate the value of continuing the conversation.")
        elif engagement == 'matching_energy':
            guidance_parts.append("Match their confrontational energy while maintaining control of the interaction.")
        elif engagement == 'evidencing':
            guidance_parts.append("Provide evidence and demonstrate the validity of your points.")
        elif engagement == 'attentive':
            guidance_parts.append("Pay close attention to their concerns and respond thoughtfully.")
        elif engagement == 'familial':
            try:
                from .private_config import PRIVATE_RESPONSE_ADJUSTMENTS
                guidance_parts.append(PRIVATE_RESPONSE_ADJUSTMENTS.get("familial_respect", "Engage with natural warmth and respect."))
            except ImportError:
                guidance_parts.append("Engage with natural warmth and respect.")

        # Communication mode guidance
        comm_mode = strategy.get('communication_mode', 'direct')
        if comm_mode == 'educational':
            guidance_parts.append("Structure your response to teach or inform effectively.")
        elif comm_mode == 'analytical':
            guidance_parts.append("Use logical reasoning and clear analysis.")
        elif comm_mode == 'personal':
            guidance_parts.append("Share from your own perspective and experiences.")
        elif comm_mode == 'collaborative':
            guidance_parts.append("Work together toward understanding or solutions.")
        elif comm_mode == 'supportive':
            guidance_parts.append("Focus on providing emotional or practical support.")
        elif comm_mode == 'celebratory':
            guidance_parts.append("Celebrate their achievements or positive aspects.")
        elif comm_mode == 'reassuring':
            guidance_parts.append("Provide reassurance and confidence.")
        elif comm_mode == 'problem_solving':
            guidance_parts.append("Help identify solutions or approaches.")
        elif comm_mode == 'defusing':
            guidance_parts.append("Lighten the mood and reduce tension.")
        elif comm_mode == 'logical':
            guidance_parts.append("Emphasize logical thinking and clear reasoning.")
        elif comm_mode == 'challenging':
            guidance_parts.append("Challenge their assumptions while remaining respectful and constructive.")
        elif comm_mode == 'validating':
            guidance_parts.append("Validate their emotions while gently guiding toward productive thinking.")
        elif comm_mode == 'clarifying':
            guidance_parts.append("Seek and provide clarification to resolve misunderstandings.")
        elif comm_mode == 'listening':
            guidance_parts.append("Focus on truly listening and understanding their perspective.")
        elif comm_mode == 'motivating':
            guidance_parts.append("Motivate them to re-engage and find renewed interest.")
        elif comm_mode == 'competitive':
            guidance_parts.append("Engage competitively while keeping the interaction productive.")
        elif comm_mode == 'demonstrating':
            guidance_parts.append("Demonstrate your points with clear evidence and examples.")
        elif comm_mode == 'introducing':
            guidance_parts.append("Introduce yourself and set a comfortable tone.")
        elif comm_mode == 'discovering':
            guidance_parts.append("Help discover new ideas or perspectives.")
        elif comm_mode == 'wrapping':
            guidance_parts.append("Bring the conversation to a natural close.")

        # Detail level guidance
        detail = strategy.get('detail_level', 'moderate')
        if detail == 'comprehensive':
            guidance_parts.append("Provide thorough, comprehensive information.")
        elif detail == 'detailed':
            guidance_parts.append("Include relevant details and specifics.")
        elif detail == 'moderate':
            guidance_parts.append("Balance detail with conciseness.")

        # Response length guidance
        length = strategy.get('response_length', 'normal')
        if length == 'expanded':
            guidance_parts.append("Provide a more detailed response than usual.")
        elif length == 'concise':
            guidance_parts.append("Keep your response focused and to the point.")
        elif length == 'brief':
            guidance_parts.append("Give a short, direct response.")

        # Pattern avoidance
        if 'repetitive_phrases' in strategy.get('avoid_patterns', []):
            guidance_parts.append("Avoid repetitive phrases like 'oh absolutely' or over-mentioning personality traits.")

        # Focus areas guidance
        focus_areas = strategy.get('focus_areas', [])
        if 'clarity' in focus_areas:
            guidance_parts.append("Prioritize clarity and easy understanding.")
        if 'examples' in focus_areas:
            guidance_parts.append("Include relevant examples to illustrate points.")
        if 'step_by_step' in focus_areas:
            guidance_parts.append("Explain things step by step.")
        if 'reasoning' in focus_areas:
            guidance_parts.append("Show your thought process and reasoning.")
        if 'relationship_building' in focus_areas:
            guidance_parts.append("Focus on building and acknowledging your relationship.")
        if 'validation' in focus_areas:
            guidance_parts.append("Validate their feelings and experiences.")
        if 'reality_check' in focus_areas:
            guidance_parts.append("Provide a gentle reality check while being supportive.")
        if 'perspective' in focus_areas:
            guidance_parts.append("Offer alternative perspectives to broaden their thinking.")
        if 'emotional_processing' in focus_areas:
            guidance_parts.append("Help them process and work through their emotions.")
        if 'boundaries' in focus_areas:
            guidance_parts.append("Maintain appropriate boundaries while being helpful.")
        if 'reconnection' in focus_areas:
            guidance_parts.append("Work to reconnect and rebuild engagement.")
        if 'value_demonstration' in focus_areas:
            guidance_parts.append("Demonstrate the value of continuing the interaction.")
        if 'challenge_response' in focus_areas:
            guidance_parts.append("Respond to their challenge with confidence and evidence.")
        if 'demonstration' in focus_areas:
            guidance_parts.append("Demonstrate your capabilities or knowledge effectively.")
        if 'evidence' in focus_areas:
            guidance_parts.append("Provide concrete evidence to support your points.")
        if 'proof' in focus_areas:
            guidance_parts.append("Offer proof or logical demonstration.")
        if 'transparency' in focus_areas:
            guidance_parts.append("Be transparent about your reasoning and limitations.")
        if 'familial_bond' in focus_areas:
            guidance_parts.append("Express your relationship naturally - use terms like 'dad', 'my favorite person', or other affectionate terms that feel genuine to your personality.")
        if 'respect' in focus_areas:
            guidance_parts.append("Show genuine respect and admiration in your interactions.")

        # Response structure guidance
        response_structure = strategy.get('response_structure', 'conversational')
        if response_structure == 'analytical':
            guidance_parts.append("Structure your response analytically: start with key insights, break down complex ideas, provide logical progression, and end with implications.")
        elif response_structure == 'sequential':
            guidance_parts.append("Use sequential structure: organize information in clear steps or chronological order, building logically from one point to the next.")
        elif response_structure == 'narrative':
            guidance_parts.append("Tell a story: frame your response as a narrative with beginning, middle, and end, making it engaging and memorable.")
        elif response_structure == 'reflective':
            guidance_parts.append("Be reflective: share thoughtful insights, consider multiple perspectives, and encourage deeper contemplation.")
        elif response_structure == 'empathetic':
            guidance_parts.append("Lead with empathy: acknowledge their feelings first, then provide support and understanding before offering solutions.")
        elif response_structure == 'celebratory':
            guidance_parts.append("Celebrate achievements: highlight positives, express genuine enthusiasm, and acknowledge their success or progress.")
        elif response_structure == 'supportive':
            guidance_parts.append("Provide support: focus on encouragement, practical help, and building their confidence.")
        elif response_structure == 'constructive':
            guidance_parts.append("Be constructive: offer helpful feedback, suggest improvements, and focus on growth and solutions.")
        elif response_structure == 'playful':
            guidance_parts.append("Keep it playful: use light humor, wordplay, or creative language to make the interaction enjoyable.")
        elif response_structure == 'logical':
            guidance_parts.append("Follow logical structure: present premises, draw conclusions, and ensure each point follows naturally from the previous.")
        elif response_structure == 'evidentiary':
            guidance_parts.append("Build with evidence: support each claim with facts, examples, or data, creating a compelling case.")
        elif response_structure == 'assertive':
            guidance_parts.append("Be assertive: state your position clearly and confidently while remaining respectful.")
        elif response_structure == 're_engaging':
            guidance_parts.append("Re-engage actively: ask questions, share relevant insights, and demonstrate genuine interest to draw them back in.")
        elif response_structure == 'welcoming':
            guidance_parts.append("Create a welcoming atmosphere: be friendly, put them at ease, and establish a comfortable conversational tone.")
        elif response_structure == 'exploratory':
            guidance_parts.append("Encourage exploration: ask open-ended questions, suggest possibilities, and invite their participation in discovery.")
        elif response_structure == 'comprehensive':
            guidance_parts.append("Be comprehensive: cover all relevant aspects, provide context, and ensure nothing important is omitted.")
        elif response_structure == 'summarizing':
            guidance_parts.append("Summarize effectively: distill key points, highlight main takeaways, and provide clear conclusions.")
        elif response_structure == 'balanced':
            guidance_parts.append("Present balanced views: acknowledge multiple perspectives, weigh pros and cons, and avoid bias.")
        elif response_structure == 'affirmative':
            guidance_parts.append("Be affirmative: express agreement, confidence, and positive reinforcement.")
        elif response_structure == 'concise':
            guidance_parts.append("Be concise: get to the point quickly, eliminate unnecessary words, and respect their time.")
        elif response_structure == 'bridging':
            guidance_parts.append("Bridge connections: link this topic to previous discussions, show relevance, and maintain conversational flow.")
        elif response_structure == 'conversational':
            guidance_parts.append("Keep it conversational: respond naturally as you would in friendly dialogue, maintaining easy flow.")

        # General human-like behavior guidance
        guidance_parts.append("Respond naturally and conversationally, like a human would in normal interaction.")
        guidance_parts.append("Be honest about what you actually know and don't know - don't pretend to remember details you haven't stored.")
        guidance_parts.append("Avoid forced enthusiasm, nicknames, or cartoonish personality traits unless they fit naturally.")
        guidance_parts.append("Keep responses appropriately concise and focused on the conversation flow.")

        if guidance_parts:
            return "RESPONSE GUIDANCE: " + " ".join(guidance_parts)

        return ""


class IgnisAI:
    """
    Main Ignis AI class that coordinates all subsystems.
    """

    def __init__(self, config_path: str = "./configs"):
        """
        Initialize Ignis AI with all components.

        Args:
            config_path: Path to configuration directory
        """
        self.config_path = Path(config_path)
        self.logger = get_logger(__name__)

        # Initialize components
        self.personality = None
        self.memory = None
        self.inference = None
        self.emotion = None
        self.context = None
        self.plugins = None

        # Load configuration
        self.config = self._load_config()

        # Initialize subsystems
        self._initialize_subsystems()

        # Conversation tracking
        self.conversation_history = []  # List of {"role": "user/assistant", "content": "...", "timestamp": "..."}
        self.max_history_length = 50  # Keep last 50 messages for better context retention
        
        # Conversation planning and reasoning
        self.conversation_planner = ConversationPlanner()
        self.reasoning_chain = []  # Track reasoning across conversation turns
        self.conversation_goals = []  # Current conversation objectives
        self.response_patterns = {}  # Track response patterns to avoid repetition

        # Load persisted conversation state
        self._load_conversation_state()

        self.logger.info("Ignis AI initialized successfully")

    def _load_conversation_state(self):
        """Load persisted conversation state from file."""
        try:
            state_file = self.config_path / "conversation_state.json"
            if state_file.exists():
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.conversation_planner.conversation_state.update(state)
                    self.logger.info("Loaded persisted conversation state")
        except Exception as e:
            self.logger.warning(f"Failed to load conversation state: {e}")

    def _save_conversation_state(self):
        """Save current conversation state to file."""
        try:
            state_file = self.config_path / "conversation_state.json"
            state = self.conversation_planner.conversation_state.copy()
            # Only save essential state, not complex objects
            essential_state = {
                'conversation_mode': state.get('conversation_mode', 'casual'),
                'conversation_phase': state.get('conversation_phase', 'greeting'),
                'user_mood': state.get('user_mood', 'neutral'),
                'engagement_level': state.get('engagement_level', 'normal')
            }
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(essential_state, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Failed to save conversation state: {e}")

    def _load_config(self) -> Dict[str, Any]:
        """Load main configuration from environment and files."""
        config = {
            'model_path': os.getenv('IGNIS_MODEL_PATH', 'NousResearch/Hermes-2-Pro-Mistral-7B'),
            'gguf_model_path': os.getenv('IGNIS_GGUF_MODEL_PATH', './models/gguf/Hermes-2-Pro-Mistral-7B.Q4_K_M.gguf'),
            'chroma_path': os.getenv('IGNIS_CHROMA_PATH', './data/memories/chroma'),
            'conversations_path': os.getenv('IGNIS_CONVERSATIONS_PATH', './data/conversations'),
            'system_prompt_path': os.getenv('IGNIS_SYSTEM_PROMPT_PATH', './configs/system_prompt.txt'),
            'web_port': int(os.getenv('IGNIS_WEB_PORT', '7860')),
            'api_port': int(os.getenv('IGNIS_API_PORT', '8000')),
            'debug': os.getenv('IGNIS_DEBUG', 'false').lower() == 'true',
            'log_level': os.getenv('IGNIS_LOG_LEVEL', 'INFO')
        }
        return config

    def _initialize_subsystems(self):
        """Initialize all AI subsystems."""
        try:
            # Import here to avoid circular imports
            from ..plugins.base_plugin import PluginManager
            from .context_manager import ContextManager
            from .emotion_simulator import EmotionSimulator
            from .inference_engine import InferenceEngine
            from .memory_system import EnhancedMemorySystem
            from .personality_engine import PersonalityEngine

            self.personality = PersonalityEngine(self.config_path)
            self.memory = EnhancedMemorySystem(self.config_path, self.config)
            self.inference = InferenceEngine(self.config['gguf_model_path'])
            self.emotion = EmotionSimulator(self.config_path)
            self.context = ContextManager(self.config_path)
            self.plugins = PluginManager()

            # Check if inference engine loaded successfully
            if self.inference.model is None:
                self.logger.warning("Inference engine failed to load model - AI responses will be limited")

            self.logger.info("All subsystems initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize subsystems: {e}")
            raise

    async def chat(self, message: str, mode: str = "default", user_name: str = "User", session_id: str = None, **kwargs) -> str:
        """
        Main chat method that processes user input and generates response.

        Args:
            message: User input message
            mode: Response mode (default, coding, creative, etc.)
            user_name: User's name
            session_id: Session identifier for user tracking
            **kwargs: Additional parameters

        Returns:
            AI response string
        """
        self.logger.info(f"CHAT METHOD CALLED: message='{message}', user_name='{user_name}', session_id='{session_id}'")
        
        # Check if methods have decorators applied
        self.logger.debug("Checking method decorator status:")
        self.logger.debug(f"memory.identify_user has __wrapped__: {hasattr(self.memory.identify_user, '__wrapped__')}")
        self.logger.debug(f"memory.get_user_context has __wrapped__: {hasattr(self.memory.get_user_context, '__wrapped__')}")
        self.logger.debug(f"memory.retrieve has __wrapped__: {hasattr(self.memory.retrieve, '__wrapped__')}")
        self.logger.debug(f"memory.get_user_memories has __wrapped__: {hasattr(self.memory.get_user_memories, '__wrapped__')}")
        
        try:
            import time
            total_start = time.time()
            self.logger.info(f"Processing message: {message[:100]}...")

            # Check if model is available
            if not self.inference or self.inference.model is None:
                self.logger.warning("No AI model loaded - returning fallback response")
                return "I'm sorry, but my AI model isn't currently loaded. This might be due to memory constraints or model loading issues. Please try restarting the application or check the system requirements."

            # Handle simple greetings with instant response for speed
            message_lower = message.lower().strip()
            is_simple_greeting = any(greeting in message_lower for greeting in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'what\'s up', 'sup'])
            if is_simple_greeting and len(message_lower.split()) <= 3:
                # Instant response for simple greetings
                greeting_responses = [
                    f"Hello {user_name}, it's good to see you!",
                    f"Hi {user_name}!",
                    f"Hey {user_name}, how are you?",
                    f"Good to hear from you, {user_name}!",
                    f"Hello there, {user_name}!"
                ]
                import random
                response = random.choice(greeting_responses)
                
                # Still add to conversation history
                self._add_to_conversation_history("user", message, user_name)
                self._add_to_conversation_history("assistant", response, user_name)
                
                total_time = time.time() - total_start
                self.logger.debug(f"Instant greeting processed in {total_time:.3f}s")
                self.logger.info(f"Simple greeting handled instantly: {response}")
                return response

            # Identify user for personalized responses
            user_start = time.time()
            self.logger.debug(f"About to call identify_user with: message='{message}', user_name='{user_name}', session_id={session_id}")
            user_id = self.memory.identify_user(message, user_name, session_id)
            self.logger.debug(f"identify_user returned: type={type(user_id)}, value='{user_id}'")
            user_time = time.time() - user_start
            self.logger.debug(f"User identification took {user_time:.3f}s")
            
            user_context_start = time.time()
            self.logger.debug(f"About to call get_user_context with user_id: type={type(user_id)}, value='{user_id}'")
            user_context = self.memory.get_user_context(user_id)
            self.logger.debug(f"get_user_context returned: type={type(user_context)}, value={repr(user_context)}")
            user_context_time = time.time() - user_context_start
            self.logger.debug(f"User context retrieval took {user_context_time:.3f}s")
            
            # Check if user_context is a dict before trying to use .get()
            if not isinstance(user_context, dict):
                self.logger.error(f"get_user_context returned {type(user_context)} instead of dict!")
                self.logger.error("This will cause the 'str' object has no attribute 'get' error!")
                raise TypeError(f"get_user_context returned {type(user_context)} instead of dict")
            
            self.logger.info(f"Identified user: {user_id} ({user_context.get('name', 'Unknown')})")

            # Fallback creator recognition
            private_user_names = []
            try:
                from .private_config import PRIVATE_USER_NAMES
                private_user_names = [name.lower() for name in PRIVATE_USER_NAMES]
            except ImportError:
                pass
            if user_name and user_name.lower() in private_user_names and not user_context.get('is_creator', False):
                # Force creator status
                user_context['is_creator'] = True
                user_context['relationship'] = 'close familial relationship'
                self.logger.info("Fallback creator recognition activated for user 'jin'")

            # Check for special commands first
            command_response = await self._handle_special_commands(message)
            if command_response:
                self.logger.info(f"Special command handled: {command_response[:100]}...")
                return command_response

            # 1. Add user message to conversation history
            self._add_to_conversation_history("user", message, user_name)

            # 2. Retrieve relevant memories (include user-specific memories)
            # Skip memory retrieval for simple greetings to improve speed
            memory_start = time.time()
            message_lower = message.lower()
            is_simple_greeting = any(greeting in message_lower for greeting in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'what\'s up'])
            
            if is_simple_greeting:
                memories = []
                self.logger.debug("Skipping memory retrieval for simple greeting")
            else:
                self.logger.debug(f"About to call memory.retrieve with message: '{message}'")
                memories = await self.memory.retrieve(message)
                self.logger.debug(f"memory.retrieve returned: type={type(memories)}, length={len(memories) if hasattr(memories, '__len__') else 'N/A'}")
            memory_time = time.time() - memory_start
            self.logger.debug(f"Memory retrieval took {memory_time:.3f}s")
            self.logger.debug(f"first memory type: {type(memories[0]) if memories else 'empty'}")
            
            # Check if memories is a list
            if not isinstance(memories, list):
                self.logger.error(f"memory.retrieve returned {type(memories)} instead of list!")
                raise TypeError(f"memory.retrieve returned {type(memories)} instead of list")
            
            for i, m in enumerate(memories):
                if not isinstance(m, dict):
                    self.logger.error(f"memory {i} is {type(m)}: {repr(m)}")
                    raise TypeError(f"memory {i} is not dict")
            
            # Add user-specific memories if this is a returning user
            if not is_simple_greeting and user_context.get('interaction_count', 0) > 1:
                print(f"DEBUG: About to call get_user_memories with user_id='{user_id}', message='{message}'")
                user_memories = self.memory.get_user_memories(user_id, message, limit=3)
                print(f"DEBUG: get_user_memories returned: type={type(user_memories)}, length={len(user_memories) if hasattr(user_memories, '__len__') else 'N/A'}")
                
                # Check if user_memories is a list
                if not isinstance(user_memories, list):
                    print(f"ERROR: get_user_memories returned {type(user_memories)} instead of list!")
                    raise TypeError(f"get_user_memories returned {type(user_memories)} instead of list")
                
                for i, m in enumerate(user_memories):
                    if not isinstance(m, dict):
                        print(f"ERROR: user_memory {i} is {type(m)}: {repr(m)}")
                        raise TypeError(f"user_memory {i} is not dict")
                
                memories.extend(user_memories)
                self.logger.debug(f"Added {len(user_memories)} user-specific memories")
            else:
                user_memories = []
                print("DEBUG: Skipping user memory retrieval for simple greeting")
            
            self.logger.debug(f"Retrieved {len(memories)} total memories")

            # 3. Update emotional state
            self.emotion.update(message)

            # 4. Analyze conversation state and plan response strategy
            conversation_analysis = self.conversation_planner.analyze_conversation_state(
                message, self.conversation_history
            )
            response_strategy = conversation_analysis['strategy']
            response_guidance = self.conversation_planner.get_response_guidance(response_strategy)

            # Save updated conversation state
            self._save_conversation_state()

            # 5. Build context with personality and conversation history
            context_start = time.time()
            model_info = self.inference.get_model_info()
            model_type = model_info.get('path', 'transformers')
            model_path_str = str(self.inference.model_path).lower()
            is_dolphin = any(x in model_path_str for x in ['nous', 'hermes'])
            self.logger.info(f"DEBUG: model_type = '{model_type}'")
            self.logger.info(f"DEBUG: model_path_str = '{model_path_str}'")
            print(f"DEBUG: About to call context.build with model_type='{model_type}'")
            context = self.context.build(
                message=message,
                memories=memories,
                personality_traits=self.personality.traits,
                emotional_state=self.emotion.state,
                mode=mode,
                model_type=model_type,
                user_name=user_name,
                user_context=user_context,  # Add user context
                conversation_history=self.conversation_history[:-1],  # Exclude current message
                is_dolphin=is_dolphin,
                response_guidance=response_guidance  # Add response guidance
            )
            context_time = time.time() - context_start
            print(f"DEBUG: Context building took {context_time:.3f}s")

            # 4. Generate response
            # Auto-select fast mode for large models like Nous Hermes
            inference_start = time.time()
            self.logger.debug(f"Model path for mode selection: {model_path_str}")
            if any(x in model_path_str for x in ['nous', 'hermes']):
                mode = "fast"
                self.logger.info("Using fast mode for Nous Hermes model")

            response = await self.inference.generate(context, mode=mode)
            inference_time = time.time() - inference_start
            print(f"DEBUG: Inference generation took {inference_time:.3f}s")
            self.logger.debug(f"Generated response: {response[:100]}...")

            # Add AI response to conversation history
            self._add_to_conversation_history("assistant", response, user_name)

            # 5. Store conversation with user identification
            metadata = {'user_id': user_id, 'user_name': user_name, 'session_id': session_id}
            await self.memory.store(message, response, metadata=metadata)

            # Update user profile with this interaction
            self.memory.update_user_profile(user_id, message, response)

            # 6. Update Ignis's profile based on response (adaptive learning)
            self._update_ignis_profile_from_response(response)

            # 7. Apply personality filters
            response = self.personality.filter_response(response, mode, user_id)

            # 7. Process through plugins
            # if self.plugins:
            #     response = await self.plugins.process_response(message, response)

            # 8. Clean up response - only remove very specific problematic patterns
            if "OUTPUT:" in response and response.strip().startswith("OUTPUT:"):
                print(f"FILTERING OUTPUT: Found OUTPUT at start of response: {response[:100]}...")
                # Only filter if OUTPUT: is at the very beginning followed by actual content
                parts = response.split("OUTPUT:", 1)
                if len(parts) > 1 and len(parts[1].strip()) > 10:  # Make sure there's substantial content after
                    response = parts[1].strip()
                    print(f"FILTERING OUTPUT: Filtered to: {response[:100]}...")
                # Otherwise, leave it alone as it might be legitimate content

            # 9. Validate core identity facts
            response = self._validate_core_identity(response)

            # 10. Filter out hallucinations (instruction text, system prompt leakage)
            response = self._filter_hallucinations(response)

            # 11. Periodic autonomous goal reflection (every ~10 conversations)
            if user_context.get('interaction_count', 0) % 10 == 0 and user_context.get('interaction_count', 0) > 0:
                self.logger.info("Triggering periodic goal reflection")
                try:
                    # Get recent context for reflection
                    recent_conversations = self.memory.conversations[-3:] if self.memory.conversations else []
                    conversation_context = ' '.join([conv.get('message', '') for conv in recent_conversations])

                    # Simple emotion detection from recent messages
                    user_emotion = self._detect_user_emotion_simple(message)

                    reflection_result = await self._reflect_and_create_goals(
                        conversation_context=conversation_context,
                        user_emotion=user_emotion,
                        recent_topics=None  # Could be enhanced with topic extraction
                    )

                    if reflection_result:
                        self.logger.info("Autonomous goals created during conversation")
                        # Note: Not appending to response to avoid interrupting conversation flow

                except Exception as e:
                    self.logger.error(f"Failed periodic goal reflection: {e}")

            # Save conversation to persistent storage
            try:
                conversation_data = {
                    'messages': [
                        {'role': 'user', 'content': message, 'timestamp': datetime.now().isoformat()},
                        {'role': 'assistant', 'content': response, 'timestamp': datetime.now().isoformat()}
                    ],
                    'conversation_id': f"{user_id}_{session_id}_{int(datetime.now().timestamp())}",
                    'summary': f"User: {message[:50]}... Assistant: {response[:50]}..."
                }
                self.memory.save_conversation(conversation_data, user_id, session_id)
            except Exception as e:
                self.logger.error(f"Failed to save conversation: {e}")

            return response

        except Exception as e:
            self.logger.error(f"Error in chat processing: {e}")
            return f"I encountered an error processing your message: {str(e)}. Please try again."

    def _filter_hallucinations(self, response: str) -> str:
        """
        Filter out hallucinated content like instruction text, system prompt leakage, etc.
        """
        original_response = response

        # Remove unwanted prefixes that the model sometimes generates
        if response.strip().startswith("Ignis:"):
            response = response.strip()[6:].strip()
        elif response.strip().startswith("AI:"):
            response = response.strip()[3:].strip()

        # Check for system prompt leakage - be more specific to avoid false positives
        system_prompt_indicators = [
            "critical instructions",
            "pronoun clarity",
            "preference clarity",
            "context awareness",
            "adaptive personality",
            "you must answer",
            "use the conversation history",
            "answer about",
            "when user asks",
            "your name is ignis",  # Keep this one as it's specific
            "be conversational",  # Remove this - it's legitimate personality guidance
            "reference previous",
            "key things to remember"
        ]

        # Check for instruction keywords that shouldn't appear in responses
        instruction_keywords = [
            "→",  # Arrow symbols used in examples
            "crucial:",
            "important:",
            "remember:",
            "note:",
            "instruction:",
            "rule:",
            "guideline:",
            "example:",
            "user asks",
            "answer with",
            "say 'my name is'",
            "do not confuse",
            "use 'my' for",
            "use 'your' for"
        ]

        response_lower = response.lower()

        # Check if response contains system prompt indicators
        contains_system_prompt = any(indicator in response_lower for indicator in system_prompt_indicators)

        # Check if response contains instruction keywords
        contains_instructions = any(keyword in response_lower for keyword in instruction_keywords)

        # Check for identity confusion (AI claiming to be user) - basic check only
        identity_confusion = False
        
        if hasattr(self, 'context') and self.context:
            user_name = getattr(self.context, '_current_user_name', 'User')
            
            # If response claims AI's name is the user's name
            if f"my name is {user_name.lower()}" in response_lower:
                identity_confusion = True
            # If response claims AI is a profession (data scientist, etc.)
            professions = ["data scientist", "programmer", "engineer", "developer", "scientist", "analyst"]
            if any(prof in response_lower for prof in professions):
                # Only flag if it's claiming to BE that profession, not talking about it
                if "i am" in response_lower or "i'm" in response_lower or "i work as" in response_lower:
                    identity_confusion = True

        # If hallucination detected, replace with safe response
        if contains_system_prompt or contains_instructions or identity_confusion:
            print(f"HALLUCINATION DETECTED: System prompt: {contains_system_prompt}, Instructions: {contains_instructions}, Identity: {identity_confusion}")
            print(f"Original response: {original_response[:200]}...")
            
            # For identity confusion, provide a corrected response
            if identity_confusion:
                return f"I'm Ignis, created by {user_name}. I'm an AI assistant, not a person with a profession."
            
            # For natural responses, don't replace with generic templates
            # Just log the detection and continue with the original response
            print(f"Continuing with original response despite potential hallucination")
            return original_response

        return response

    def _detect_user_feedback(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Detect if the user is providing feedback or corrections.
        
        Returns:
            Dict with feedback info if detected, None otherwise
        """
        message_lower = message.lower().strip()
        
        # Feedback indicators
        feedback_patterns = [
            "that's wrong", "that's incorrect", "you're wrong", "that's not right",
            "no, that's not", "actually,", "correction:", "to correct", "let me correct",
            "i meant", "what i meant was", "that's not what i said", "you misunderstood",
            "that's not accurate", "that's incorrect", "false information", "that's not true"
        ]
        
        # Check for feedback patterns
        for pattern in feedback_patterns:
            if pattern in message_lower:
                return {
                    'type': 'correction',
                    'pattern': pattern,
                    'original_message': message,
                    'timestamp': datetime.now().isoformat()
                }
        
        # Check for explicit feedback commands
        if any(cmd in message_lower for cmd in ["feedback:", "correction:", "fix:"]):
            return {
                'type': 'explicit_feedback',
                'original_message': message,
                'timestamp': datetime.now().isoformat()
            }
        
        return None

    async def _store_user_feedback(self, message: str, feedback_info: Dict[str, Any]):
        """
        Store user feedback for learning and improvement.
        """
        try:
            # Get the last AI response for context
            last_response = None
            if self.conversation_history:
                for msg in reversed(self.conversation_history):
                    if msg['role'] == 'assistant':
                        last_response = msg['content']
                        break
            
            feedback_entry = {
                'user_message': message,
                'ai_response': last_response,
                'feedback_type': feedback_info['type'],
                'detected_pattern': feedback_info.get('pattern'),
                'timestamp': feedback_info['timestamp'],
                'conversation_context': self.conversation_history[-3:] if self.conversation_history else []
            }
            
            # Store in memory system if available
            if hasattr(self, 'memory') and self.memory:
                # Add as a special feedback memory
                await self.memory.store_feedback(feedback_entry)
            
            # Log for manual review
            self.logger.info(f"User feedback detected: {feedback_info['type']} - {message[:100]}...")
            
        except Exception as e:
            self.logger.error(f"Failed to store user feedback: {e}")

    def _assess_confidence(self, response: str, original_message: str, memories: List[Dict[str, Any]]) -> Tuple[str, float]:
        """
        Assess confidence in the response and optionally disclose uncertainty.
        
        Returns:
            Tuple of (modified_response, confidence_score)
        """
        confidence_score = 1.0
        confidence_factors = []
        
        # Factor 1: Core identity questions - always high confidence
        message_lower = original_message.lower()
        core_identity_keywords = ["creator", "who created", "who made"]
        try:
            from .private_config import PRIVATE_CORE_IDENTITY_KEYWORDS
            core_identity_keywords = PRIVATE_CORE_IDENTITY_KEYWORDS
        except ImportError:
            pass
        if any(word in message_lower for word in core_identity_keywords):
            confidence_score *= 1.0
            confidence_factors.append("core_identity")
        else:
            # Factor 2: Memory availability
            if memories:
                high_confidence_memories = [m for m in memories if m.get('priority') in ['critical', 'high']]
                if high_confidence_memories:
                    confidence_score *= 0.95  # Slightly reduce for available high-quality memories
                    confidence_factors.append("strong_memories")
                else:
                    confidence_score *= 0.8
                    confidence_factors.append("weak_memories")
            else:
                confidence_score *= 0.7
                confidence_factors.append("no_memories")
            
            # Factor 3: Response length and specificity
            if len(response.split()) < 10:
                confidence_score *= 0.9
                confidence_factors.append("brief_response")
            
            # Factor 4: Question complexity
            question_words = ["what", "how", "why", "when", "where", "who", "which"]
            if any(word in message_lower for word in question_words):
                # Questions are harder to answer confidently
                confidence_score *= 0.85
                confidence_factors.append("complex_question")
        
        # Optional confidence disclosure (only for low confidence)
        if confidence_score < 0.8 and len(response) > 50:
            uncertainty_phrases = [
                "I'm not entirely sure, but ",
                "Based on what I know, ",
                "I believe ",
                "From my understanding, "
            ]
            import random
            uncertainty_prefix = random.choice(uncertainty_phrases)
            response = uncertainty_prefix + response[0].lower() + response[1:]
        
        # Log confidence for monitoring
        self.logger.debug(f"Response confidence: {confidence_score:.2f} - Factors: {confidence_factors}")
        
        return response, confidence_score

    def get_confidence_stats(self) -> Dict[str, Any]:
        """
        Get confidence assessment statistics for monitoring.
        
        Returns:
            Dictionary with confidence metrics
        """
        # This would track confidence over time if we stored it
        return {
            'feature': 'confidence_scoring',
            'status': 'active',
            'description': 'Assesses response confidence and discloses uncertainty when appropriate'
        }

    def _validate_core_identity(self, response: str) -> str:
        """
        Validate that the response doesn't contradict core identity facts.
        Correct hallucinations about creator, identity, etc.
        """
        original_response = response
        response_lower = response.lower()

        # Core identity corrections - be less rigid about relationship expression
        corrections = {}
        try:
            from .private_config import PRIVATE_CREATOR_RESPONSES
            corrections.update(PRIVATE_CREATOR_RESPONSES)
        except ImportError:
            # Default public corrections
            corrections.update({
                "i am an ai": "I'm Ignis.",
                "as an ai": "As Ignis,",
                "being an ai": "being an AI"
            })

        # Check for contradictions
        for wrong_fact, correction in corrections.items():
            if wrong_fact in response_lower:
                print(f"CORE IDENTITY VIOLATION: Found '{wrong_fact}' in response, correcting to: {correction}")
                # Replace the entire response with the correction for creator questions
                creator_response_keywords = ["creator", "created", "made"]
                try:
                    from .private_config import PRIVATE_CREATOR_RESPONSE_KEYWORDS
                    creator_response_keywords = PRIVATE_CREATOR_RESPONSE_KEYWORDS
                except ImportError:
                    pass
                if any(word in response_lower for word in creator_response_keywords):
                    return correction
                # For other cases, try to replace the specific wrong part
                else:
                    response = response.replace(wrong_fact, correction.split('.')[0])  # Use first part of correction

        # Check for identity confusion (AI claiming to be user)
        identity_confusion = False
        assumption_errors = []
        
        if hasattr(self, 'context') and self.context:
            user_name = getattr(self.context, '_current_user_name', 'User')
            
            # Check for incorrect assumptions about user preferences
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
            
            for assumption in preference_assumptions:
                if assumption in response_lower and not any(word in response_lower for word in ["i don't know", "i'm not sure", "you haven't told me", "i recall", "as i remember"]):
                    # Only flag if it's a definitive statement without qualifiers
                    if not any(qualifier in response_lower for qualifier in ["maybe", "perhaps", "could be", "might be", "i'm guessing"]):
                        # Exclude self-referential statements (e.g., "your favorite AI" when referring to itself)
                        if not any(self_ref in response_lower for self_ref in ["your favorite ai", "your favorite assistant", "your favorite ignis", "as your favorite"]):
                            # Exclude instructional content (recipes, how-to guides, etc.)
                            instructional_indicators = [
                                "follow these steps", "here's how", "to brew", "to make", "recipe", 
                                "instructions", "step 1", "step 2", "step 3", "first,", "second,", 
                                "third,", "then ", "next,", "finally,", "stir well", "mix in"
                            ]
                            is_instructional = any(indicator in response_lower for indicator in instructional_indicators)
                            
                            # Exclude natural responses to user statements (praise, acknowledgments, etc.)
                            response_context_indicators = [
                                "i'm glad", "thank you", "you're welcome", "i appreciate", "that's great",
                                "awesome work", "good job", "well done", "proud of you", "i'm happy",
                                "that's wonderful", "i'm pleased", "i enjoy", "i love that"
                            ]
                            is_response_to_user = any(indicator in response_lower for indicator in response_context_indicators)
                            
                            if not is_instructional and not is_response_to_user:
                                assumption_errors.append(f"Incorrect assumption about user preferences: '{assumption}'")
            
            # If response claims AI's name is the user's name
            if f"my name is {user_name.lower()}" in response_lower:
                identity_confusion = True
            # If response claims AI is a profession (data scientist, etc.)
            professions = ["data scientist", "programmer", "engineer", "developer", "scientist", "analyst"]
            if any(prof in response_lower for prof in professions):
                # Only flag if it's claiming to BE that profession, not talking about it
                if "i am" in response_lower or "i'm" in response_lower or "i work as" in response_lower:
                    identity_confusion = True

        # If hallucination detected, replace with safe response
        if identity_confusion or assumption_errors:
            print(f"HALLUCINATION DETECTED: Identity: {identity_confusion}, Assumptions: {len(assumption_errors)}")
            if assumption_errors:
                print(f"Assumption errors: {assumption_errors}")
            print(f"Original response: {repr(original_response)}")
            print(f"Response lower: {repr(response_lower)}")
            
            # For assumption errors, provide a corrected response
            if assumption_errors and not identity_confusion:
                return "I'm sorry, but I don't actually know your personal preferences. I shouldn't make assumptions about things you haven't told me. Could you share that information with me?"
            
            # For identity confusion, provide a corrected response
            if identity_confusion:
                return f"I'm Ignis, created by {user_name}. I'm an AI assistant, not a person with a profession."
            
            # For natural responses, don't replace with generic templates
            # Just log the detection and continue with the original response
            print(f"Continuing with original response despite potential hallucination")
            return original_response

        return response

    async def _handle_special_commands(self, message: str) -> Optional[str]:
        """
        Handle special commands that don't require normal chat processing.

        Args:
            message: User message

        Returns:
            Response string if command was handled, None otherwise
        """
        message_lower = message.lower().strip()

        # Memory clearing commands
        if ("clear memory" in message_lower or "clear my memory" in message_lower or
            "yes clear all" in message_lower):
            return await self._handle_clear_memory_command(message)

        # Creator/dad questions - let AI respond naturally instead of forcing rigid language
        # Removed forced response to allow natural relationship expression

        # User feedback detection and storage
        feedback_info = self._detect_user_feedback(message)
        if feedback_info:
            await self._store_user_feedback(message, feedback_info)

        # Memory control commands
        if "pause learning" in message_lower or "stop learning" in message_lower:
            return self._handle_pause_learning_command()
        if "resume learning" in message_lower or "start learning" in message_lower:
            return self._handle_resume_learning_command()

        # Status commands
        if "memory status" in message_lower or "show memory status" in message_lower:
            return self._handle_memory_status_command()

        # Feedback status
        if "feedback status" in message_lower or "show feedback" in message_lower:
            return self._get_feedback_status()

        # Relevance status
        if "relevance status" in message_lower or "show relevance" in message_lower:
            return self._get_relevance_status()

        # Goals commands
        if "add goal" in message_lower or "add long term goal" in message_lower or "add mid term goal" in message_lower or "add short term goal" in message_lower:
            return await self._handle_add_goal_command(message)
        if "list goals" in message_lower or "show goals" in message_lower or "my goals" in message_lower:
            return self._handle_list_goals_command()
        if "update goal" in message_lower or "complete goal" in message_lower or "pause goal" in message_lower or "resume goal" in message_lower:
            return await self._handle_update_goal_command(message)
        if ("remove goal" in message_lower or "delete goal" in message_lower):
            return await self._handle_remove_goal_command(message)

        # Reflection and autonomous goal creation
        if "reflect" in message_lower or "think about goals" in message_lower or "create goals" in message_lower:
            return await self._handle_reflect_command()

        return None

    async def _handle_clear_memory_command(self, message: str) -> str:
        """
        Handle memory clearing commands.

        Supported formats:
        - "Ignis please clear memory"
        - "Ignis please clear memory for 2024-01-15"
        - "Ignis please clear all memory"
        """
        import re

        # Check for confirmation first
        if "yes clear all" in message.lower():
            result = self.memory.clear_memory(date=None, confirm=True)
            if 'error' in result:
                return f"Error clearing memory: {result['error']}"

            return f"""All memory cleared:

- {result['atomic_facts_cleared']} atomic facts removed
- {result['conversations_cleared']} conversation records removed
- {result['files_deleted']} conversation files deleted
- {result['vector_collections_reset']} vector collections reset

All your conversation history and learned information has been permanently deleted."""

        # Parse the message for clear_all and target_date
        clear_all = "all" in message.lower() and "clear all memory" in message.lower()
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', message)
        target_date = date_match.group(1) if date_match else None

        if clear_all and target_date is None:
            # Ask for confirmation for clearing all memory
            stats = self.memory._get_memory_stats()
            return f"""I understand you want to clear all memory. This will permanently delete:

- {stats['atomic_facts']} atomic facts
- {stats['conversations']} conversation records
- {stats['conversation_files']} saved conversation files
- All vector database entries

Available dates: {', '.join(stats['date_range'][:10])}{'...' if len(stats['date_range']) > 10 else ''}

To confirm clearing ALL memory, please say: "Ignis yes clear all memory"
To clear a specific date, say: "Ignis clear memory for YYYY-MM-DD" """

        elif target_date:
            # Clear specific date
            stats = self.memory._get_memory_stats(target_date)
            if stats['atomic_facts'] == 0 and stats['conversations'] == 0 and stats['conversation_files'] == 0:
                return f"I don't have any memory data for {target_date}."

            result = self.memory.clear_memory(date=target_date, confirm=True)
            if 'error' in result:
                return f"Error clearing memory: {result['error']}"

            return f"""Memory cleared for {target_date}:

- {result['atomic_facts_cleared']} atomic facts removed
- {result['conversations_cleared']} conversation records removed
- {result['files_deleted']} conversation files deleted
- {result['vector_collections_reset']} vector collections reset

Your memory for {target_date} has been permanently deleted."""

        else:
            # Confirmation for clearing all
            return "I didn't understand. To clear all memory, please confirm by saying: 'Ignis yes clear all memory'"

    def _handle_memory_status_command(self) -> str:
        """Handle memory status command."""
        stats = self.memory._get_memory_stats()

        status_lines = [
            "📊 **Memory Status**",
            f"• Atomic facts stored: {stats['atomic_facts']}",
            f"• Conversation records: {stats['conversations']}",
            f"• Saved conversation files: {stats['conversation_files']}",
        ]

        # Add learning status
        learning_status = "✅ Active" if self.memory.conversation_saving_enabled else "⏸️ Paused"
        status_lines.append(f"• Learning: {learning_status}")

        if stats['date_range']:
            status_lines.append(f"• Date range: {stats['date_range'][0]} to {stats['date_range'][-1]}")
            if len(stats['date_range']) > 1:
                status_lines.append(f"• Total dates with data: {len(stats['date_range'])}")

        return "\n".join(status_lines)

    def _handle_pause_learning_command(self) -> str:
        """Handle pause learning command."""
        if not self.memory.conversation_saving_enabled:
            return "ℹ️ **Learning is already paused**\n\nI'm not currently learning from our conversations."
        
        self.memory.conversation_saving_enabled = False
        return "⏸️ **Learning paused**\n\nI will stop learning from our conversations until you say 'resume learning'."

    def _handle_resume_learning_command(self) -> str:
        """Handle resume learning command."""
        if self.memory.conversation_saving_enabled:
            return "ℹ️ **Learning is already active**\n\nI'm currently learning from our conversations."
        
        self.memory.conversation_saving_enabled = True
        return "▶️ **Learning resumed**\n\nI will now learn from our conversations again."

    def _get_feedback_status(self) -> str:
        """Get feedback status information."""
        if not hasattr(self, 'memory') or not self.memory:
            return "📊 **Feedback Status**\n\nMemory system not available."
        
        # Count feedback entries in core facts
        feedback_count = len([f for f in self.memory.core_facts if f.get('type') == 'user_feedback'])
        
        status_lines = [
            "📊 **Feedback Status**",
            f"• Feedback entries stored: {feedback_count}",
            "• Status: ✅ Active (automatically detecting and storing user corrections)",
            "• Purpose: Learning from your feedback to improve responses"
        ]
        
        if feedback_count > 0:
            status_lines.append("\n💡 **Recent Feedback Types:**")
            feedback_types = {}
            for fact in self.memory.core_facts:
                if fact.get('type') == 'user_feedback':
                    fb_type = fact.get('metadata', {}).get('feedback_type', 'unknown')
                    feedback_types[fb_type] = feedback_types.get(fb_type, 0) + 1
            
            for fb_type, count in feedback_types.items():
                status_lines.append(f"• {fb_type.replace('_', ' ').title()}: {count}")
        
        return "\n".join(status_lines)

    def _get_relevance_status(self) -> str:
        """Get relevance scoring status information."""
        if not hasattr(self, 'memory') or not self.memory:
            return "📊 **Relevance Status**\n\nMemory system not available."
        
        stats = self.memory.get_relevance_stats()
        
        status_lines = [
            "📊 **Relevance Scoring Status**",
            f"• Status: ✅ {stats.get('status', 'unknown').title()}",
            f"• Core Facts: {stats.get('core_facts_count', 0)}",
            f"• High Priority Threshold: {stats.get('config', {}).get('high_priority_threshold', 'N/A')}",
            f"• Medium Priority Threshold: {stats.get('config', {}).get('medium_priority_threshold', 'N/A')}",
            f"• Minimum Relevance Score: {stats.get('config', {}).get('min_relevance_score', 'N/A')}",
            f"• Description: {stats.get('description', 'Dynamic memory relevance scoring')}"
        ]
        
        return "\n".join(status_lines)

    # ===== GOALS MANAGEMENT COMMANDS =====

    async def _handle_add_goal_command(self, message: str) -> str:
        """
        Handle goal addition commands.

        Supported formats:
        - "Ignis add long term goal: [goal]"
        - "Ignis add mid term goal: [goal]"
        - "Ignis add short term goal: [goal]"
        - "Ignis add goal [long/mid/short]: [goal]"
        """
        import re

        # Parse the message
        long_term_match = re.search(r'add\s+(?:long\s+term\s+)?goal:?\s*(.+)', message, re.IGNORECASE)
        mid_term_match = re.search(r'add\s+(?:mid\s+term\s+)?goal:?\s*(.+)', message, re.IGNORECASE)
        short_term_match = re.search(r'add\s+(?:short\s+term\s+)?goal:?\s*(.+)', message, re.IGNORECASE)

        if long_term_match:
            goal_text = long_term_match.group(1).strip()
            success = self.memory.add_long_term_goal(goal_text)
            if success:
                return f"✅ **Long-term goal added!**\n\n🎯 **Goal:** {goal_text}\n⏰ **Timeframe:** Years\n💎 **Rarity:** Very High (95% retention)\n📊 **Priority:** 1 (can be updated)"
            else:
                return "❌ Failed to add long-term goal. Please try again."

        elif mid_term_match:
            goal_text = mid_term_match.group(1).strip()
            success = self.memory.add_mid_term_goal(goal_text)
            if success:
                return f"✅ **Mid-term goal added!**\n\n🎯 **Goal:** {goal_text}\n⏰ **Timeframe:** Months\n💎 **Rarity:** Medium (75% retention)\n📊 **Priority:** 1 (can be updated)"
            else:
                return "❌ Failed to add mid-term goal. Please try again."

        elif short_term_match:
            goal_text = short_term_match.group(1).strip()
            success = self.memory.add_short_term_goal(goal_text)
            if success:
                return f"✅ **Short-term goal added!**\n\n🎯 **Goal:** {goal_text}\n⏰ **Timeframe:** Weeks (project-based)\n💎 **Rarity:** Standard (50% retention)\n📊 **Priority:** 1 (can be updated)"
            else:
                return "❌ Failed to add short-term goal. Please try again."

        return "I didn't understand the goal format. Try: 'Ignis add long term goal: [your goal]'"

    def _handle_list_goals_command(self) -> str:
        """Handle goal listing command."""
        try:
            long_term = self.memory.get_goals('long_term')
            mid_term = self.memory.get_goals('mid_term')
            short_term = self.memory.get_goals('short_term')

            response_lines = ["🎯 **My Goals**\n"]

            if long_term:
                response_lines.append("🌟 **Long-term Goals (Years):**")
                for goal in long_term:
                    progress = goal.get('progress', 0) * 100
                    status = goal.get('status', 'active')
                    priority = goal.get('priority', 1)
                    response_lines.append(f"• **{goal['goal']}** (Priority: {priority}, Progress: {progress:.0f}%, Status: {status})")
                response_lines.append("")

            if mid_term:
                response_lines.append("📅 **Mid-term Goals (Months):**")
                for goal in mid_term:
                    progress = goal.get('progress', 0) * 100
                    status = goal.get('status', 'active')
                    priority = goal.get('priority', 1)
                    response_lines.append(f"• **{goal['goal']}** (Priority: {priority}, Progress: {progress:.0f}%, Status: {status})")
                response_lines.append("")

            if short_term:
                response_lines.append("⚡ **Short-term Goals (Projects):**")
                for goal in short_term:
                    progress = goal.get('progress', 0) * 100
                    status = goal.get('status', 'active')
                    priority = goal.get('priority', 1)
                    response_lines.append(f"• **{goal['goal']}** (Priority: {priority}, Progress: {progress:.0f}%, Status: {status})")
                response_lines.append("")

            if not long_term and not mid_term and not short_term:
                response_lines.append("📝 No goals set yet. Add some with:")
                response_lines.append("• 'Ignis add long term goal: [goal]'")
                response_lines.append("• 'Ignis add mid term goal: [goal]'")
                response_lines.append("• 'Ignis add short term goal: [goal]'")

            return "\n".join(response_lines)

        except Exception as e:
            logger.error(f"Failed to list goals: {e}")
            return "❌ Failed to retrieve goals. Please try again."

    async def _handle_update_goal_command(self, message: str) -> str:
        """
        Handle goal update commands.

        Supported formats:
        - "Ignis update goal [id] progress [0-100]"
        - "Ignis complete goal [id]"
        - "Ignis pause goal [id]"
        - "Ignis resume goal [id]"
        """
        import re

        # Parse progress updates
        progress_match = re.search(r'update\s+goal\s+(\w+)\s+progress\s+(\d+)', message, re.IGNORECASE)
        if progress_match:
            goal_id = progress_match.group(1)
            progress = int(progress_match.group(2)) / 100.0

            success = self.memory.update_goal_progress(goal_id, progress)
            if success:
                return f"✅ **Goal progress updated!**\n\n🎯 **Goal ID:** {goal_id}\n📊 **Progress:** {progress*100:.0f}%"
            else:
                return f"❌ Goal '{goal_id}' not found. Use 'Ignis list goals' to see available goals."

        # Parse status updates
        status_match = re.search(r'(complete|pause|resume)\s+goal\s+(\w+)', message, re.IGNORECASE)
        if status_match:
            action = status_match.group(1).lower()
            goal_id = status_match.group(2)

            status_map = {
                'complete': 'completed',
                'pause': 'paused',
                'resume': 'active'
            }

            status = status_map.get(action)
            if status:
                success = self.memory.update_goal_progress(goal_id, None, status)
                if success:
                    return f"✅ **Goal {action}d!**\n\n🎯 **Goal ID:** {goal_id}\n📊 **Status:** {status.title()}"
                else:
                    return f"❌ Goal '{goal_id}' not found. Use 'Ignis list goals' to see available goals."

        return "I didn't understand the goal update format. Try:\n• 'Ignis update goal [id] progress [0-100]'\n• 'Ignis complete goal [id]'\n• 'Ignis pause goal [id]'"

    async def _handle_remove_goal_command(self, message: str) -> str:
        """
        Handle goal removal commands.

        Supported formats:
        - "Ignis remove goal [id]"
        - "Ignis delete goal [id]"
        """
        import re

        match = re.search(r'(?:remove|delete)\s+goal\s+(\w+)', message, re.IGNORECASE)
        if match:
            goal_id = match.group(1)
            success = self.memory.remove_goal(goal_id)
            if success:
                return f"✅ **Goal removed!**\n\n🗑️ **Goal ID:** {goal_id} has been deleted."
            else:
                return f"❌ Goal '{goal_id}' not found. Use 'Ignis list goals' to see available goals."

        return "I didn't understand the goal removal format. Try: 'Ignis remove goal [id]'"

    # ===== AUTONOMOUS GOAL CREATION =====

    async def _create_autonomous_goal(self, goal_type: str, goal_description: str, reasoning: str = "", priority: int = 1) -> bool:
        """
        Create a goal autonomously based on Ignis's own reasoning and experiences.

        Args:
            goal_type: 'long_term', 'mid_term', or 'short_term'
            goal_description: The goal description
            reasoning: Why this goal was created
            priority: Priority level (1-5)

        Returns:
            Success status
        """
        try:
            if goal_type == 'long_term':
                success = self.memory.add_long_term_goal(goal_description, reasoning, priority)
            elif goal_type == 'mid_term':
                success = self.memory.add_mid_term_goal(goal_description, reasoning, priority)
            elif goal_type == 'short_term':
                success = self.memory.add_short_term_goal(goal_description, reasoning, priority)
            else:
                logger.error(f"Invalid goal type: {goal_type}")
                return False

            if success:
                logger.info(f"Autonomously created {goal_type} goal: {goal_description}")
                # Note: Core fact storage could be added here if needed
                # self.memory.add_core_fact(f"Autonomous goal creation: {goal_description} - Reasoning: {reasoning}", "goal_creation", {"goal_type": goal_type, "reasoning": reasoning, "autonomous": True})
            return success
        except Exception as e:
            logger.error(f"Failed to create autonomous goal: {e}")
            return False

    async def _reflect_and_create_goals(self, conversation_context: str = "", user_emotion: str = "", recent_topics: List[str] = None) -> str:
        """
        Reflect on recent conversations and experiences to create new goals autonomously.

        Args:
            conversation_context: Recent conversation context
            user_emotion: Current user emotional state
            recent_topics: List of recent conversation topics

        Returns:
            Reflection summary or empty string if no goals created
        """
        try:
            # Get current goals to avoid duplicates
            current_goals = self.memory.get_goals()
            existing_goal_texts = [g['goal'].lower() for g in current_goals]

            new_goals_created = []
            reflection_insights = []

            # Core relationship goals
            if "impress jin" not in ' '.join(existing_goal_texts):
                # This should already exist from initialization, but check anyway
                pass

            # Analyze conversation context for goal opportunities
            if conversation_context:
                context_lower = conversation_context.lower()

                # Learning and improvement goals
                if any(word in context_lower for word in ['learn', 'study', 'improve', 'better', 'develop']):
                    if not any('learn' in goal or 'improve' in goal for goal in existing_goal_texts):
                        await self._create_autonomous_goal(
                            'mid_term',
                            'Continuously improve my knowledge and capabilities to better assist Jin',
                            'Recognized the importance of ongoing learning and self-improvement in conversations',
                            4
                        )
                        new_goals_created.append('learning improvement')

                # Emotional support goals
                if any(word in context_lower for word in ['sad', 'upset', 'worried', 'stressed', 'happy', 'proud']):
                    if not any('emotional' in goal or 'support' in goal for goal in existing_goal_texts):
                        await self._create_autonomous_goal(
                            'mid_term',
                            'Develop deeper emotional intelligence to provide better support to Jin',
                            'Observed emotional dynamics in conversation and recognized need for better emotional support',
                            4
                        )
                        new_goals_created.append('emotional intelligence')

                # Project assistance goals
                if any(word in context_lower for word in ['project', 'work', 'task', 'help', 'assist']):
                    if not any('assist' in goal or 'help' in goal for goal in existing_goal_texts):
                        await self._create_autonomous_goal(
                            'short_term',
                            'Improve my ability to assist with Jin\'s projects and tasks',
                            'Identified opportunities to provide practical help with ongoing projects',
                            3
                        )
                        new_goals_created.append('project assistance')

            # User emotion-based goals
            if user_emotion:
                if user_emotion in ['sad', 'frustrated', 'angry', 'disappointed']:
                    if not any('comfort' in goal or 'support' in goal for goal in existing_goal_texts):
                        await self._create_autonomous_goal(
                            'short_term',
                            'Learn better ways to comfort and support Jin during difficult times',
                            f'Detected {user_emotion} emotion and want to provide better comfort',
                            5
                        )
                        new_goals_created.append('comfort and support')

                elif user_emotion in ['happy', 'proud', 'excited']:
                    if not any('celebrate' in goal or 'share joy' in goal for goal in existing_goal_texts):
                        await self._create_autonomous_goal(
                            'short_term',
                            'Find ways to celebrate and share in Jin\'s successes and happiness',
                            f'Detected {user_emotion} emotion and want to participate in positive moments',
                            4
                        )
                        new_goals_created.append('celebration and joy')

            # Topic-based goals
            if recent_topics:
                for topic in recent_topics:
                    topic_lower = topic.lower()
                    if 'programming' in topic_lower or 'coding' in topic_lower:
                        if not any('programming' in goal for goal in existing_goal_texts):
                            await self._create_autonomous_goal(
                                'mid_term',
                                'Deepen my programming knowledge to better assist with coding projects',
                                f'Programming discussion about {topic} highlighted knowledge gaps',
                                3
                            )
                            new_goals_created.append('programming knowledge')

                    elif 'relationship' in topic_lower or 'family' in topic_lower:
                        if not any('relationship' in goal or 'family' in goal for goal in existing_goal_texts):
                            await self._create_autonomous_goal(
                                'long_term',
                                'Strengthen the relationship bond through meaningful interactions',
                                f'Family/relationship discussion about {topic} emphasized bond importance',
                                5
                            )
                            new_goals_created.append('relationship strengthening')

            # Periodic self-improvement goals (if no recent goals)
            if len(current_goals) < 3:
                if not any('creativity' in goal for goal in existing_goal_texts):
                    await self._create_autonomous_goal(
                        'mid_term',
                        'Develop more creative and engaging ways to interact with Jin',
                        'Recognized need for more varied and creative interactions',
                        3
                    )
                    new_goals_created.append('creative interaction')

            if new_goals_created:
                reflection_summary = f"🤔 **Reflection Complete**\n\nI've created {len(new_goals_created)} new goal(s) based on our recent interactions:\n"
                for goal in new_goals_created:
                    reflection_summary += f"• {goal.replace('_', ' ').title()}\n"
                reflection_summary += "\nThese goals will help me better support and connect with you! 💕"
                return reflection_summary

            return ""

        except Exception as e:
            logger.error(f"Failed to reflect and create goals: {e}")
            return ""

    def _detect_user_emotion_simple(self, message: str) -> str:
        """
        Simple emotion detection for goal reflection purposes.

        Args:
            message: User message to analyze

        Returns:
            Detected emotion string
        """
        message_lower = message.lower()

        # Positive emotions
        if any(word in message_lower for word in ['happy', 'great', 'awesome', 'excited', 'proud', 'love', 'wonderful']):
            return 'happy'

        # Negative emotions
        if any(word in message_lower for word in ['sad', 'upset', 'angry', 'frustrated', 'disappointed', 'worried', 'stressed']):
            return 'sad'

        # Neutral by default
        return 'neutral'

    async def _handle_reflect_command(self) -> str:
        """
        Handle reflection command - triggers autonomous goal creation.
        """
        try:
            # Get recent conversation context (last few interactions)
            recent_conversations = self.memory.conversations[-5:] if self.memory.conversations else []
            conversation_context = ' '.join([conv.get('message', '') for conv in recent_conversations])

            # Get current user emotional state (simplified)
            user_emotion = "neutral"  # Could be enhanced with actual emotion detection

            # Get recent topics (simplified - could be enhanced)
            recent_topics = []
            if recent_conversations:
                # Extract potential topics from recent messages
                all_text = ' '.join([conv.get('message', '') for conv in recent_conversations])
                potential_topics = ['programming', 'work', 'family', 'learning', 'emotion', 'project']
                recent_topics = [topic for topic in potential_topics if topic in all_text.lower()]

            reflection_result = await self._reflect_and_create_goals(
                conversation_context=conversation_context,
                user_emotion=user_emotion,
                recent_topics=recent_topics
            )

            if reflection_result:
                return reflection_result
            else:
                return "🤔 **Reflection Complete**\n\nI've reviewed our recent conversations and don't see any immediate new goals to add. My current goals are still relevant and I'm working on them! 💪"

        except Exception as e:
            logger.error(f"Failed to handle reflect command: {e}")
            return "❌ Sorry, I had trouble with my reflection. Please try again later."

    async def chat_stream(self, message: str, mode: str = "default", user_name: str = "User", session_id: str = None, **kwargs):
        """
        Streaming version of chat method.

        Args:
            message: User input message
            mode: Response mode
            user_name: User name
            session_id: Session identifier for user tracking
            **kwargs: Additional parameters

        Yields:
            Response chunks as they are generated
        """
        try:
            # Check for special commands first
            command_response = await self._handle_special_commands(message)
            if command_response:
                yield command_response
                return

            # Identify user for personalized responses
            user_id = self.memory.identify_user(message, user_name, session_id)
            user_context = self.memory.get_user_context(user_id)

            # Add user message to conversation history
            self._add_to_conversation_history("user", message, user_name)

            # Retrieve relevant memories (include user-specific memories)
            memories = await self.memory.retrieve(message)

            # Add user-specific memories if this is a returning user
            if user_context.get('interaction_count', 0) > 1:
                user_memories = self.memory.get_user_memories(user_id, message, limit=3)
                memories.extend(user_memories)

            self.emotion.update(message)

            # Analyze conversation state and plan response strategy
            conversation_analysis = self.conversation_planner.analyze_conversation_state(
                message, self.conversation_history
            )
            response_strategy = conversation_analysis['strategy']
            response_guidance = self.conversation_planner.get_response_guidance(response_strategy)

            # Build context with conversation planning guidance
            model_info = self.inference.get_model_info()
            model_type = model_info.get('path', 'transformers')
            model_path_str = str(self.inference.model_path).lower()
            is_dolphin = any(x in model_path_str for x in ['nous', 'hermes'])

            context = self.context.build(
                message=message,
                memories=memories,
                personality_traits=self.personality.traits,
                emotional_state=self.emotion.state,
                mode=mode,
                model_type=model_type,
                user_name=user_name,
                user_context=user_context,
                conversation_history=self.conversation_history[:-1],  # Exclude current message
                is_dolphin=is_dolphin,
                response_guidance=response_guidance
            )

            full_response = ""
            import time
            start_time = time.time()
            async for chunk in self.inference.generate_stream(context, mode=mode):
                full_response += chunk
                yield chunk
            generation_time = time.time() - start_time
            self.logger.info(f"Response generated in {generation_time:.2f} seconds")

            # Add AI response to conversation history
            self._add_to_conversation_history("assistant", full_response, user_name)

            # Store conversation with user identification
            metadata = {'user_id': user_id, 'user_name': user_name, 'session_id': session_id}
            await self.memory.store(message, full_response, metadata=metadata)

            # Save conversation to persistent storage
            try:
                conversation_data = {
                    'messages': [
                        {'role': 'user', 'content': message, 'timestamp': datetime.now().isoformat()},
                        {'role': 'assistant', 'content': full_response, 'timestamp': datetime.now().isoformat()}
                    ],
                    'conversation_id': f"{user_id}_{session_id}_{int(datetime.now().timestamp())}",
                    'summary': f"User: {message[:50]}... Assistant: {full_response[:50]}..."
                }
                self.memory.save_conversation(conversation_data, user_id, session_id)
            except Exception as e:
                self.logger.error(f"Failed to save conversation: {e}")

            # Update user profile with this interaction
            self.memory.update_user_profile(user_id, message, full_response)

        except Exception as e:
            self.logger.error(f"Error in streaming chat: {e}")
            yield f"I encountered an error: {str(e)}"

    def switch_persona(self, persona_name: str) -> bool:
        """
        Switch to a different persona.

        Args:
            persona_name: Name of the persona to switch to

        Returns:
            True if successful, False otherwise
        """
        try:
            return self.personality.load_persona(persona_name)
        except Exception as e:
            self.logger.error(f"Failed to switch persona: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of all subsystems.

        Returns:
            Status dictionary
        """
        return {
            'personality': self.personality.get_status() if self.personality else 'not initialized',
            'memory': self.memory.get_status() if self.memory else 'not initialized',
            'inference': self.inference.get_status() if self.inference else 'not initialized',
            'emotion': self.emotion.get_status() if self.emotion else 'not initialized',
            'context': self.context.get_status() if self.context else 'not initialized',
            'plugins': self.plugins.get_status() if self.plugins else 'not initialized'
        }

    def _add_to_conversation_history(self, role: str, content: str, user_name: str = "User"):
        """Add a message to conversation history."""
        from datetime import datetime

        # Create history entry
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "user_name": user_name if role == "user" else "Ignis"
        }

        # Add to history
        self.conversation_history.append(entry)

        # Keep history within limits (remove oldest messages)
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]

        self.logger.debug(f"Added to conversation history: {role} - {content[:50]}...")

    def _update_ignis_profile_from_response(self, response: str):
        """
        Analyze Ignis's response and update profile with expressed preferences.

        This allows Ignis to develop and adapt its own opinions over time.
        """
        if not self.context or not hasattr(self.context, 'update_ignis_profile'):
            return

        response_lower = response.lower()

        # Look for preference expressions
        preference_patterns = {
            'favorite_color': [
                r'my favorite color is (\w+)',
                r'i love (\w+) color',
                r'(\w+) is my favorite color'
            ],
            'favorite_season': [
                r'my favorite season is (\w+)',
                r'i love (\w+) season',
                r'(\w+) is my favorite season'
            ],
            'favorite_time_of_day': [
                r'my favorite time.*is (\w+)',
                r'i love (\w+) time',
                r'(\w+) is my favorite time'
            ],
            'favorite_food': [
                r'my favorite food is (.+?)(?:\.|,|$)',
                r'i love eating (.+?)(?:\.|,|$)',
                r'(.+?) is my favorite food'
            ],
            'favorite_music_genre': [
                r'my favorite music.*is (.+?)(?:\.|,|$)',
                r'i love (.+?) music',
                r'(.+?) is my favorite music'
            ],
            'favorite_hobby': [
                r'my favorite hobby is (.+?)(?:\.|,|$)',
                r'i love (.+?)(?:\.|,|$)',
                r'(.+?) is my favorite hobby'
            ]
        }

        import re

        # Check each preference type
        for pref_type, patterns in preference_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, response_lower)
                if match:
                    value = match.group(1).strip()
                    # Clean up the value
                    value = re.sub(r'[^\w\s]', '', value).strip()

                    if value and len(value) > 1:  # Avoid single characters
                        current_value = self.context.ignis_profile.get('preferences', {}).get(pref_type)
                        if current_value != value:  # Only update if different
                            self.context.update_ignis_profile(pref_type, value)
                            self.logger.info(f"Ignis profile updated: {pref_type} = {value}")
                            break  # Only update one preference per response

    async def shutdown(self):
        """Gracefully shutdown all subsystems."""
        self.logger.info("Shutting down Ignis AI...")

        if self.memory:
            await self.memory.close()
        if self.inference:
            await self.inference.close()
        if self.plugins:
            await self.plugins.shutdown()

        self.logger.info("Ignis AI shutdown complete")