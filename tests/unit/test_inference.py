#!/usr/bin/env python3
"""
Test script to check if the model can generate responses.
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest
import torch

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.inference_engine import InferenceEngine


@pytest.mark.anyio
async def test_generation():
    print("Testing inference engine...")

    engine = InferenceEngine()

    if not engine.model:
        print("ERROR: Model not loaded!")
        return

    print(f"Model loaded: {engine.get_model_info()}")
    # print(f"Model device: {engine.model.device}")  # Llama model doesn't have device attribute
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # Test simple generation
    test_prompt = "Hello, how are you?"
    print(f"Testing with prompt: {test_prompt}")

    try:
        # Test direct generate with simple prompt
        simple_prompt = "Hello"
        params = {"max_tokens": 20, "temperature": 0.1}
        response = await engine._generate_transformers(simple_prompt, params)
        print(f"Simple response: {repr(response)}")
    except Exception as e:
        print(f"Simple generation failed: {e}")
        import traceback
        traceback.print_exc()

    try:
        # Test through generate method
        response = await engine.generate(test_prompt, max_tokens=20)
        print(f"Full response: {repr(response)}")
    except Exception as e:
        print(f"Full generation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_generation())