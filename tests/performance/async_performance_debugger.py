"""
Async Performance Debugger
Analyzes and optimizes async operations for better performance.
"""

import asyncio
import inspect
import os
import threading
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import psutil


class AsyncPerformanceDebugger:
    """
    Debugs and optimizes async performance in Ignis AI.
    """

    def __init__(self):
        self.operation_times = {}
        self.blocking_calls = []
        self.concurrency_metrics = {}
        self.memory_usage = {}
        self.is_monitoring = False
        self.monitor_thread = None

    def profile_async_operation(self, func: Callable) -> Callable:
        """
        Decorator to profile async operations.
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = tracemalloc.get_traced_memory()[0] if tracemalloc.is_tracing() else 0

            try:
                result = await func(*args, **kwargs)
                end_time = time.time()
                end_memory = tracemalloc.get_traced_memory()[0] if tracemalloc.is_tracing() else 0

                operation_name = f"{func.__name__}"
                duration = end_time - start_time
                memory_delta = end_memory - start_memory

                if operation_name not in self.operation_times:
                    self.operation_times[operation_name] = []

                self.operation_times[operation_name].append({
                    'duration': duration,
                    'memory_delta': memory_delta,
                    'timestamp': time.time(),
                    'args_count': len(args) + len(kwargs)
                })

                return result
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                print(f"⚠️  Async operation {func.__name__} failed after {duration:.3f}s: {e}")
                raise

        return wrapper

    def detect_blocking_calls(self, func: Callable) -> Callable:
        """
        Decorator to detect blocking calls in async functions.
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            loop = asyncio.get_running_loop()
            start_time = time.time()

            # Check for blocking operations
            original_call_soon = loop.call_soon
            blocking_detected = []

            def patched_call_soon(callback, *args, **kwargs):
                # This is a simplified detection - in practice you'd need more sophisticated analysis
                if hasattr(callback, '__name__') and 'block' in callback.__name__.lower():
                    blocking_detected.append(callback.__name__)
                return original_call_soon(callback, *args, **kwargs)

            loop.call_soon = patched_call_soon

            try:
                result = await func(*args, **kwargs)
                end_time = time.time()

                if blocking_detected:
                    self.blocking_calls.append({
                        'function': func.__name__,
                        'blocking_calls': blocking_detected,
                        'duration': end_time - start_time,
                        'timestamp': time.time()
                    })

                return result
            finally:
                loop.call_soon = original_call_soon

        return wrapper

    def start_performance_monitoring(self):
        """
        Start background performance monitoring.
        """
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_performance, daemon=True)
        self.monitor_thread.start()

    def stop_performance_monitoring(self):
        """
        Stop performance monitoring.
        """
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)

    def _monitor_performance(self):
        """
        Background performance monitoring.
        """
        process = psutil.Process(os.getpid())

        while self.is_monitoring:
            try:
                # CPU usage (non-blocking)
                cpu_percent = process.cpu_percent(interval=0.1)

                # Memory usage
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024

                # Thread count
                thread_count = process.num_threads()

                timestamp = time.time()
                # Don't try to access asyncio from thread - just monitor system resources
                self.concurrency_metrics[timestamp] = {
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb,
                    'thread_count': thread_count,
                    'active_tasks': 0  # Will be set from main thread
                }

                time.sleep(1)  # Monitor every second instead of 5

            except Exception as e:
                print(f"Performance monitoring error: {e}")
                break

    async def analyze_async_efficiency(self) -> Dict[str, Any]:
        """
        Analyze async operation efficiency.
        """
        results = {
            'operation_stats': {},
            'blocking_call_count': len(self.blocking_calls),
            'average_operation_time': 0,
            'slowest_operations': [],
            'memory_efficient_operations': [],
            'recommendations': []
        }

        # Analyze operation times
        total_time = 0
        total_operations = 0

        for op_name, times in self.operation_times.items():
            if not times:
                continue

            durations = [t['duration'] for t in times]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)

            results['operation_stats'][op_name] = {
                'count': len(times),
                'avg_duration': avg_duration,
                'max_duration': max_duration,
                'min_duration': min_duration,
                'total_time': sum(durations)
            }

            total_time += sum(durations)
            total_operations += len(times)

        if total_operations > 0:
            results['average_operation_time'] = total_time / total_operations

        # Find slowest operations
        all_ops = []
        for op_name, stats in results['operation_stats'].items():
            all_ops.append((op_name, stats['max_duration']))

        all_ops.sort(key=lambda x: x[1], reverse=True)
        results['slowest_operations'] = all_ops[:5]

        # Generate recommendations
        if results['blocking_call_count'] > 0:
            results['recommendations'].append(f"⚠️  {results['blocking_call_count']} blocking calls detected - consider using asyncio.run_in_executor()")

        if results['average_operation_time'] > 1.0:
            results['recommendations'].append("🐌 Average operation time > 1s - consider optimizing async operations")

        slow_ops = [op for op, time in results['slowest_operations'] if time > 2.0]
        if slow_ops:
            results['recommendations'].append(f"🐌 Slow operations detected: {', '.join(slow_ops[:3])}")

        return results

    async def optimize_memory_operations(self) -> Dict[str, Any]:
        """
        Analyze memory usage patterns and suggest optimizations.
        """
        results = {
            'memory_spikes': [],
            'high_memory_operations': [],
            'memory_efficiency_score': 0,
            'optimization_suggestions': []
        }

        # Analyze memory usage in operations
        for op_name, times in self.operation_times.items():
            memory_deltas = [t.get('memory_delta', 0) for t in times if 'memory_delta' in t]

            if memory_deltas:
                avg_memory = sum(memory_deltas) / len(memory_deltas)
                max_memory = max(memory_deltas)

                if max_memory > 50 * 1024 * 1024:  # 50MB spike
                    results['memory_spikes'].append({
                        'operation': op_name,
                        'max_memory_mb': max_memory / 1024 / 1024,
                        'avg_memory_mb': avg_memory / 1024 / 1024
                    })

                if avg_memory > 10 * 1024 * 1024:  # 10MB average
                    results['high_memory_operations'].append(op_name)

        # Calculate efficiency score
        total_spikes = len(results['memory_spikes'])
        total_high_mem_ops = len(results['high_memory_operations'])

        if total_spikes == 0 and total_high_mem_ops == 0:
            results['memory_efficiency_score'] = 100
        else:
            penalty = (total_spikes * 10) + (total_high_mem_ops * 5)
            results['memory_efficiency_score'] = max(0, 100 - penalty)

        # Generate suggestions
        if results['memory_spikes']:
            results['optimization_suggestions'].append("💾 Memory spikes detected - consider streaming large data or using generators")

        if results['high_memory_operations']:
            results['optimization_suggestions'].append("💾 High memory operations found - review data structures and caching strategies")

        return results

    def create_async_optimization_report(self) -> str:
        """
        Generate a comprehensive async optimization report.
        """
        report = []
        report.append("🚀 Async Performance Optimization Report")
        report.append("=" * 50)

        # Operation statistics
        report.append("\n📊 Operation Statistics:")
        for op_name, stats in self.operation_times.items():
            if stats:
                durations = [s['duration'] for s in stats]
                avg_time = sum(durations) / len(durations)
                report.append(f"  {op_name}: {len(stats)} calls, avg {avg_time:.3f}s")

        # Blocking calls
        if self.blocking_calls:
            report.append(f"\n⚠️  Blocking Calls Detected: {len(self.blocking_calls)}")
            for call in self.blocking_calls[:5]:  # Show first 5
                report.append(f"  {call['function']}: {call['blocking_calls']}")

        # Concurrency metrics
        if self.concurrency_metrics:
            report.append("\n🔄 Concurrency Metrics:")
            recent_metrics = list(self.concurrency_metrics.values())[-5:]  # Last 5 readings
            avg_cpu = sum(m['cpu_percent'] for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m['memory_mb'] for m in recent_metrics) / len(recent_metrics)
            report.append(".1f")
            report.append(".1f")

        # Recommendations
        report.append("\n💡 Recommendations:")
        if not self.operation_times:
            report.append("  - Start monitoring with @profile_async_operation decorator")
        else:
            report.append("  - Consider using asyncio.gather() for concurrent operations")
            report.append("  - Use asyncio.run_in_executor() for CPU-bound tasks")
            report.append("  - Implement connection pooling for database operations")

        return "\n".join(report)

async def run_async_performance_analysis():
    """
    Run comprehensive async performance analysis.
    """
    debugger = AsyncPerformanceDebugger()

    # Start monitoring
    debugger.start_performance_monitoring()

    print("⚡ Async Performance Analysis")
    print("=" * 40)

    # Simulate some async operations for demonstration
    @debugger.profile_async_operation
    async def sample_async_operation(delay: float):
        await asyncio.sleep(delay)
        return f"Completed after {delay}s"

    # Run sample operations
    tasks = []
    for i in range(5):
        tasks.append(sample_async_operation(0.1 * (i + 1)))

    await asyncio.gather(*tasks)

    # Analyze results
    efficiency = await debugger.analyze_async_efficiency()
    memory = await debugger.optimize_memory_operations()

    print(f"Operations analyzed: {len(efficiency['operation_stats'])}")
    print(".3f")
    print(f"Blocking calls: {efficiency['blocking_call_count']}")
    print(f"Memory efficiency: {memory['memory_efficiency_score']}/100")

    if efficiency['recommendations']:
        print("\n💡 Recommendations:")
        for rec in efficiency['recommendations']:
            print(f"  {rec}")

    if memory['optimization_suggestions']:
        print("\n💾 Memory Optimization:")
        for sug in memory['optimization_suggestions']:
            print(f"  {sug}")

    # Generate full report
    report = debugger.create_async_optimization_report()
    print(f"\n{report}")

    # Stop monitoring
    debugger.stop_performance_monitoring()

if __name__ == "__main__":
    asyncio.run(run_async_performance_analysis())