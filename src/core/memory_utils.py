"""
Memory utilities for Ignis AI.
Contains helper functions, validation logic, and utility classes.
"""

import hashlib
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..utils.logger import get_logger

logger = get_logger(__name__)


class MemoryValidation:
    """
    Validation utilities for memory operations.
    """

    @staticmethod
    def validate_fact_with_rules(content: str, source: str, context_facts: List[str] = None) -> Dict[str, Any]:
        """
        Validate a fact using rule-based safeguards.

        Args:
            content: Fact content to validate
            source: Source of the fact
            context_facts: Recent context facts for validation

        Returns:
            Validation result dictionary
        """
        result = {
            'is_valid': True,
            'confidence': 1.0,
            'flags': [],
            'reasoning': []
        }

        content_lower = content.lower()

        # Rule 1: Hallucination Detection
        hallucination_patterns = [
            r'i (remember|recall) (that|when)',
            r'back (in|when) \d{4}',
            r'i used to',
            r'we (discussed|talked about|went over)',
            r'as i mentioned (before|earlier)'
        ]

        for pattern in hallucination_patterns:
            if re.search(pattern, content_lower):
                result['flags'].append('potential_hallucination')
                result['confidence'] *= 0.7
                result['reasoning'].append(f"Detected hallucination pattern: {pattern}")

        # Rule 2: Contradiction Detection
        if context_facts:
            contradictions = MemoryValidation._detect_contradictions(content, context_facts)
            if contradictions:
                result['flags'].append('potential_contradiction')
                result['confidence'] *= 0.8
                result['reasoning'].extend([f"Potential contradiction: {c}" for c in contradictions])

        # Rule 3: Source Reliability
        source_penalties = {
            'hallucination': 0.3,
            'ai_inferred': 0.8,
            'user_stated': 1.0,
            'system': 1.0
        }

        if source in source_penalties:
            penalty = source_penalties[source]
            if penalty < 1.0:
                result['flags'].append(f'source_penalty_{source}')
                result['confidence'] *= penalty
                result['reasoning'].append(f"Source reliability penalty: {source} ({penalty})")

        # Rule 4: Content Quality
        if len(content.split()) < 3:
            result['flags'].append('too_short')
            result['confidence'] *= 0.9
            result['reasoning'].append("Content too short for reliable fact")

        # Rule 5: Uncertain Language
        uncertain_words = ['maybe', 'perhaps', 'might', 'could', 'possibly', 'i think', 'i believe']
        if any(word in content_lower for word in uncertain_words):
            result['flags'].append('uncertain_language')
            result['confidence'] *= 0.95
            result['reasoning'].append("Contains uncertain language")

        # Determine final validity
        if result['confidence'] < 0.5:
            result['is_valid'] = False
            result['reasoning'].append(f"Overall confidence too low: {result['confidence']:.2f}")

        return result

    @staticmethod
    def _detect_contradictions(content: str, context_facts: List[str]) -> List[str]:
        """
        Detect contradictions between content and context facts.

        Args:
            content: New content to check
            context_facts: Existing context facts

        Returns:
            List of contradiction descriptions
        """
        contradictions = []
        content_lower = content.lower()

        for fact in context_facts:
            fact_lower = fact.lower()

            # Identity contradictions
            if ('my name is' in content_lower and 'my name is' in fact_lower):
                content_names = re.findall(r'my name is (\w+)', content_lower)
                fact_names = re.findall(r'my name is (\w+)', fact_lower)
                if content_names and fact_names and set(content_names) != set(fact_names):
                    contradictions.append(f"Name contradiction: {content_names} vs {fact_names}")

            # Relationship contradictions
            relationship_indicators = []
            try:
                from .private_config import PRIVATE_RELATIONSHIP_INDICATORS
                relationship_indicators.extend(PRIVATE_RELATIONSHIP_INDICATORS)
            except ImportError:
                # Generic fallback
                relationship_indicators = ['creator', 'made']
            content_rels = [w for w in relationship_indicators if w in content_lower]
            fact_rels = [w for w in relationship_indicators if w in fact_lower]

            if content_rels and fact_rels and set(content_rels) != set(fact_rels):
                contradictions.append(f"Relationship contradiction: {content_rels} vs {fact_rels}")

        return contradictions


class TextProcessing:
    """
    Text processing utilities for memory operations.
    """

    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """
        Extract keywords from text.

        Args:
            text: Input text

        Returns:
            List of keywords
        """
        # Simple keyword extraction - split and filter
        words = re.findall(r'\b\w+\b', text.lower())

        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall'}

        keywords = [word for word in words if len(word) > 2 and word not in stop_words]

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                unique_keywords.append(keyword)
                seen.add(keyword)

        return unique_keywords[:10]  # Limit to top 10

    @staticmethod
    def extract_entities(text: str) -> List[str]:
        """
        Extract named entities from text.

        Args:
            text: Input text

        Returns:
            List of extracted entities
        """
        entities = []

        # Simple regex-based extraction
        # Person names (capitalized words)
        person_matches = re.findall(r'\b[A-Z][a-z]+\b', text)
        entities.extend(person_matches)

        # Remove duplicates
        entities = list(set(entities))

        return entities

    @staticmethod
    def calculate_recency_score(timestamp_str: str, current_time: datetime = None) -> float:
        """
        Calculate recency score (0-1, higher = more recent).

        Args:
            timestamp_str: ISO timestamp string
            current_time: Current time (default: now)

        Returns:
            Recency score between 0.0 and 1.0
        """
        if current_time is None:
            current_time = datetime.now()

        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            hours_old = (current_time - timestamp).total_seconds() / 3600

            # Exponential decay: recent = high score, old = low score
            if hours_old < 1:
                return 1.0  # Less than 1 hour = perfect recency
            elif hours_old < 24:
                return 0.8  # Less than 1 day = high recency
            elif hours_old < 168:  # 1 week
                return 0.6
            elif hours_old < 720:  # 1 month
                return 0.4
            else:
                return 0.2  # Older than 1 month
        except (ValueError, TypeError):
            return 0.5  # Default if parsing fails

    @staticmethod
    def is_uncertain_language(content: str) -> bool:
        """
        Check if content contains uncertain language.

        Args:
            content: Text content

        Returns:
            True if uncertain language detected
        """
        uncertain_words = ['maybe', 'perhaps', 'might', 'could', 'possibly', 'i think', 'i believe']
        return any(word in content.lower() for word in uncertain_words)

    @staticmethod
    def contains_contradictions(content: str) -> bool:
        """
        Check if content contains contradictory statements.

        Args:
            content: Text content

        Returns:
            True if contradictions detected
        """
        contradiction_patterns = [
            r'i remember.*but.*not',
            r'you said.*but.*actually',
            r'previously.*now.*different'
        ]
        return any(re.search(pattern, content.lower()) for pattern in contradiction_patterns)

    @staticmethod
    def estimate_query_complexity(query: str) -> float:
        """
        Estimate query complexity (0-1 scale).

        Args:
            query: Query string

        Returns:
            Complexity score
        """
        complexity = 0.0

        # Length factor
        words = query.split()
        if len(words) > 10:
            complexity += 0.3
        elif len(words) > 5:
            complexity += 0.1

        # Question complexity
        question_words = ['what', 'when', 'where', 'why', 'how', 'who', 'which', 'whose']
        query_lower = query.lower()
        question_count = sum(1 for word in question_words if word in query_lower)
        complexity += min(question_count * 0.2, 0.4)

        # Multiple clauses
        clause_indicators = [',', ';', 'and', 'or', 'but']
        clause_count = sum(1 for indicator in clause_indicators if indicator in query_lower)
        complexity += min(clause_count * 0.1, 0.2)

        # Entity mentions
        entities = TextProcessing.extract_entities(query)
        complexity += min(len(entities) * 0.1, 0.2)

        return min(complexity, 1.0)


class RelevanceScoring:
    """
    Relevance scoring utilities for memory retrieval.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize relevance scorer.

        Args:
            config: Relevance configuration
        """
        self.config = config
        self.relevance_config = config.get('relevance_scoring', {})

    def calculate_relevance_score(self, memory: Dict[str, Any], query: str, current_time: datetime = None) -> float:
        """
        Calculate a comprehensive relevance score for a memory.

        Args:
            memory: Memory item to score
            query: Current query string
            current_time: Current timestamp

        Returns:
            Relevance score between 0.0 and 1.0
        """
        if current_time is None:
            current_time = datetime.now()

        base_score = 0.0
        factors = {}

        # Factor 1: Base priority
        priority_scores = {'critical': 1.0, 'high': 0.8, 'medium': 0.6, 'low': 0.4}
        base_priority = memory.get('metadata', {}).get('priority', 'medium')
        priority_score = priority_scores.get(base_priority, 0.5)
        base_score += priority_score * self.relevance_config.get('priority_weight', 0.3)
        factors['priority'] = priority_score

        # Factor 2: Semantic Similarity (simplified)
        semantic_score = self._calculate_semantic_similarity(query, memory.get('content', ''))
        base_score += semantic_score * self.relevance_config.get('semantic_weight', 0.4)
        factors['semantic'] = semantic_score

        # Factor 3: Recency
        memory_timestamp = memory.get('metadata', {}).get('timestamp')
        if memory_timestamp:
            try:
                if isinstance(memory_timestamp, str):
                    memory_time = datetime.fromisoformat(memory_timestamp.replace('Z', '+00:00'))
                else:
                    memory_time = memory_timestamp

                age_days = (current_time - memory_time).days
                max_age = self.relevance_config.get('max_age_days', 365)

                if age_days <= 0:
                    recency_score = 1.0
                elif age_days <= max_age:
                    recency_score = 1.0 - (age_days / max_age)
                else:
                    recency_score = 0.1

                base_score += recency_score * self.relevance_config.get('recency_weight', 0.2)
                factors['recency'] = recency_score
            except (ValueError, TypeError):
                base_score += 0.5 * self.relevance_config.get('recency_weight', 0.2)
                factors['recency'] = 0.5
        else:
            base_score += 0.5 * self.relevance_config.get('recency_weight', 0.2)
            factors['recency'] = 0.5

        # Factor 4: Confidence adjustment
        confidence = memory.get('metadata', {}).get('confidence', 0.8)
        confidence_multiplier = 0.8 + (confidence * 0.4)
        final_score = min(1.0, base_score * confidence_multiplier)

        # Store scoring factors for debugging
        memory['_relevance_factors'] = factors
        memory['_relevance_score'] = final_score

        return final_score

    def _calculate_semantic_similarity(self, query: str, content: str) -> float:
        """
        Calculate semantic similarity between query and content.

        Args:
            query: Query string
            content: Content string

        Returns:
            Similarity score
        """
        score = 0.0

        # Exact phrase matches
        if query in content or content in query:
            score += 0.8

        # Keyword overlap
        query_keywords = TextProcessing.extract_keywords(query)
        content_keywords = TextProcessing.extract_keywords(content)

        if query_keywords and content_keywords:
            overlap = len(set(query_keywords).intersection(set(content_keywords)))
            keyword_score = overlap / max(len(query_keywords), len(content_keywords))
            score += keyword_score * 0.6

        return min(score, 1.0)


def generate_fact_id(content: str, timestamp: str = None) -> str:
    """
    Generate a unique fact ID.

    Args:
        content: Fact content
        timestamp: Timestamp string

    Returns:
        Unique fact ID
    """
    if timestamp is None:
        timestamp = datetime.now().isoformat()

    hash_input = f"{content}{timestamp}"
    return hashlib.md5(hash_input.encode()).hexdigest()[:16]