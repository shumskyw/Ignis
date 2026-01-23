"""
High-Performance Memory System for ChatGPT-Level Competition
Optimized for speed, concurrency, and low latency.
"""

import asyncio
import hashlib
import json
import os
import threading
import time
from collections import OrderedDict, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..utils.logger import get_logger

logger = get_logger(__name__)


class HighPerformanceMemorySystem:
    """
    Optimized memory system for maximum speed and ChatGPT-level performance.
    """

    def __init__(self, config_path: str = "./configs"):
        self.config_path = Path(config_path)

        # Performance optimizations
        self.executor = ThreadPoolExecutor(max_workers=max(1, os.cpu_count() // 2))
        self.memory_cache = OrderedDict()  # LRU cache for memory operations
        self.cache_max_size = 500
        self.cache_lock = asyncio.Lock()

        # Async operation pools
        self.vector_search_pool = ThreadPoolExecutor(max_workers=2)
        self.file_io_pool = ThreadPoolExecutor(max_workers=4)

        # Performance monitoring
        self.operation_times = defaultdict(list)
        self.cache_hits = 0
        self.cache_misses = 0
        self.performance_lock = threading.Lock()

        # Load configuration
        self._load_config()

    def _load_config(self):
        """Load optimized memory configuration."""
        config_file = self.config_path / "memory_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.memory_config = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load memory config: {e}")
                self.memory_config = {}
        else:
            self.memory_config = {}

        # Set high-performance defaults
        self.memory_config.setdefault('retrieval_settings', {
            'short_term_weight': 0.7,
            'context_window': 15,  # Increased for better context
            'confidence_threshold': 0.3,  # Lower threshold for speed
            'max_results': 20
        })

        self.memory_config.setdefault('short_term', {
            'max_messages': 100,  # Increased capacity
            'max_age_hours': 48,  # Longer retention
            'cleanup_interval': 1800  # 30 minutes
        })

    async def initialize(self):
        """Initialize the high-performance memory system."""
        logger.info("🚀 Initializing High-Performance Memory System")

        # Initialize data structures
        self.conversations_path = Path("data/conversations")
        self.short_term_path = self.conversations_path / "short_term"
        self.sessions_path = self.conversations_path / "sessions"

        # Ensure directories exist
        for path in [self.conversations_path, self.short_term_path, self.sessions_path]:
            path.mkdir(parents=True, exist_ok=True)

        # Load existing data asynchronously
        await self._load_existing_data()

        logger.info("✅ High-Performance Memory System ready")

    async def _load_existing_data(self):
        """Load existing memory data asynchronously."""
        # This would load vector stores, conversation history, etc.
        # For now, just ensure basic structure
        pass

    @lru_cache(maxsize=100)
    def _get_cache_key(self, operation: str, *args) -> str:
        """Generate cache key for memory operations."""
        key_data = f"{operation}_{'_'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def retrieve_optimized(self, query: str, user_id: str = None,
                               limit: int = 15) -> List[Dict[str, Any]]:
        """
        High-performance memory retrieval optimized for speed.

        Args:
            query: Search query
            user_id: Optional user filter
            limit: Maximum results to return

        Returns:
            List of relevant memories
        """
        start_time = time.time()
        cache_key = self._get_cache_key("retrieve", query, user_id or "", limit)

        # Check cache first
        async with self.cache_lock:
            if cache_key in self.memory_cache:
                self.cache_hits += 1
                logger.debug("✅ Memory cache hit")
                return self.memory_cache[cache_key]

        self.cache_misses += 1

        try:
            # Parallel retrieval: short-term and long-term simultaneously
            short_term_task = self._retrieve_short_term_optimized(query, limit // 2)
            long_term_task = self._retrieve_long_term_optimized(query, limit // 2, user_id)

            short_term_results, long_term_results = await asyncio.gather(
                short_term_task, long_term_task
            )

            # Combine and rank results
            all_results = short_term_results + long_term_results
            all_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            results = all_results[:limit]

            # Fast confidence filtering
            filtered_results = []
            for memory in results:
                confidence = memory.get('confidence', 0.5)
                if confidence >= 0.3:  # Lower threshold for speed
                    filtered_results.append(memory)

            # Cache results
            async with self.cache_lock:
                self.memory_cache[cache_key] = filtered_results
                # LRU eviction
                if len(self.memory_cache) > self.cache_max_size:
                    self.memory_cache.popitem(last=False)

            # Update performance metrics
            self._update_performance_metrics("retrieve", time.time() - start_time)

            return filtered_results

        except Exception as e:
            logger.error(f"Memory retrieval failed: {e}")
            return []

    async def _retrieve_short_term_optimized(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Optimized short-term memory retrieval."""
        loop = asyncio.get_event_loop()

        def _sync_retrieve():
            results = []
            if not self.short_term_path.exists():
                return results

            # Read recent session files (limit to avoid excessive I/O)
            session_files = list(self.short_term_path.glob("*.json"))
            session_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            for session_file in session_files[:5]:  # Only check 5 most recent
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)

                    messages = session_data.get('messages', [])
                    for msg in messages[-20:]:  # Last 20 messages
                        content = msg.get('content', '').lower()
                        query_lower = query.lower()

                        # Fast relevance check
                        if query_lower in content or any(word in content for word in query_lower.split()[:3]):
                            results.append({
                                'type': 'short_term',
                                'content': msg.get('content', ''),
                                'relevance_score': 0.8 if query_lower in content else 0.6,
                                'confidence': 0.8,
                                'metadata': msg
                            })

                            if len(results) >= limit:
                                break

                    if len(results) >= limit:
                        break

                except Exception as e:
                    logger.debug(f"Error reading session {session_file}: {e}")

            return results[:limit]

        return await loop.run_in_executor(self.executor, _sync_retrieve)

    async def _retrieve_long_term_optimized(self, query: str, limit: int,
                                          user_id: str = None) -> List[Dict[str, Any]]:
        """Optimized long-term memory retrieval."""
        # Placeholder for vector search - in real implementation would use ChromaDB
        # For now, return empty list to focus on short-term optimization
        return []

    async def store_optimized(self, content: str, metadata: Dict[str, Any] = None,
                            user_id: str = None, session_id: str = None):
        """
        High-performance memory storage.

        Args:
            content: Content to store
            metadata: Additional metadata
            user_id: User identifier
            session_id: Session identifier
        """
        start_time = time.time()

        try:
            metadata = metadata or {}
            metadata.update({
                'user_id': user_id,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'content_hash': hashlib.md5(content.encode()).hexdigest()
            })

            # Async file I/O
            loop = asyncio.get_event_loop()

            def _sync_store():
                # Store in short-term memory
                session_file = self.short_term_path / f"{session_id or 'default'}.json"

                # Load existing data
                existing_data = {'messages': []}
                if session_file.exists():
                    try:
                        with open(session_file, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                    except:
                        pass

                # Add new message
                existing_data['messages'].append({
                    'content': content,
                    'metadata': metadata,
                    'timestamp': metadata['timestamp']
                })

                # Keep only recent messages (sliding window)
                max_messages = self.memory_config.get('short_term', {}).get('max_messages', 100)
                if len(existing_data['messages']) > max_messages:
                    existing_data['messages'] = existing_data['messages'][-max_messages:]

                # Save asynchronously
                with open(session_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=2, ensure_ascii=False)

            await loop.run_in_executor(self.file_io_pool, _sync_store)

            # Clear relevant cache entries
            await self._invalidate_cache()

            # Update performance metrics
            self._update_performance_metrics("store", time.time() - start_time)

        except Exception as e:
            logger.error(f"Memory storage failed: {e}")

    async def _invalidate_cache(self):
        """Invalidate cache entries that might be affected by new data."""
        async with self.cache_lock:
            # Simple invalidation - in production would be more selective
            self.memory_cache.clear()

    def _update_performance_metrics(self, operation: str, duration: float):
        """Update performance monitoring metrics."""
        with self.performance_lock:
            self.operation_times[operation].append(duration)
            # Keep only last 100 measurements
            if len(self.operation_times[operation]) > 100:
                self.operation_times[operation] = self.operation_times[operation][-100:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get memory system performance statistics."""
        with self.performance_lock:
            stats = {
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'cache_hit_rate': (self.cache_hits / max(self.cache_hits + self.cache_misses, 1)) * 100,
                'operation_stats': {}
            }

            for op, times in self.operation_times.items():
                if times:
                    stats['operation_stats'][op] = {
                        'count': len(times),
                        'avg_time': sum(times) / len(times),
                        'max_time': max(times),
                        'min_time': min(times)
                    }

            return stats

    async def cleanup_old_data(self):
        """Clean up old memory data for performance."""
        loop = asyncio.get_event_loop()

        def _sync_cleanup():
            max_age_hours = self.memory_config.get('short_term', {}).get('max_age_hours', 24)
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

            cleaned_files = 0
            removed_messages = 0

            if self.short_term_path.exists():
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
                                    msg_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                    if msg_time >= cutoff_time:
                                        filtered_messages.append(msg)
                                except:
                                    filtered_messages.append(msg)  # Keep if can't parse
                            else:
                                filtered_messages.append(msg)  # Keep if no timestamp

                        if len(filtered_messages) != original_count:
                            removed_messages += (original_count - len(filtered_messages))

                            if filtered_messages:
                                session_data['messages'] = filtered_messages
                                with open(session_file, 'w', encoding='utf-8') as f:
                                    json.dump(session_data, f, indent=2, ensure_ascii=False)
                            else:
                                # Remove empty files
                                session_file.unlink()
                                cleaned_files += 1

                    except Exception as e:
                        logger.debug(f"Error cleaning {session_file}: {e}")

            return cleaned_files, removed_messages

        cleaned_files, removed_messages = await loop.run_in_executor(self.executor, _sync_cleanup)

        if cleaned_files > 0 or removed_messages > 0:
            logger.info(f"🧹 Cleaned up {cleaned_files} files and {removed_messages} old messages")

        return cleaned_files, removed_messages

    async def shutdown(self):
        """Shutdown the memory system gracefully."""
        self.executor.shutdown(wait=True)
        self.vector_search_pool.shutdown(wait=True)
        self.file_io_pool.shutdown(wait=True)

        logger.info("🧹 High-Performance Memory System shut down")