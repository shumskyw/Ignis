"""
Short-Term Memory Debugger
Debugs and repairs issues with recent conversation context and message storage.
"""

import asyncio
import hashlib
import json
import os
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ShortTermMemoryDebugger:
    """
    Debugs short-term memory issues in Ignis AI.
    """

    def __init__(self, data_path: str = "data"):
        self.data_path = Path(data_path)
        self.conversations_path = self.data_path / "conversations"
        self.short_term_path = self.conversations_path / "short_term"
        self.config_path = Path("configs") / "memory_config.json"

        # Load memory configuration
        self.memory_config = self._load_memory_config()

    def _load_memory_config(self) -> Dict[str, Any]:
        """Load memory configuration."""
        default_config = {
            'short_term': {
                'max_messages': 50,
                'max_age_hours': 24,
                'cleanup_interval': 3600
            },
            'retrieval_settings': {
                'short_term_weight': 0.7,
                'context_window': 10
            }
        }

        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    for key, value in loaded_config.items():
                        if key in default_config:
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
            except Exception as e:
                print(f"Warning: Could not load memory config: {e}")

        return default_config

    def analyze_short_term_storage(self) -> Dict[str, Any]:
        """
        Analyze short-term memory storage health.
        """
        results = {
            'total_messages': 0,
            'sessions_count': 0,
            'average_messages_per_session': 0,
            'oldest_message_age_hours': 0,
            'newest_message_age_hours': 0,
            'storage_issues': [],
            'health_score': 0
        }

        if not self.short_term_path.exists():
            results['storage_issues'].append("Short-term storage directory not found")
            return results

        total_messages = 0
        sessions = []
        all_timestamps = []
        max_files = 5  # Limit for performance
        file_count = 0

        # Analyze each session file
        for session_file in self.short_term_path.glob("*.json"):
            if file_count >= max_files:
                break

            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                messages = session_data.get('messages', [])
                total_messages += len(messages)
                sessions.append(session_data)
                file_count += 1

                # Collect timestamps (limit to recent messages for speed)
                for msg in messages[-10:]:  # Only check last 10 messages per session
                    timestamp = msg.get('timestamp')
                    if timestamp:
                        try:
                            # Handle different timestamp formats
                            if isinstance(timestamp, str):
                                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            else:
                                dt = datetime.fromtimestamp(timestamp)
                            all_timestamps.append(dt)
                        except:
                            pass

            except Exception as e:
                results['storage_issues'].append(f"Error reading {session_file.name}: {e}")
                continue

        results['total_messages'] = total_messages
        results['sessions_count'] = len(sessions)

        if sessions:
            results['average_messages_per_session'] = total_messages / len(sessions)

        # Analyze message ages
        if all_timestamps:
            now = datetime.now()
            ages_hours = [(now - ts).total_seconds() / 3600 for ts in all_timestamps]

            results['oldest_message_age_hours'] = max(ages_hours)
            results['newest_message_age_hours'] = min(ages_hours)

            # Check for stale messages
            max_age = self.memory_config.get('short_term', {}).get('max_age_hours', 24)
            stale_count = sum(1 for age in ages_hours if age > max_age)
            if stale_count > 0:
                results['storage_issues'].append(f"{stale_count} messages older than {max_age} hours")

        # Check message limits
        max_messages = self.memory_config.get('short_term', {}).get('max_messages', 50)
        if total_messages > max_messages * len(sessions) * 1.5:  # Allow some overflow
            results['storage_issues'].append("Message count exceeds recommended limits")

        # Calculate health score
        issue_penalty = len(results['storage_issues']) * 10
        age_penalty = max(0, results['oldest_message_age_hours'] - 24) * 2
        results['health_score'] = max(0, 100 - issue_penalty - age_penalty)

        return results

    def debug_message_retrieval(self, query: str, user_id: str = None) -> Dict[str, Any]:
        """
        Debug short-term message retrieval logic.
        """
        results = {
            'query': query,
            'retrieved_messages': 0,
            'relevant_messages': 0,
            'retrieval_time_ms': 0,
            'relevance_score': 0,
            'issues': []
        }

        start_time = datetime.now()

        # Simulate retrieval logic (simplified)
        retrieved_messages = []

        if self.short_term_path.exists():
            for session_file in self.short_term_path.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)

                    if user_id and session_data.get('user_id') != user_id:
                        continue

                    messages = session_data.get('messages', [])

                    # Simple relevance check
                    for msg in messages[-10:]:  # Last 10 messages
                        content = msg.get('content', '').lower()
                        query_lower = query.lower()

                        # Check for keyword matches
                        if any(word in content for word in query_lower.split()):
                            retrieved_messages.append(msg)
                            results['retrieved_messages'] += 1

                            # Calculate relevance (simplified)
                            if query_lower in content:
                                results['relevant_messages'] += 1

                except Exception as e:
                    results['issues'].append(f"Error processing {session_file}: {e}")

        end_time = datetime.now()
        results['retrieval_time_ms'] = (end_time - start_time).total_seconds() * 1000

        # Calculate relevance score
        if results['retrieved_messages'] > 0:
            results['relevance_score'] = (results['relevant_messages'] / results['retrieved_messages']) * 100

        # Check for issues
        if results['retrieval_time_ms'] > 100:  # More than 100ms
            results['issues'].append(".1f")

        if results['relevance_score'] < 50:
            results['issues'].append(".1f")

        return results

    def check_context_consistency(self, session_id: str) -> Dict[str, Any]:
        """
        Check context consistency within a session.
        """
        results = {
            'session_id': session_id,
            'total_messages': 0,
            'context_breaks': 0,
            'temporal_gaps': 0,
            'consistency_score': 0,
            'issues': []
        }

        session_file = self.short_term_path / f"{session_id}.json"
        if not session_file.exists():
            results['issues'].append("Session file not found")
            return results

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            messages = session_data.get('messages', [])
            results['total_messages'] = len(messages)

            if len(messages) < 2:
                results['issues'].append("Insufficient messages for consistency analysis")
                return results

            # Check temporal consistency
            prev_timestamp = None
            for msg in messages:
                timestamp = msg.get('timestamp')
                if timestamp and prev_timestamp:
                    try:
                        if isinstance(timestamp, str):
                            curr_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        else:
                            curr_dt = datetime.fromtimestamp(timestamp)

                        if isinstance(prev_timestamp, str):
                            prev_dt = datetime.fromisoformat(prev_timestamp.replace('Z', '+00:00'))
                        else:
                            prev_dt = datetime.fromtimestamp(prev_timestamp)

                        gap_seconds = (curr_dt - prev_dt).total_seconds()
                        if gap_seconds < 0:  # Messages out of order
                            results['temporal_gaps'] += 1
                        elif gap_seconds > 3600:  # More than 1 hour gap
                            results['temporal_gaps'] += 1
                    except:
                        results['temporal_gaps'] += 1

                prev_timestamp = timestamp

            # Check context flow (simplified)
            prev_role = None
            for msg in messages:
                role = msg.get('role')
                if role == prev_role:
                    results['context_breaks'] += 1  # Consecutive messages from same role
                prev_role = role

            # Calculate consistency score
            break_penalty = results['context_breaks'] + results['temporal_gaps']
            if results['total_messages'] > 0:
                results['consistency_score'] = max(0, 100 - (break_penalty / results['total_messages']) * 100)

        except Exception as e:
            results['issues'].append(f"Error analyzing session: {e}")

        return results

    def repair_short_term_memory(self) -> Dict[str, Any]:
        """
        Attempt to repair common short-term memory issues.
        """
        results = {
            'repairs_attempted': 0,
            'repairs_successful': 0,
            'files_cleaned': 0,
            'messages_removed': 0,
            'issues_fixed': [],
            'remaining_issues': []
        }

        max_age_hours = self.memory_config.get('short_term', {}).get('max_age_hours', 24)
        max_messages = self.memory_config.get('short_term', {}).get('max_messages', 50)
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        if not self.short_term_path.exists():
            results['remaining_issues'].append("Short-term storage directory not found")
            return results

        # Clean up old sessions and messages
        for session_file in self.short_term_path.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                messages = session_data.get('messages', [])
                original_count = len(messages)

                # Remove old messages
                filtered_messages = []
                for msg in messages:
                    timestamp = msg.get('timestamp')
                    if timestamp:
                        try:
                            if isinstance(timestamp, str):
                                msg_dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            else:
                                msg_dt = datetime.fromtimestamp(timestamp)

                            if msg_dt >= cutoff_time:
                                filtered_messages.append(msg)
                        except:
                            # Keep messages with invalid timestamps
                            filtered_messages.append(msg)
                    else:
                        # Keep messages without timestamps
                        filtered_messages.append(msg)

                # Limit message count
                if len(filtered_messages) > max_messages:
                    filtered_messages = filtered_messages[-max_messages:]

                removed_count = original_count - len(filtered_messages)

                if removed_count > 0:
                    # Save cleaned session
                    session_data['messages'] = filtered_messages
                    with open(session_file, 'w', encoding='utf-8') as f:
                        json.dump(session_data, f, indent=2, ensure_ascii=False)

                    results['messages_removed'] += removed_count
                    results['repairs_attempted'] += 1
                    results['repairs_successful'] += 1
                    results['issues_fixed'].append(f"Cleaned {removed_count} old messages from {session_file.name}")

            except Exception as e:
                results['remaining_issues'].append(f"Error repairing {session_file}: {e}")

        # Remove empty session files
        for session_file in self.short_term_path.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                if not session_data.get('messages'):
                    session_file.unlink()
                    results['files_cleaned'] += 1
                    results['issues_fixed'].append(f"Removed empty session file {session_file.name}")

            except Exception as e:
                results['remaining_issues'].append(f"Error checking {session_file}: {e}")

        return results

    def create_short_term_health_report(self) -> str:
        """
        Generate a comprehensive short-term memory health report.
        """
        report = []
        report.append("🧠 Short-Term Memory Health Report")
        report.append("=" * 45)

        # Storage analysis
        storage = self.analyze_short_term_storage()
        report.append(f"\n💾 Storage Health: {storage['health_score']}/100")
        report.append(f"  Total Messages: {storage['total_messages']}")
        report.append(f"  Sessions: {storage['sessions_count']}")
        report.append(".1f")

        if storage['storage_issues']:
            report.append("  Issues:")
            for issue in storage['storage_issues']:
                report.append(f"    ⚠️  {issue}")

        # Retrieval test
        retrieval = self.debug_message_retrieval("test query")
        report.append(".1f")
        report.append(f"  Retrieved: {retrieval['retrieved_messages']} messages")
        report.append(".1f")

        if retrieval['issues']:
            report.append("  Issues:")
            for issue in retrieval['issues']:
                report.append(f"    ⚠️  {issue}")

        # Recommendations
        report.append("\n💡 Recommendations:")
        if storage['health_score'] < 70:
            report.append("  - Run repair_short_term_memory() to clean up old data")
        if retrieval['relevance_score'] < 60:
            report.append("  - Improve message retrieval algorithm")
        if storage['oldest_message_age_hours'] > 48:
            report.append("  - Configure shorter message retention time")

        return "\n".join(report)

async def run_short_term_memory_analysis():
    """
    Run comprehensive short-term memory analysis.
    """
    debugger = ShortTermMemoryDebugger()

    print("🧠 Short-Term Memory Analysis")
    print("=" * 40)

    # Analyze storage health
    storage = debugger.analyze_short_term_storage()
    print(f"Storage Health: {storage['health_score']}/100")
    print(f"Messages: {storage['total_messages']}, Sessions: {storage['sessions_count']}")
    print(".1f")

    if storage['storage_issues']:
        print("Issues found:")
        for issue in storage['storage_issues']:
            print(f"  ⚠️  {issue}")

    # Test retrieval
    retrieval = debugger.debug_message_retrieval("hello world")
    print("\nRetrieval Test:")
    print(f"  Query: '{retrieval['query']}'")
    print(f"  Retrieved: {retrieval['retrieved_messages']} messages")
    print(".1f")

    # Attempt repairs
    print("\n🔧 Attempting Repairs...")
    repairs = debugger.repair_short_term_memory()
    print(f"Repairs attempted: {repairs['repairs_attempted']}")
    print(f"Successful: {repairs['repairs_successful']}")
    print(f"Messages cleaned: {repairs['messages_removed']}")
    print(f"Files removed: {repairs['files_cleaned']}")

    if repairs['issues_fixed']:
        print("Fixed issues:")
        for fix in repairs['issues_fixed'][:3]:  # Show first 3
            print(f"  ✅ {fix}")

    # Generate full report
    report = debugger.create_short_term_health_report()
    print(f"\n{report}")

if __name__ == "__main__":
    asyncio.run(run_short_term_memory_analysis())