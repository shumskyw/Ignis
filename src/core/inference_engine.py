"""
Llama.cpp-based Inference Engine for Ignis AI.
Optimized for GGUF models with CUDA acceleration.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, AsyncGenerator, List
import asyncio
from llama_cpp import Llama

class InferenceEngine:
    """
    Inference engine using llama.cpp for GGUF model loading and CUDA acceleration.
    """
    
    # Class-level model cache
    _model_cache = {}
    
    def __init__(self, model_path: str = "models/gguf/Hermes-2-Pro-Mistral-7B.Q4_K_M.gguf", n_gpu_layers: int = -1, n_ctx: int = 2048):
        """
        Initialize llama.cpp inference engine.

        Args:
            model_path: Path to GGUF model file
            n_gpu_layers: Number of layers to offload to GPU (-1 for all, 0 for CPU)
            n_ctx: Context window size
        """
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        # Use cached model if available
        model_key = str(self.model_path)
        if model_key not in self._model_cache:
            print(f"DEBUG: Loading model {model_key} for first time...")
            self._model_cache[model_key] = Llama(
                model_path=str(self.model_path),
                n_gpu_layers=0,  # CPU mode for now
                n_ctx=1024,      # Reduced context for faster processing
                n_threads=12,    # Increased from 8 to 12 for Ryzen 7 9700X (16 logical cores)
                n_batch=1024,    # Increased batch size for better throughput
                verbose=False,   # Reduce logs for performance
                numa=False,      # Disable NUMA for better performance on consumer CPUs
                # CPU-specific optimizations
                offload_kqv=True,  # Offload KQV cache to CPU for better memory usage
                mul_mat_q=True,   # Use quantized matrix multiplication
                logits_all=False  # Don't compute all logits for speed
            )
            print(f"DEBUG: Model cached successfully")
        else:
            print(f"DEBUG: Using cached model {model_key}")
        
        self.llm = self._model_cache[model_key]
        print(f"DEBUG: InferenceEngine loaded model: {self.llm}")

    @property
    def model(self):
        """Return the underlying model for compatibility."""
        return self.llm

    async def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7, mode: str = "default", **kwargs) -> str:
        """
        Generate text response.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            mode: Response mode ('fast', 'creative', 'default')
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        print(f"DEBUG: InferenceEngine.generate called with prompt: '{prompt[:100]}...'")
        # Adjust parameters based on mode
        if mode == "fast":
            temperature = 0.1
            max_tokens = 64  # Very short for speed
            top_k = 30
            top_p = 0.8
        elif mode == "creative":
            temperature = 1.2
            max_tokens = 256  # Reduced for speed
        elif mode == "speed":
            # Ultra-fast mode with minimal quality trade-offs
            temperature = 0.3
            max_tokens = 96
            top_k = 25
            top_p = 0.75
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        start_time = asyncio.get_event_loop().time()
        
        response = await loop.run_in_executor(
            None,
            lambda: self.llm(
                prompt, 
                max_tokens=max_tokens, 
                temperature=temperature, 
                echo=False,
                top_p=0.9,      # Add top_p for better quality
                top_k=40,       # Add top_k for coherence
                repeat_penalty=1.1,  # Reduce repetition
                **kwargs
            )
        )
        
        end_time = asyncio.get_event_loop().time()
        print(f"DEBUG: Inference generation took {(end_time - start_time):.3f}s")
        
        print(f"DEBUG: LLM response type: {type(response)}, value: {response}")
        
        if response is None:
            return "I apologize, but I couldn't generate a response right now. Please try again."
        
        # Handle different response formats
        if isinstance(response, str):
            text = response.strip()
        else:
            text = response["choices"][0]["text"].strip()
        
        print(f"DEBUG: Raw LLM response: '{text[:200]}...'")
        
        # Post-process response for llama.cpp models to extract direct answers
        if "gguf" in str(self.model_path).lower() or "hermes" in str(self.model_path).lower():
            text = self._extract_direct_answer(text)
        
        print(f"DEBUG: Processed text: '{text[:200]}...'")
        
        # Ensure we have a response
        if not text:
            return "I apologize, but I couldn't generate a response right now. Please try again."
        
        return text

    async def chat(self, messages: List[Dict[str, str]], max_tokens: int = 512, **kwargs) -> str:
        """
        Handle chat conversations.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate

        Returns:
            Chat response
        """
        # Format messages for Hermes-2-Pro
        formatted_prompt = self._format_chat_messages(messages)
        return await self.generate(formatted_prompt, max_tokens=max_tokens, **kwargs)

    def _format_chat_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Format chat messages for the model.

        Args:
            messages: List of {'role': 'user'/'assistant', 'content': str}

        Returns:
            Formatted prompt string
        """
        formatted = []
        for msg in messages:
            role = msg['role']
            content = msg['content']
            if role == 'user':
                formatted.append(f"User: {content}")
            elif role == 'assistant':
                formatted.append(f"Assistant: {content}")
            elif role == 'system':
                formatted.append(f"System: {content}")
        
        return "\n".join(formatted) + "\nAssistant:"

    def _extract_direct_answer(self, response: str) -> str:
        """
        Extract direct answer from dialogue-style response.
        
        Args:
            response: Raw model response
            
        Returns:
            Extracted direct answer
        """
        # Remove dummy tokens first
        response = response.replace('<dummy00008>', '').replace('<dummy00022>', '').replace('<dummy00002>', '')
        
        # If response doesn't contain dialogue markers, return as-is
        if "User:" not in response and "Continue the conversation" not in response:
            return response.strip()
        
        # Try to extract the first meaningful response before dialogue starts
        lines = response.split('\n')
        direct_answer = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("User:") or "Continue the conversation" in line:
                break
            if line.startswith("RESPONSE:") or line.startswith("Ignis:"):
                # Extract content after the prefix
                content = line.split(":", 1)[1].strip() if ":" in line else line
                direct_answer.append(content)
            elif not any(prefix in line for prefix in ["System:", "Assistant:", "User:"]):
                # If it's a direct response without prefix
                direct_answer.append(line)
        
        if direct_answer:
            return " ".join(direct_answer).strip()
        
        # Fallback: try to extract first sentence
        sentences = response.split('.')
        if sentences and sentences[0].strip():
            return sentences[0].strip() + "."
        
        # Last resort: return first 100 characters
        return response.strip()[:100] + "..." if len(response) > 100 else response.strip()

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "path": str(self.model_path),
            "type": "llama.cpp",
            "model_path": str(self.model_path),
            "n_ctx": 2048,
            "n_gpu_layers": -1
        }