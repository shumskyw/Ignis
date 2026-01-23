"""
High-Performance Inference Engine for ChatGPT-Level Competition
Optimized for speed, concurrency, and low latency.
"""

import asyncio
import hashlib
import json
import os
import threading
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

from ..utils.logger import get_logger

logger = get_logger(__name__)


class HighPerformanceInferenceEngine:
    """
    Optimized inference engine for maximum speed and ChatGPT-level performance.
    """

    def __init__(self, config_path: str = "./configs", system_config: Dict[str, Any] = None):
        self.config_path = Path(config_path)
        self.system_config = system_config or {}

        # Model configuration
        self.model = None
        self.tokenizer = None
        self.generation_params = {}

        # Performance optimizations
        self.executor = ThreadPoolExecutor(max_workers=max(1, os.cpu_count() // 2))
        self.response_cache = {}
        self.cache_lock = asyncio.Lock()
        self.cache_max_size = 1000
        self.cache_ttl = 300  # 5 minutes

        # Connection pooling for GGUF models
        self.model_pool = []
        self.pool_size = 2  # Keep 2 model instances for concurrent requests
        self.pool_lock = asyncio.Lock()

        # Performance monitoring
        self.request_count = 0
        self.total_tokens = 0
        self.avg_response_time = 0
        self.performance_lock = threading.Lock()

        # GPU optimizations
        if TORCH_AVAILABLE and torch.cuda.is_available():
            torch.backends.cudnn.benchmark = True
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True

        # Model paths
        self.gguf_model_path = Path("models/gguf/Hermes-2-Pro-Mistral-7B.Q4_K_M.gguf")

    async def initialize(self):
        """Initialize the high-performance inference engine."""
        logger.info("🚀 Initializing High-Performance Inference Engine")

        # Start performance monitoring
        tracemalloc.start()

        # Load model configuration
        await self._load_config()

        # Initialize model pool for concurrent requests
        await self._initialize_model_pool()

        # Warm up the models
        await self._warm_up_models()

        logger.info("✅ High-Performance Inference Engine ready")

    async def _load_config(self):
        """Load optimized generation parameters."""
        config_file = self.config_path / "generation_params.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # High-performance defaults
                self.generation_params = {
                    "fast": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "max_tokens": 512,
                        "repetition_penalty": 1.1,
                        "do_sample": True
                    },
                    "creative": {
                        "temperature": 0.9,
                        "top_p": 0.95,
                        "top_k": 50,
                        "max_tokens": 1024,
                        "repetition_penalty": 1.15,
                        "do_sample": True
                    },
                    "default": {
                        "temperature": 0.8,
                        "top_p": 0.92,
                        "top_k": 45,
                        "max_tokens": 768,
                        "repetition_penalty": 1.12,
                        "do_sample": True
                    }
                }

                # Override with loaded config
                for mode, params in config.items():
                    if mode in self.generation_params:
                        self.generation_params[mode].update(params)

            except Exception as e:
                logger.warning(f"Failed to load generation config: {e}")

    async def _initialize_model_pool(self):
        """Initialize a pool of model instances for concurrent processing."""
        try:
            from llama_cpp import Llama

            for i in range(self.pool_size):
                model = Llama(
                    model_path=str(self.gguf_model_path),
                    n_ctx=4096,
                    n_threads=max(1, os.cpu_count() // 2),
                    n_gpu_layers=35 if torch.cuda.is_available() else 0,
                    verbose=False,
                    chat_format="chatml"
                )
                self.model_pool.append(model)
                logger.info(f"✅ Model instance {i+1}/{self.pool_size} loaded")

        except ImportError:
            logger.warning("llama-cpp-python not available, using single model instance")
        except Exception as e:
            logger.error(f"Failed to initialize model pool: {e}")

    async def _warm_up_models(self):
        """Warm up models with a test generation."""
        if not self.model_pool:
            return

        logger.info("🔥 Warming up models...")
        test_prompt = "Hello, how are you?"

        # Warm up all model instances concurrently
        tasks = []
        for model in self.model_pool:
            task = asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda m=model: m.create_chat_completion(
                    messages=[{"role": "user", "content": test_prompt}],
                    max_tokens=10,
                    temperature=0.1
                )
            )
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("✅ Models warmed up")

    def _get_cache_key(self, context: str, params: Dict[str, Any]) -> str:
        """Generate cache key for context and parameters."""
        content = f"{context}_{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()

    async def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get cached response if available and not expired."""
        async with self.cache_lock:
            if cache_key in self.response_cache:
                cached_item = self.response_cache[cache_key]
                if time.time() - cached_item['timestamp'] < self.cache_ttl:
                    return cached_item['response']
                else:
                    # Remove expired cache entry
                    del self.response_cache[cache_key]
        return None

    async def _cache_response(self, cache_key: str, response: str):
        """Cache a response."""
        async with self.cache_lock:
            # Implement LRU-style cache eviction
            if len(self.response_cache) >= self.cache_max_size:
                # Remove oldest entry
                oldest_key = min(self.response_cache.keys(),
                               key=lambda k: self.response_cache[k]['timestamp'])
                del self.response_cache[oldest_key]

            self.response_cache[cache_key] = {
                'response': response,
                'timestamp': time.time()
            }

    async def generate_optimized(self, context: str, mode: str = "fast", **kwargs) -> str:
        """
        High-performance text generation optimized for speed.

        Args:
            context: Input context
            mode: Generation mode (fast, creative, default)
            **kwargs: Additional parameters

        Returns:
            Generated response
        """
        start_time = time.time()

        try:
            # Get optimized parameters
            params = self.generation_params.get(mode, self.generation_params.get("default", {})).copy()
            params.update(kwargs)

            # Check cache first
            cache_key = self._get_cache_key(context, params)
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                logger.debug("✅ Cache hit - returning cached response")
                return cached_response

            # Get model from pool
            model = await self._get_model_from_pool()

            if not model:
                return "Error: No model available"

            # Generate with timeout
            timeout = params.get('timeout', 10)  # Shorter timeout for speed

            try:
                response = await asyncio.wait_for(
                    self._generate_with_model(model, context, params),
                    timeout=timeout
                )

                # Cache successful response
                await self._cache_response(cache_key, response)

                # Update performance metrics
                self._update_performance_metrics(time.time() - start_time, len(response.split()))

                return response

            except asyncio.TimeoutError:
                logger.warning(f"Generation timeout after {timeout}s")
                return "Response timeout - please try again"
            finally:
                # Return model to pool
                await self._return_model_to_pool(model)

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return f"Generation error: {str(e)}"

    async def _get_model_from_pool(self) -> Optional[Any]:
        """Get a model instance from the pool."""
        async with self.pool_lock:
            if self.model_pool:
                return self.model_pool.pop(0)
        return None

    async def _return_model_to_pool(self, model: Any):
        """Return a model instance to the pool."""
        async with self.pool_lock:
            if len(self.model_pool) < self.pool_size:
                self.model_pool.append(model)

    async def _generate_with_model(self, model, context: str, params: Dict[str, Any]) -> str:
        """Generate response using a model instance."""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            self.executor,
            lambda: model.create_chat_completion(
                messages=[{"role": "user", "content": context}],
                temperature=params.get("temperature", 0.8),
                top_p=params.get("top_p", 0.92),
                top_k=params.get("top_k", 45),
                max_tokens=params.get("max_tokens", 768),
                repeat_penalty=params.get("repetition_penalty", 1.12)
            )
        )

        return response["choices"][0]["message"]["content"]

    def _update_performance_metrics(self, response_time: float, token_count: int):
        """Update performance monitoring metrics."""
        with self.performance_lock:
            self.request_count += 1
            self.total_tokens += token_count

            # Update rolling average
            if self.request_count == 1:
                self.avg_response_time = response_time
            else:
                self.avg_response_time = (self.avg_response_time * (self.request_count - 1) + response_time) / self.request_count

    async def generate_stream_optimized(self, context: str, mode: str = "fast", **kwargs) -> AsyncGenerator[str, None]:
        """
        Streaming generation for real-time responses.
        """
        params = self.generation_params.get(mode, self.generation_params.get("default", {})).copy()
        params.update(kwargs)

        model = await self._get_model_from_pool()
        if not model:
            yield "Error: No model available"
            return

        try:
            # For streaming, we'll simulate it by generating in chunks
            full_response = await self._generate_with_model(model, context, params)

            # Stream response in chunks
            words = full_response.split()
            for i in range(0, len(words), 3):  # Stream 3 words at a time
                chunk = " ".join(words[i:i+3])
                yield chunk + " "
                await asyncio.sleep(0.05)  # Small delay for streaming effect

        finally:
            await self._return_model_to_pool(model)

    async def batch_generate(self, contexts: List[str], mode: str = "fast", **kwargs) -> List[str]:
        """
        Generate responses for multiple contexts concurrently.
        """
        tasks = [self.generate_optimized(context, mode, **kwargs) for context in contexts]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        with self.performance_lock:
            return {
                'total_requests': self.request_count,
                'average_response_time': round(self.avg_response_time, 3),
                'total_tokens_generated': self.total_tokens,
                'cache_size': len(self.response_cache),
                'model_pool_size': len(self.model_pool),
                'tokens_per_second': round(self.total_tokens / max(self.avg_response_time, 0.001), 2) if self.request_count > 0 else 0
            }

    async def cleanup(self):
        """Clean up resources."""
        self.executor.shutdown(wait=True)
        tracemalloc.stop()

        # Clear caches
        async with self.cache_lock:
            self.response_cache.clear()

        logger.info("🧹 High-Performance Inference Engine cleaned up")