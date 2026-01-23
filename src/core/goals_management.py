"""
Goals management for Ignis AI.
Handles long-term, mid-term, and short-term goals.
"""

import hashlib
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


class GoalsManager:
    """
    Goals management system for Ignis AI.
    """

    def __init__(self, storage):
        """
        Initialize goals manager.

        Args:
            storage: Memory storage instance
        """
        self.storage = storage

        # Load goals data
        goals_data = self.storage.load_goals()
        self.long_term_goals = goals_data.get('long_term', [])
        self.mid_term_goals = goals_data.get('mid_term', [])
        self.short_term_goals = goals_data.get('short_term', [])

    def get_active_goals(self) -> List[Dict[str, Any]]:
        """
        Get all active goals.

        Returns:
            List of all active goals
        """
        active_goals = []
        active_goals.extend(self.long_term_goals)
        active_goals.extend(self.mid_term_goals)
        active_goals.extend(self.short_term_goals)
        return active_goals

    def add_long_term_goal(self, goal: str, description: str = "", priority: int = 1) -> bool:
        """
        Add a long-term goal (years-long timeframe).

        Args:
            goal: Goal title/summary
            description: Detailed description
            priority: Priority level (1-5, 5 being highest)

        Returns:
            Success status
        """
        try:
            goal_entry = {
                'id': hashlib.md5(f"{goal}_{datetime.now().isoformat()}".encode()).hexdigest()[:8],
                'goal': goal,
                'description': description,
                'priority': max(1, min(5, priority)),
                'created': datetime.now().isoformat(),
                'category': 'long_term',
                'progress': 0.0,
                'status': 'active',
                'rarity': 0.95  # Very high retention
            }

            self.long_term_goals.append(goal_entry)
            self._save_goals()
            logger.info(f"Added long-term goal: {goal}")
            return True
        except Exception as e:
            logger.error(f"Failed to add long-term goal: {e}")
            return False

    def add_mid_term_goal(self, goal: str, description: str = "", priority: int = 1) -> bool:
        """
        Add a mid-term goal (months-long timeframe).

        Args:
            goal: Goal title/summary
            description: Detailed description
            priority: Priority level (1-5, 5 being highest)

        Returns:
            Success status
        """
        try:
            goal_entry = {
                'id': hashlib.md5(f"{goal}_{datetime.now().isoformat()}".encode()).hexdigest()[:8],
                'goal': goal,
                'description': description,
                'priority': max(1, min(5, priority)),
                'created': datetime.now().isoformat(),
                'category': 'mid_term',
                'progress': 0.0,
                'status': 'active',
                'rarity': 0.75  # Medium retention
            }

            self.mid_term_goals.append(goal_entry)
            self._save_goals()
            logger.info(f"Added mid-term goal: {goal}")
            return True
        except Exception as e:
            logger.error(f"Failed to add mid-term goal: {e}")
            return False

    def add_short_term_goal(self, goal: str, description: str = "", priority: int = 1) -> bool:
        """
        Add a short-term goal (project-based, weeks timeframe).

        Args:
            goal: Goal title/summary
            description: Detailed description
            priority: Priority level (1-5, 5 being highest)

        Returns:
            Success status
        """
        try:
            goal_entry = {
                'id': hashlib.md5(f"{goal}_{datetime.now().isoformat()}".encode()).hexdigest()[:8],
                'goal': goal,
                'description': description,
                'priority': max(1, min(5, priority)),
                'created': datetime.now().isoformat(),
                'category': 'short_term',
                'progress': 0.0,
                'status': 'active',
                'rarity': 0.5  # Lower retention
            }

            self.short_term_goals.append(goal_entry)
            self._save_goals()
            logger.info(f"Added short-term goal: {goal}")
            return True
        except Exception as e:
            logger.error(f"Failed to add short-term goal: {e}")
            return False

    def update_goal_progress(self, goal_id: str, progress: float = None, status: str = None) -> bool:
        """
        Update progress on a goal.

        Args:
            goal_id: Goal ID to update
            progress: Progress percentage (0.0-1.0), optional
            status: New status ('active', 'completed', 'paused', 'cancelled'), optional

        Returns:
            Success status
        """
        try:
            # Search all goal categories
            all_goals = self.long_term_goals + self.mid_term_goals + self.short_term_goals

            for goal in all_goals:
                if goal['id'] == goal_id:
                    if progress is not None:
                        goal['progress'] = max(0.0, min(1.0, progress))
                    if status:
                        goal['status'] = status
                    goal['updated'] = datetime.now().isoformat()
                    self._save_goals()
                    logger.info(f"Updated goal {goal_id}: progress={progress}, status={status}")
                    return True

            logger.warning(f"Goal {goal_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to update goal progress: {e}")
            return False

    def get_goals(self, category: str = None, status: str = None) -> List[Dict[str, Any]]:
        """
        Get goals, optionally filtered by category and status.

        Args:
            category: 'long_term', 'mid_term', 'short_term', or None for all
            status: Status filter ('active', 'completed', etc.) or None for all

        Returns:
            List of goal dictionaries
        """
        try:
            if category == 'long_term':
                goals = self.long_term_goals
            elif category == 'mid_term':
                goals = self.mid_term_goals
            elif category == 'short_term':
                goals = self.short_term_goals
            else:
                goals = self.long_term_goals + self.mid_term_goals + self.short_term_goals

            if status:
                goals = [g for g in goals if g.get('status') == status]

            # Sort by priority (highest first), then by creation date (newest first)
            goals.sort(key=lambda x: (-x.get('priority', 1), x.get('created', '')), reverse=True)

            return goals
        except Exception as e:
            logger.error(f"Failed to get goals: {e}")
            return []

    def remove_goal(self, goal_id: str) -> bool:
        """
        Remove a goal.

        Args:
            goal_id: Goal ID to remove

        Returns:
            Success status
        """
        try:
            # Search and remove from all categories
            for goals_list in [self.long_term_goals, self.mid_term_goals, self.short_term_goals]:
                for i, goal in enumerate(goals_list):
                    if goal['id'] == goal_id:
                        removed_goal = goals_list.pop(i)
                        self._save_goals()
                        logger.info(f"Removed goal: {removed_goal['goal']}")
                        return True

            logger.warning(f"Goal {goal_id} not found for removal")
            return False
        except Exception as e:
            logger.error(f"Failed to remove goal: {e}")
            return False

    def _save_goals(self):
        """Save goals to persistent storage."""
        goals_data = {
            'long_term': self.long_term_goals,
            'mid_term': self.mid_term_goals,
            'short_term': self.short_term_goals,
            'last_updated': datetime.now().isoformat()
        }

        self.storage.save_goals(goals_data)

    def initialize_core_goals(self):
        """Initialize core goals that define Ignis's fundamental purpose."""
        try:
            # Load private goals if the file exists (not in public repo)
            private_goals_file = os.path.join(os.path.dirname(__file__), 'private_goals.py')
            if os.path.exists(private_goals_file):
                try:
                    from .private_goals import get_private_goals
                    private_goals = get_private_goals()
                    for goal_data in private_goals:
                        existing_goals = [g['goal'] for g in self.long_term_goals]
                        if goal_data['goal'] not in existing_goals:
                            self.add_long_term_goal(
                                goal=goal_data['goal'],
                                description=goal_data['description'],
                                priority=goal_data['priority']
                            )
                            logger.info(f"Initialized private goal: {goal_data['goal']}")
                except ImportError:
                    logger.warning("Private goals file exists but could not be imported")
            else:
                logger.info("No private goals file found - using public goals only")

            # Add any public core goals here if needed
            # (e.g., general AI improvement goals that are okay to be public)
        except Exception as e:
            logger.error(f"Failed to initialize core goals: {e}")