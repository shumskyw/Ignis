"""
ChatGPT-Level Performance Optimizer
Benchmarks and optimizes Ignis AI for ChatGPT-level speed and quality.
"""

import asyncio
import json
import os
import statistics
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import psutil
from async_performance_debugger import AsyncPerformanceDebugger
from conversation_continuity_debugger import ConversationContinuityDebugger

from src.core.high_performance_inference import HighPerformanceInferenceEngine
from src.core.high_performance_memory import HighPerformanceMemorySystem


class ChatGPTPerformanceOptimizer:
    """
    Optimizes Ignis AI for ChatGPT-level performance through benchmarking and tuning.
    """

    def __init__(self):
        self.inference_engine = None
        self.memory_system = None
        self.continuity_debugger = ConversationContinuityDebugger()
        self.performance_debugger = AsyncPerformanceDebugger()

        # Performance targets (ChatGPT-level)
        self.targets = {
            'response_time_p50': 2.0,  # seconds
            'response_time_p95': 5.0,
            'tokens_per_second': 50,
            'concurrent_requests': 10,
            'memory_usage_mb': 2048,
            'cache_hit_rate': 70.0
        }

        # Benchmark results
        self.benchmark_results = {}

    async def initialize_systems(self):
        """Initialize all high-performance systems."""
        print("🚀 Initializing ChatGPT-Level Performance Systems...")

        # Initialize inference engine
        self.inference_engine = HighPerformanceInferenceEngine()
        await self.inference_engine.initialize()

        # Initialize memory system
        self.memory_system = HighPerformanceMemorySystem()
        await self.memory_system.initialize()

        print("✅ All systems initialized")

    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """
        Run comprehensive benchmark suite comparing to ChatGPT targets.
        """
        print("📊 Running Comprehensive ChatGPT-Level Benchmark Suite")
        print("=" * 60)

        results = {
            'timestamp': time.time(),
            'inference_benchmarks': {},
            'memory_benchmarks': {},
            'concurrency_benchmarks': {},
            'overall_score': 0,
            'recommendations': []
        }

        # 1. Inference Benchmarks
        print("\n🧠 Running Inference Benchmarks...")
        results['inference_benchmarks'] = await self._benchmark_inference()

        # 2. Memory Benchmarks
        print("\n💾 Running Memory Benchmarks...")
        results['memory_benchmarks'] = await self._benchmark_memory()

        # 3. Concurrency Benchmarks
        print("\n🔄 Running Concurrency Benchmarks...")
        results['concurrency_benchmarks'] = await self._benchmark_concurrency()

        # 4. System Health Check
        print("\n🏥 Running System Health Check...")
        results['system_health'] = await self._system_health_check()

        # Calculate overall score
        results['overall_score'] = self._calculate_overall_score(results)

        # Generate recommendations
        results['recommendations'] = self._generate_optimization_recommendations(results)

        # Save benchmark results
        self._save_benchmark_results(results)

        return results

    async def _benchmark_inference(self) -> Dict[str, Any]:
        """Benchmark inference performance."""
        test_prompts = [
            "Hello, how are you today?",
            "Explain quantum computing in simple terms.",
            "Write a short story about a robot learning emotions.",
            "What are the benefits of renewable energy?",
            "How does machine learning work?"
        ]

        results = {
            'response_times': [],
            'token_counts': [],
            'throughput': 0,
            'cache_performance': {},
            'quality_score': 0
        }

        print("  Testing single requests...")
        start_time = time.time()

        for prompt in test_prompts:
            request_start = time.time()

            try:
                response = await self.inference_engine.generate_optimized(prompt, mode="fast")
                response_time = time.time() - request_start

                results['response_times'].append(response_time)
                results['token_counts'].append(len(response.split()))

                print(f"  ✅ {response_time:.2f}s")
            except Exception as e:
                print(f"  ❌ Failed: {e}")
                results['response_times'].append(10.0)  # Penalty for failures

        total_time = time.time() - start_time
        results['throughput'] = len(test_prompts) / total_time

        # Get cache performance
        perf_stats = self.inference_engine.get_performance_stats()
        results['cache_performance'] = {
            'cache_size': perf_stats.get('cache_size', 0),
            'hit_rate': perf_stats.get('tokens_per_second', 0)  # Approximation
        }

        return results

    async def _benchmark_memory(self) -> Dict[str, Any]:
        """Benchmark memory system performance."""
        results = {
            'retrieval_times': [],
            'storage_times': [],
            'cache_performance': {},
            'accuracy_score': 0
        }

        test_queries = [
            "artificial intelligence",
            "machine learning",
            "quantum computing",
            "renewable energy"
        ]

        print("  Testing memory operations...")

        # Test retrieval performance
        for query in test_queries:
            start_time = time.time()
            memories = await self.memory_system.retrieve_optimized(query, limit=5)
            retrieval_time = time.time() - start_time

            results['retrieval_times'].append(retrieval_time)
            print(f"  📖 {retrieval_time:.3f}s")
        # Test storage performance
        test_content = "This is a test memory entry for benchmarking purposes."
        start_time = time.time()
        await self.memory_system.store_optimized(
            test_content,
            metadata={'test': True},
            user_id='benchmark_user',
            session_id='benchmark_session'
        )
        storage_time = time.time() - start_time
        results['storage_times'].append(storage_time)
        print(f"  💾 {storage_time:.3f}s")
        # Get memory performance stats
        mem_stats = self.memory_system.get_performance_stats()
        results['cache_performance'] = {
            'hit_rate': mem_stats.get('cache_hit_rate', 0),
            'total_operations': mem_stats.get('cache_hits', 0) + mem_stats.get('cache_misses', 0)
        }

        return results

    async def _benchmark_concurrency(self) -> Dict[str, Any]:
        """Benchmark concurrent request handling."""
        results = {
            'concurrent_response_times': [],
            'throughput_rps': 0,
            'error_rate': 0,
            'resource_usage': {}
        }

        concurrent_requests = 5  # Start with 5 concurrent requests
        test_prompts = ["Hello world"] * concurrent_requests

        print(f"  Testing {concurrent_requests} concurrent requests...")

        start_time = time.time()

        # Run concurrent requests
        responses = await self.inference_engine.batch_generate(test_prompts, mode="fast")

        total_time = time.time() - start_time
        results['throughput_rps'] = len(responses) / total_time

        # Analyze response times and errors
        successful_responses = 0
        response_times = []

        for response in responses:
            if not isinstance(response, Exception):
                successful_responses += 1
                # Estimate response time (approximation)
                response_times.append(total_time / len(responses))
            else:
                print(f"  ❌ Concurrent request failed: {response}")

        results['concurrent_response_times'] = response_times
        results['error_rate'] = ((len(responses) - successful_responses) / len(responses)) * 100

        # Resource usage
        process = psutil.Process(os.getpid())
        results['resource_usage'] = {
            'cpu_percent': process.cpu_percent(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'threads': process.num_threads()
        }

        print(f"  🧠 CPU: {results['resource_usage']['cpu_percent']:.2f}%")
        print(f"  💾 Memory: {results['resource_usage']['memory_mb']:.1f}MB")
        return results

    async def _system_health_check(self) -> Dict[str, Any]:
        """Perform system health check."""
        health = {
            'memory_usage': 0,
            'cpu_usage': 0,
            'disk_usage': 0,
            'cache_efficiency': 0,
            'error_count': 0
        }

        # Memory usage
        process = psutil.Process(os.getpid())
        health['memory_usage'] = process.memory_info().rss / 1024 / 1024

        # CPU usage
        health['cpu_usage'] = process.cpu_percent(interval=1)

        # Disk usage
        disk = psutil.disk_usage('/')
        health['disk_usage'] = disk.percent

        # Cache efficiency (from memory system)
        mem_stats = self.memory_system.get_performance_stats()
        health['cache_efficiency'] = mem_stats.get('cache_hit_rate', 0)

        return health

    def _calculate_overall_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall performance score compared to ChatGPT targets."""
        score_components = []

        # Inference performance (40% weight)
        inf_bench = results.get('inference_benchmarks', {})
        if inf_bench.get('response_times'):
            avg_response_time = statistics.mean(inf_bench['response_times'])
            target_p50 = self.targets['response_time_p50']

            # Score based on how close to target (100 = meets target, 0 = 10x slower)
            time_score = max(0, min(100, (target_p50 / avg_response_time) * 100))
            score_components.append(time_score * 0.4)

        # Memory performance (20% weight)
        mem_bench = results.get('memory_benchmarks', {})
        if mem_bench.get('retrieval_times'):
            avg_retrieval_time = statistics.mean(mem_bench['retrieval_times'])
            # Target: < 0.1s for memory retrieval
            mem_score = max(0, min(100, (0.1 / avg_retrieval_time) * 100))
            score_components.append(mem_score * 0.2)

        # Concurrency performance (20% weight)
        conc_bench = results.get('concurrency_benchmarks', {})
        throughput = conc_bench.get('throughput_rps', 0)
        target_concurrent = self.targets['concurrent_requests']

        conc_score = min(100, (throughput / target_concurrent) * 100)
        score_components.append(conc_score * 0.2)

        # System health (20% weight)
        health = results.get('system_health', {})
        memory_usage = health.get('memory_usage', 0)
        target_memory = self.targets['memory_usage_mb']

        health_score = max(0, 100 - (memory_usage / target_memory) * 100)
        score_components.append(health_score * 0.2)

        return sum(score_components) if score_components else 0

    def _generate_optimization_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on benchmark results."""
        recommendations = []

        # Inference optimizations
        inf_bench = results.get('inference_benchmarks', {})
        if inf_bench.get('response_times'):
            avg_time = statistics.mean(inf_bench['response_times'])
            if avg_time > self.targets['response_time_p50']:
                recommendations.append(f"⚡ Inference too slow ({avg_time:.2f}s avg). Enable GPU acceleration and optimize model parameters.")

        # Memory optimizations
        mem_bench = results.get('memory_benchmarks', {})
        if mem_bench.get('cache_performance', {}).get('hit_rate', 0) < self.targets['cache_hit_rate']:
            recommendations.append("💾 Low cache hit rate. Increase cache size and improve cache key generation.")

        # Concurrency optimizations
        conc_bench = results.get('concurrency_benchmarks', {})
        if conc_bench.get('error_rate', 0) > 5:
            recommendations.append("🔄 High error rate in concurrent requests. Implement request queuing and better resource management.")

        # System health
        health = results.get('system_health', {})
        if health.get('memory_usage', 0) > self.targets['memory_usage_mb']:
            recommendations.append("🧠 High memory usage. Implement memory pooling and garbage collection optimization.")

        if not recommendations:
            recommendations.append("✅ Performance looks good! Continue monitoring and consider advanced optimizations.")

        return recommendations

    def _save_benchmark_results(self, results: Dict[str, Any]):
        """Save benchmark results to file."""
        results_file = Path("performance_benchmarks.json")

        # Load existing results
        existing_results = []
        if results_file.exists():
            try:
                with open(results_file, 'r') as f:
                    existing_results = json.load(f)
            except:
                pass

        # Add new results
        existing_results.append(results)

        # Keep only last 10 results
        existing_results = existing_results[-10:]

        # Save
        with open(results_file, 'w') as f:
            json.dump(existing_results, f, indent=2)

    async def apply_performance_optimizations(self) -> Dict[str, Any]:
        """Apply automatic performance optimizations."""
        optimizations = {
            'applied': [],
            'failed': [],
            'performance_improvement': 0
        }

        print("🔧 Applying Performance Optimizations...")

        try:
            # Clean up memory
            cleaned_files, removed_messages = await self.memory_system.cleanup_old_data()
            if cleaned_files > 0 or removed_messages > 0:
                optimizations['applied'].append(f"Cleaned {cleaned_files} files and {removed_messages} messages")
                optimizations['performance_improvement'] += 5

            # Clear caches to ensure fresh state
            await self.memory_system._invalidate_cache()

            optimizations['applied'].append("Cleared memory caches for optimal performance")

        except Exception as e:
            optimizations['failed'].append(f"Memory cleanup failed: {e}")

        return optimizations

    def generate_performance_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive performance report."""
        report = []
        report.append("🚀 ChatGPT-Level Performance Report")
        report.append("=" * 50)
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}")

        # Overall score
        score = results['overall_score']
        score_icon = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
        report.append(f"\n{score_icon} Overall Performance Score: {score:.1f}/100")

        # Component breakdown
        report.append("\n📊 Performance Breakdown:")

        inf_bench = results.get('inference_benchmarks', {})
        if inf_bench.get('response_times'):
            avg_time = statistics.mean(inf_bench['response_times'])
            report.append(f"  ⚡ Inference: {avg_time:.2f}s avg response time")
        mem_bench = results.get('memory_benchmarks', {})
        if mem_bench.get('retrieval_times'):
            avg_retrieval = statistics.mean(mem_bench['retrieval_times'])
            report.append(f"  🧠 Memory: {avg_retrieval:.3f}s avg retrieval time")
        conc_bench = results.get('concurrency_benchmarks', {})
        throughput = conc_bench.get('throughput_rps', 0)
        report.append(f"  🚀 Throughput: {throughput:.2f} RPS")
        # Targets comparison
        report.append("\n🎯 ChatGPT Targets:")
        report.append(f"  Response Time (P50): {self.targets['response_time_p50']}s")
        report.append(f"  Concurrent Requests: {self.targets['concurrent_requests']}")
        report.append(f"  Memory Usage: {self.targets['memory_usage_mb']}MB")

        # Recommendations
        if results.get('recommendations'):
            report.append(f"\n💡 Recommendations ({len(results['recommendations'])}):")
            for rec in results['recommendations']:
                report.append(f"  • {rec}")

        return "\n".join(report)

async def run_chatgpt_optimization():
    """Run the complete ChatGPT-level optimization suite."""
    optimizer = ChatGPTPerformanceOptimizer()

    try:
        # Initialize systems
        await optimizer.initialize_systems()

        # Run benchmarks
        results = await optimizer.run_comprehensive_benchmark()

        # Generate report
        report = optimizer.generate_performance_report(results)
        print(f"\n{report}")

        # Apply optimizations
        if results['overall_score'] < 80:
            print("\n🔧 Applying automatic optimizations...")
            optimizations = await optimizer.apply_performance_optimizations()

            if optimizations['applied']:
                print("✅ Applied optimizations:")
                for opt in optimizations['applied']:
                    print(f"  • {opt}")

            if optimizations['failed']:
                print("❌ Failed optimizations:")
                for fail in optimizations['failed']:
                    print(f"  • {fail}")

        # Final status
        print(f"\n🏆 Optimization complete! Current score: {results['overall_score']:.1f}/100")

        if results['overall_score'] >= 80:
            print("🎉 ChatGPT-level performance achieved!")
        elif results['overall_score'] >= 60:
            print("👍 Good performance - minor optimizations needed")
        else:
            print("⚠️  Performance needs improvement - review recommendations above")

    except Exception as e:
        print(f"❌ Optimization failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        if optimizer.inference_engine:
            await optimizer.inference_engine.cleanup()
        if optimizer.memory_system:
            await optimizer.memory_system.shutdown()

if __name__ == "__main__":
    asyncio.run(run_chatgpt_optimization())