#!/usr/bin/env python3
"""
Download model script for Ignis AI.
Downloads the primary language model from HuggingFace.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main download function."""
    parser = argparse.ArgumentParser(description='Download Ignis AI model')
    parser.add_argument('--model', default='dphn/dolphin-2.9-llama3-8b',
                       help='HuggingFace model ID')
    parser.add_argument('--output', default='./models/dolphin-2.9-llama3-8b',
                       help='Output directory')
    parser.add_argument('--token', help='HuggingFace token (if required)')

    args = parser.parse_args()

    try:
        download_model(args.model, args.output, args.token)
        print("✓ Model downloaded successfully!")
        print(f"Model saved to: {args.output}")

    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        print(f"✗ Failed to download model: {e}")
        sys.exit(1)


def download_model(model_id: str, output_dir: str, token: str = None):
    """
    Download model from HuggingFace.

    Args:
        model_id: HuggingFace model ID
        output_dir: Output directory
        token: HuggingFace token
    """
    try:
        from huggingface_hub import snapshot_download

        print(f"Downloading model: {model_id}")
        print("This may take a while (20-30GB)...")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Download model
        download_kwargs = {
            'repo_id': model_id,
            'local_dir': str(output_path),
            'local_dir_use_symlinks': False,
        }

        if token:
            download_kwargs['token'] = token

        snapshot_download(**download_kwargs)

        print("✓ Download completed!")

    except ImportError:
        print("✗ huggingface_hub not installed. Install with: pip install huggingface_hub")
        raise
    except Exception as e:
        print(f"✗ Download failed: {e}")
        raise


if __name__ == '__main__':
    main()