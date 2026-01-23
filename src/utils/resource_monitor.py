"""
Resource monitoring utilities for Ignis AI.
Provides real-time monitoring of CPU, GPU, and memory usage during inference.
"""

import os
import threading
import time
from typing import Any, Dict, Optional

import psutil

try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    GPUtil = None

class ResourceMonitor:
    """
    Monitors system resources during inference generation.
    Provides real-time updates and performance analysis.
    """

    def __init__(self):
        self.monitoring = False
        self.start_time = None
        self.cpu_history = []
        self.memory_history = []
        self.gpu_history = []
        self.thread = None
        self.max_generation_time = 33.0  # seconds - our benchmark

    def start_monitoring(self, operation_name: str = "inference"):
        """Start resource monitoring."""
        if self.monitoring:
            return

        self.monitoring = True
        self.start_time = time.time()
        self.cpu_history = []
        self.memory_history = []
        self.gpu_history = []
        self.operation_name = operation_name

        # Start monitoring thread
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

        print(f"\n[MONITOR] Starting resource monitoring for {operation_name}")
        print(f"[TIME] Max expected time: {self.max_generation_time}s (red line)")
        print("[STATS] Monitoring: CPU | Memory | GPU (if available)")
        print("-" * 60)

    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return summary."""
        if not self.monitoring:
            return {}

        self.monitoring = False
        if self.thread:
            self.thread.join(timeout=1.0)

        end_time = time.time()
        total_time = end_time - self.start_time

        # Calculate statistics
        stats = {
            "total_time": total_time,
            "max_expected_time": self.max_generation_time,
            "performance_ratio": total_time / self.max_generation_time,
            "cpu_avg": sum(self.cpu_history) / len(self.cpu_history) if self.cpu_history else 0,
            "cpu_max": max(self.cpu_history) if self.cpu_history else 0,
            "memory_avg": sum(self.memory_history) / len(self.memory_history) if self.memory_history else 0,
            "memory_max": max(self.memory_history) if self.memory_history else 0,
        }

        if self.gpu_history:
            gpu_stats = []
            for gpu_data in self.gpu_history:
                if gpu_data:
                    gpu_stats.extend([g.get('usage', 0) for g in gpu_data])
            if gpu_stats:
                stats["gpu_avg"] = sum(gpu_stats) / len(gpu_stats)
                stats["gpu_max"] = max(gpu_stats)

        print(f"\n[COMPLETE] {self.operation_name.upper()} COMPLETE")
        print(f"[TIME] Total time: {total_time:.2f}s")
        print(f"[PERF] Performance: {stats['performance_ratio']:.1f}x expected time")
        print(f"[CPU] CPU: {stats['cpu_avg']:.1f}% avg, {stats['cpu_max']:.1f}% max")
        print(f"[MEM] Memory: {stats['memory_avg']:.1f}% avg, {stats['memory_max']:.1f}% max")

        if "gpu_avg" in stats:
            print(f"[GPU] GPU: {stats['gpu_avg']:.1f}% avg, {stats['gpu_max']:.1f}% max")

        # Performance assessment
        if total_time > self.max_generation_time:
            print(f"[SLOW] Exceeded max time by {total_time - self.max_generation_time:.2f}s")
        elif total_time < self.max_generation_time * 0.5:
            print("[FAST] Well under time limit")
        else:
            print("[OK] Within acceptable range")

        return stats

    def _monitor_loop(self):
        """Main monitoring loop."""
        update_interval = 0.5  # seconds

        while self.monitoring:
            current_time = time.time() - self.start_time

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # GPU usage (if available)
            gpu_data = None
            if GPU_AVAILABLE and GPUtil:
                try:
                    gpu_data = GPUtil.getGPUs()
                    gpu_data = [{"id": gpu.id, "usage": gpu.load * 100, "memory": gpu.memoryUtil * 100}
                               for gpu in gpu_data]
                except Exception as e:
                    print(f"GPU monitoring error: {e}")

            # Store data
            self.cpu_history.append(cpu_percent)
            self.memory_history.append(memory_percent)
            self.gpu_history.append(gpu_data)

            # Display current status
            status_line = f"[{current_time:.1f}s] CPU:{cpu_percent:5.1f}% | MEM:{memory_percent:5.1f}%"

            if gpu_data:
                gpu_usage = gpu_data[0]['usage'] if gpu_data else 0
                status_line += f" | GPU:{gpu_usage:5.1f}%"

            # Color coding based on time
            if current_time > self.max_generation_time:
                status_line = f"\033[91m{status_line} 🚨\033[0m"  # Red for slow
            elif current_time > self.max_generation_time * 0.8:
                status_line = f"\033[93m{status_line} ⚠️\033[0m"   # Yellow for warning
            else:
                status_line = f"\033[92m{status_line} ✅\033[0m"   # Green for good

            print(status_line, end='\r', flush=True)

            time.sleep(update_interval)

        # Clear the progress line
        print(" " * 80, end='\r', flush=True)

# Global monitor instance
_monitor = ResourceMonitor()

def start_resource_monitoring(operation_name: str = "inference"):
    """Start monitoring system resources."""
    _monitor.start_monitoring(operation_name)

def stop_resource_monitoring() -> Dict[str, Any]:
    """Stop monitoring and get summary."""
    return _monitor.stop_monitoring()

def get_resource_stats() -> Dict[str, Any]:
    """Get current resource statistics."""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "gpu_available": GPU_AVAILABLE,
        "gpu_data": GPUtil.getGPUs() if GPU_AVAILABLE else None
    }