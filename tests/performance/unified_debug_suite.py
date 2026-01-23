"""
Unified Memory & Performance Debug Suite
Combines conversation continuity, async performance, and short-term memory debugging.
"""

import asyncio
import time
from typing import Any, Dict, List

from async_performance_debugger import AsyncPerformanceDebugger
from conversation_continuity_debugger import ConversationContinuityDebugger
from short_term_memory_debugger import ShortTermMemoryDebugger


class UnifiedDebugSuite:
    """
    Unified debugging suite for Ignis AI memory and performance issues.
    """

    def __init__(self):
        self.continuity_debugger = ConversationContinuityDebugger()
        self.performance_debugger = AsyncPerformanceDebugger()
        self.memory_debugger = ShortTermMemoryDebugger()

    async def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """
        Run comprehensive analysis across all debuggers.
        """
        results = {
            'timestamp': time.time(),
            'conversation_continuity': {},
            'async_performance': {},
            'short_term_memory': {},
            'overall_health_score': 0,
            'critical_issues': [],
            'recommendations': []
        }

        print("🔍 Starting Comprehensive Memory & Performance Analysis")
        print("=" * 60)

        # 1. Conversation Continuity Analysis
        print("\n📝 Analyzing Conversation Continuity...")
        try:
            continuity = self.continuity_debugger.analyze_session_continuity()
            results['conversation_continuity'] = continuity

            continuity_score = continuity.get('continuity_score', 0)
            print(".1f")

            if continuity['issues']:
                results['critical_issues'].extend([f"Continuity: {issue}" for issue in continuity['issues']])

        except Exception as e:
            print(f"❌ Continuity analysis failed: {e}")
            results['conversation_continuity'] = {'error': str(e)}

        # 2. Async Performance Analysis
        print("\n⚡ Analyzing Async Performance...")
        try:
            # Start monitoring
            self.performance_debugger.start_performance_monitoring()

            # Run some sample operations to analyze (reduced for speed)
            await self._run_sample_operations()

            # Stop monitoring first
            self.performance_debugger.stop_performance_monitoring()

            # Get analysis
            efficiency = await self.performance_debugger.analyze_async_efficiency()
            memory = await self.performance_debugger.optimize_memory_operations()

            results['async_performance'] = {
                'efficiency': efficiency,
                'memory': memory
            }

            perf_score = 100 - (len(efficiency.get('recommendations', [])) * 10)
            perf_score = max(0, min(100, perf_score))
            print(f"Performance Score: {perf_score}/100")

            if efficiency.get('blocking_call_count', 0) > 0:
                results['critical_issues'].append(f"Performance: {efficiency['blocking_call_count']} blocking calls detected")

        except Exception as e:
            print(f"❌ Performance analysis failed: {e}")
            results['async_performance'] = {'error': str(e)}
        finally:
            # Ensure monitoring is stopped
            try:
                self.performance_debugger.stop_performance_monitoring()
            except:
                pass

        # 3. Short-Term Memory Analysis
        print("\n🧠 Analyzing Short-Term Memory...")
        try:
            storage = self.memory_debugger.analyze_short_term_storage()
            retrieval = self.memory_debugger.debug_message_retrieval("test query")

            results['short_term_memory'] = {
                'storage': storage,
                'retrieval': retrieval
            }

            memory_score = storage.get('health_score', 0)
            print(f"Memory Health: {memory_score}/100")

            if storage.get('storage_issues'):
                results['critical_issues'].extend([f"Memory: {issue}" for issue in storage['storage_issues']])

        except Exception as e:
            print(f"❌ Memory analysis failed: {e}")
            results['short_term_memory'] = {'error': str(e)}

        # Calculate overall health score
        scores = []
        if 'continuity_score' in results['conversation_continuity']:
            scores.append(results['conversation_continuity']['continuity_score'])
        if results['async_performance'] and 'efficiency' in results['async_performance']:
            scores.append(100 - (len(results['async_performance']['efficiency'].get('recommendations', [])) * 10))
        if results['short_term_memory'] and 'storage' in results['short_term_memory']:
            scores.append(results['short_term_memory']['storage'].get('health_score', 0))

        if scores:
            results['overall_health_score'] = sum(scores) / len(scores)
        else:
            results['overall_health_score'] = 0

        # Generate recommendations
        results['recommendations'] = self._generate_recommendations(results)

        return results

    async def _run_sample_operations(self):
        """
        Run sample async operations for performance analysis (optimized for speed).
        """
        @self.performance_debugger.profile_async_operation
        async def sample_memory_operation():
            await asyncio.sleep(0.001)  # Much faster - simulate quick memory access
            return "memory_result"

        @self.performance_debugger.profile_async_operation
        async def sample_computation():
            # Simulate lightweight computation
            result = sum(i for i in range(100))  # Much smaller loop
            return result

        # Run fewer concurrent operations for speed
        tasks = []
        for _ in range(3):  # Reduced from 10 to 3
            tasks.extend([sample_memory_operation(), sample_computation()])

        await asyncio.gather(*tasks, return_exceptions=True)

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """
        Generate comprehensive recommendations based on analysis.
        """
        recommendations = []

        # Conversation continuity recommendations
        continuity = results.get('conversation_continuity', {})
        if continuity.get('continuity_score', 100) < 70:
            recommendations.append("📝 Improve session continuity - reduce gaps between conversations")
        if continuity.get('average_session_gap', 0) > 48:
            recommendations.append("📝 Implement conversation state persistence across long gaps")

        # Async performance recommendations
        perf = results.get('async_performance', {})
        if perf and 'efficiency' in perf:
            efficiency = perf['efficiency']
            recommendations.extend(efficiency.get('recommendations', []))

        # Short-term memory recommendations
        memory = results.get('short_term_memory', {})
        if memory and 'storage' in memory:
            storage = memory['storage']
            if storage.get('health_score', 100) < 70:
                recommendations.append("🧠 Run short-term memory repair to clean up old data")
            if storage.get('oldest_message_age_hours', 0) > 48:
                recommendations.append("🧠 Configure shorter message retention time")

        # General recommendations
        if results['overall_health_score'] < 60:
            recommendations.append("🚨 Critical: Overall system health is poor - comprehensive review needed")
        elif results['overall_health_score'] < 80:
            recommendations.append("⚠️  Moderate issues detected - address recommendations above")

        return recommendations

    async def run_automated_repairs(self) -> Dict[str, Any]:
        """
        Run automated repair operations.
        """
        repair_results = {
            'repairs_attempted': 0,
            'repairs_successful': 0,
            'issues_fixed': [],
            'remaining_issues': []
        }

        print("\n🔧 Running Automated Repairs...")

        # Short-term memory repairs
        try:
            memory_repairs = self.memory_debugger.repair_short_term_memory()
            repair_results['repairs_attempted'] += memory_repairs['repairs_attempted']
            repair_results['repairs_successful'] += memory_repairs['repairs_successful']
            repair_results['issues_fixed'].extend(memory_repairs['issues_fixed'])
            repair_results['remaining_issues'].extend(memory_repairs['remaining_issues'])
            print(f"🧠 Memory repairs: {memory_repairs['repairs_successful']}/{memory_repairs['repairs_attempted']} successful")
        except Exception as e:
            repair_results['remaining_issues'].append(f"Memory repair failed: {e}")

        # Performance optimizations (limited automation possible)
        try:
            # Could implement automatic performance fixes here
            print("⚡ Performance optimizations: Manual review recommended")
        except Exception as e:
            repair_results['remaining_issues'].append(f"Performance optimization failed: {e}")

        return repair_results

    def generate_comprehensive_report(self, results: Dict[str, Any]) -> str:
        """
        Generate a comprehensive analysis report.
        """
        report = []
        report.append("🎯 Ignis AI Memory & Performance Analysis Report")
        report.append("=" * 55)
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}")

        # Overall health
        health = results['overall_health_score']
        health_icon = "🟢" if health >= 80 else "🟡" if health >= 60 else "🔴"
        report.append(f"\n{health_icon} Overall Health Score: {health:.1f}/100")

        # Critical issues
        if results['critical_issues']:
            report.append(f"\n🚨 Critical Issues ({len(results['critical_issues'])}):")
            for issue in results['critical_issues'][:5]:  # Show top 5
                report.append(f"  • {issue}")

        # Component scores
        report.append("\n📊 Component Scores:")

        continuity = results.get('conversation_continuity', {})
        if 'continuity_score' in continuity:
            report.append(".1f")

        perf = results.get('async_performance', {})
        if perf and 'efficiency' in perf:
            rec_count = len(perf['efficiency'].get('recommendations', []))
            perf_score = max(0, 100 - rec_count * 10)
            report.append(f"  Async Performance: {perf_score}/100")

        memory = results.get('short_term_memory', {})
        if memory and 'storage' in memory:
            mem_score = memory['storage'].get('health_score', 0)
            report.append(f"  Short-Term Memory: {mem_score}/100")

        # Recommendations
        if results['recommendations']:
            report.append(f"\n💡 Recommendations ({len(results['recommendations'])}):")
            for rec in results['recommendations']:
                report.append(f"  • {rec}")

        # Next steps
        report.append("\n🚀 Next Steps:")
        report.append("  1. Review critical issues above")
        report.append("  2. Implement recommended fixes")
        report.append("  3. Run automated repairs")
        report.append("  4. Re-run analysis to verify improvements")

        return "\n".join(report)

async def run_unified_debug_suite():
    """
    Run the complete unified debug suite.
    """
    suite = UnifiedDebugSuite()

    # Run comprehensive analysis
    results = await suite.run_comprehensive_analysis()

    # Generate and display report
    report = suite.generate_comprehensive_report(results)
    print(f"\n{report}")

    # Offer automated repairs
    if results['overall_health_score'] < 80:
        print("\n🔧 Would you like to run automated repairs? (y/n)")
        # In a real implementation, you'd get user input here
        # For now, we'll run them automatically
        repair_results = await suite.run_automated_repairs()

        if repair_results['repairs_successful'] > 0:
            print(f"\n✅ Repairs completed: {repair_results['repairs_successful']}/{repair_results['repairs_attempted']} successful")
        if repair_results['remaining_issues']:
            print("Remaining issues:")
            for issue in repair_results['remaining_issues'][:3]:
                print(f"  ⚠️  {issue}")

if __name__ == "__main__":
    asyncio.run(run_unified_debug_suite())