"""
Memory System for Ignis AI - Modular Architecture

This file now imports the new modular memory system that replaces the original
5744-line monolithic implementation while maintaining competitive AI performance.
"""

from ..memory import ModularMemorySystem

# Maintain backward compatibility by aliasing the new system
EnhancedMemorySystem = ModularMemorySystem

# Export the original class name for compatibility
__all__ = ['EnhancedMemorySystem']
