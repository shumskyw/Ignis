"""
Standalone test for the new GPU-optimized inference engine.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Mock dependencies
class MockLogger:
    def info(self, msg): print(f'[INFO] {msg}')
    def warning(self, msg): print(f'[WARN] {msg}')
    def error(self, msg): print(f'[ERROR] {msg}')
    def debug(self, msg): pass

def mock_start_monitoring(name): pass
def mock_stop_monitoring(): return {'gpu_utilization': 85.0, 'duration': 2.1}

# Monkey patch the imports before importing
import sys

sys.modules['src.utils.logger'] = type('module', (), {'get_logger': lambda x: MockLogger()})
sys.modules['src.utils.resource_monitor'] = type('module', (), {
    'start_resource_monitoring': mock_start_monitoring,
    'stop_resource_monitoring': mock_stop_monitoring
})

# Now import the inference engine
from src.core.inference_engine import InferenceEngine


async def test_inference():
    print('Testing new GPU-optimized inference engine...')
    print(f'CUDA available: {__import__("torch").cuda.is_available()}')

    engine = InferenceEngine()

    # Check model loading
    info = engine.get_model_info()
    print(f'Model info: {info}')

    if info['status'] == 'loaded':
        print('Model loaded successfully! Testing generation...')
        try:
            response = await engine.generate('Hello, how are you today?', mode='default')
            print(f'Response: {response[:300]}...')
            print('GPU-optimized inference working!')
        except Exception as e:
            print(f'Generation failed: {e}')
            import traceback
            traceback.print_exc()
    else:
        print('Model failed to load - check CUDA availability and model download')

if __name__ == "__main__":
    asyncio.run(test_inference())