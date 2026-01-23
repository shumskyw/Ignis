"""
Conversation Continuity Debugger
Debugs session management, context preservation, and topic threading issues.
"""

import asyncio
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConversationContinuityDebugger:
    """
    Debugs conversation continuity issues in Ignis AI.
    """

    def __init__(self, data_path: str = "data"):
        self.data_path = Path(data_path)
        self.conversations_path = self.data_path / "conversations"
        self.sessions_path = self.conversations_path / "sessions"
        self.metadata_path = self.conversations_path / "metadata.json"

    def analyze_session_continuity(self, user_id: str = None) -> Dict[str, Any]:
        """
        Analyze session continuity for a user or all users.
        """
        results = {
            'total_sessions': 0,
            'sessions_with_gaps': 0,
            'average_session_gap': 0,
            'longest_gap_hours': 0,
            'continuity_score': 0,
            'issues': []
        }

        if not self.sessions_path.exists():
            results['issues'].append("No sessions directory found")
            return results

        sessions = []
        session_count = 0
        max_sessions = 10  # Limit for performance

        for session_file in self.sessions_path.glob("*.json"):
            if session_count >= max_sessions:
                break

            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    if not user_id or session_data.get('user_id') == user_id:
                        sessions.append(session_data)
                        session_count += 1
            except Exception as e:
                results['issues'].append(f"Error reading session {session_file.name}: {e}")
                continue

        if not sessions:
            results['issues'].append("No sessions found for user" if user_id else "No sessions found")
            return results

        # Sort sessions by start time
        sessions.sort(key=lambda x: x.get('start_time', ''))

        results['total_sessions'] = len(sessions)

        # Analyze gaps between sessions
        gaps = []
        prev_end = None

        for session in sessions:
            start_time = session.get('start_time')
            end_time = session.get('end_time')

            if start_time and prev_end:
                try:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    prev_end_dt = datetime.fromisoformat(prev_end.replace('Z', '+00:00'))
                    gap = (start_dt - prev_end_dt).total_seconds() / 3600  # hours
                    gaps.append(gap)

                    if gap > 24:  # More than 24 hours gap
                        results['sessions_with_gaps'] += 1
                        results['longest_gap_hours'] = max(results['longest_gap_hours'], gap)
                except:
                    pass

            if end_time:
                prev_end = end_time

        if gaps:
            results['average_session_gap'] = sum(gaps) / len(gaps)

        # Calculate continuity score (lower gaps = higher score)
        if results['average_session_gap'] > 0:
            # Score from 0-100, where 100 = perfect continuity (no gaps)
            results['continuity_score'] = max(0, 100 - (results['average_session_gap'] * 2))

        return results

    def check_context_preservation(self, session_id: str) -> Dict[str, Any]:
        """
        Check if context is properly preserved within a session.
        """
        results = {
            'session_id': session_id,
            'total_messages': 0,
            'context_references': 0,
            'topic_shifts': 0,
            'continuity_breaks': [],
            'preservation_score': 0
        }

        session_file = self.sessions_path / f"{session_id}.json"
        if not session_file.exists():
            results['continuity_breaks'].append("Session file not found")
            return results

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            messages = session_data.get('messages', [])
            results['total_messages'] = len(messages)

            # Analyze message flow for context references
            prev_topics = set()
            current_topics = set()

            for i, msg in enumerate(messages):
                content = msg.get('content', '').lower()

                # Simple topic detection (can be enhanced)
                if any(word in content for word in ['you', 'your', 'we', 'our', 'this', 'that', 'it']):
                    results['context_references'] += 1

                # Check for topic shifts (simplified)
                new_topics = set()
                if 'pokemon' in content:
                    new_topics.add('pokemon')
                if 'code' in content or 'programming' in content:
                    new_topics.add('programming')
                if 'memory' in content:
                    new_topics.add('memory')

                if prev_topics and not prev_topics.intersection(new_topics):
                    results['topic_shifts'] += 1

                prev_topics = new_topics

            # Calculate preservation score
            if results['total_messages'] > 0:
                ref_ratio = results['context_references'] / results['total_messages']
                shift_penalty = results['topic_shifts'] / max(1, results['total_messages'] / 10)
                results['preservation_score'] = min(100, (ref_ratio * 50) + (50 - shift_penalty * 10))

        except Exception as e:
            results['continuity_breaks'].append(f"Error analyzing session: {e}")

        return results

    def debug_topic_threading(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Debug topic threading across multiple sessions.
        """
        results = {
            'user_id': user_id,
            'time_period_days': days,
            'topics_tracked': {},
            'threading_score': 0,
            'issues': []
        }

        cutoff_date = datetime.now() - timedelta(days=days)

        # Collect all recent sessions for user
        sessions = []
        if self.sessions_path.exists():
            for session_file in self.sessions_path.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        if session_data.get('user_id') == user_id:
                            start_time = session_data.get('start_time', '')
                            if start_time:
                                try:
                                    session_date = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                    if session_date >= cutoff_date:
                                        sessions.append(session_data)
                                except:
                                    pass
                except Exception as e:
                    results['issues'].append(f"Error reading session: {e}")

        # Analyze topic flow across sessions
        topic_flow = defaultdict(list)

        for session in sessions:
            session_topics = set()
            messages = session.get('messages', [])

            for msg in messages:
                content = msg.get('content', '').lower()

                # Extract topics (simplified)
                if 'pokemon' in content:
                    session_topics.add('pokemon')
                if 'programming' in content or 'code' in content:
                    session_topics.add('programming')
                if 'memory' in content:
                    session_topics.add('memory')

            session_id = session.get('session_id', 'unknown')
            for topic in session_topics:
                topic_flow[topic].append(session_id)

        results['topics_tracked'] = dict(topic_flow)

        # Calculate threading score based on topic continuity
        total_topics = len(topic_flow)
        threaded_topics = sum(1 for sessions in topic_flow.values() if len(sessions) > 1)

        if total_topics > 0:
            results['threading_score'] = (threaded_topics / total_topics) * 100

        return results

async def run_continuity_analysis():
    """
    Run comprehensive conversation continuity analysis.
    """
    debugger = ConversationContinuityDebugger()

    print("🔍 Conversation Continuity Analysis")
    print("=" * 50)

    # Analyze overall continuity
    continuity = debugger.analyze_session_continuity()
    print(f"Total Sessions: {continuity['total_sessions']}")
    print(f"Sessions with Gaps: {continuity['sessions_with_gaps']}")
    print(".2f")
    print(".1f")
    print(".1f")
    print(f"Issues: {continuity['issues']}")

    print("\n📊 Sample Session Analysis:")
    # Analyze a recent session if available
    if continuity['total_sessions'] > 0:
        # Get a sample session ID (this would need to be implemented to get actual IDs)
        print("Session continuity analysis would show context preservation scores here")

    print("\n🧵 Topic Threading Analysis:")
    threading = debugger.debug_topic_threading("sample_user", 7)
    print(f"Topics Tracked: {len(threading['topics_tracked'])}")
    print(".1f")
    print(f"Issues: {threading['issues']}")

if __name__ == "__main__":
    asyncio.run(run_continuity_analysis())