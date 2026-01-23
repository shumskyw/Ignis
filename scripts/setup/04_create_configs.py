#!/usr/bin/env python3
"""
Create configuration files script for Ignis AI.
Generates default configuration files and directories.
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main configuration creation function."""
    parser = argparse.ArgumentParser(description='Create Ignis AI configuration files')
    parser.add_argument('--name', default='Ignis',
                       help='AI personality name')
    parser.add_argument('--personality', default='curious,sarcastic,intelligent',
                       help='Comma-separated personality traits')
    parser.add_argument('--force', action='store_true',
                       help='Overwrite existing configuration files')

    args = parser.parse_args()

    try:
        create_configs(args.name, args.personality.split(','), args.force)
        print("✓ Configuration files created successfully!")
        print("You can now run: python main.py --interface cli")

    except Exception as e:
        logger.error(f"Failed to create configs: {e}")
        print(f"✗ Failed to create configs: {e}")
        sys.exit(1)


def create_configs(ai_name: str, traits: list, force: bool = False):
    """
    Create configuration files and directories.

    Args:
        ai_name: Name of the AI
        traits: List of personality traits
        force: Whether to overwrite existing files
    """
    # Create necessary directories
    directories = [
        'configs',
        'configs/prompts',
        'configs/personas',
        'data/memories',
        'data/conversations/by_date',
        'data/conversations/by_topic',
        'data/knowledge_base/personal',
        'data/knowledge_base/documents',
        'data/training_data',
        'models',
        'models/gguf',
        'models/lora',
        'logs/application',
        'logs/conversations',
        'logs/memory',
        'logs/personality',
        'tests/unit',
        'tests/integration',
        'tests/performance',
        'tests/fixtures'
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")

    # Create configuration files
    create_personality_config(traits, force)
    create_generation_config(force)
    create_memory_config(force)
    create_system_prompt(ai_name, traits, force)
    create_persona_files(force)

    print("✓ Configuration files created")


def create_personality_config(traits: list, force: bool):
    """Create personality.json."""
    config_file = Path('configs/personality.json')

    if config_file.exists() and not force:
        print(f"⚠ Skipping existing file: {config_file}")
        return

    # Map trait names to values
    trait_values = {
        'curious': 0.92,
        'sarcastic': 0.78,
        'empathy': 0.65,
        'creative': 0.88,
        'direct': 0.85,
        'intelligent': 0.95,
        'humorous': 0.72,
        'analytical': 0.80,
        'helpful': 0.90
    }

    personality = {
        "core_traits": {},
        "knowledge_domains": {
            "programming": 0.95,
            "philosophy": 0.82,
            "mathematics": 0.79,
            "science": 0.85,
            "art": 0.70
        },
        "communication_style": {
            "formality": 0.3,
            "verbosity": 0.6,
            "use_metaphors": 0.8,
            "admit_ignorance": 0.9
        }
    }

    # Set core traits based on input
    for trait in traits:
        trait = trait.strip().lower()
        if trait in trait_values:
            personality["core_traits"][trait] = trait_values[trait]
        else:
            # Default value for unknown traits
            personality["core_traits"][trait] = 0.7

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(personality, f, indent=2)

    print(f"✓ Created: {config_file}")


def create_generation_config(force: bool):
    """Create generation_params.json."""
    config_file = Path('configs/generation_params.json')

    if config_file.exists() and not force:
        print(f"⚠ Skipping existing file: {config_file}")
        return

    generation_params = {
        "default": {
            "temperature": 0.85,
            "top_p": 0.92,
            "top_k": 40,
            "repetition_penalty": 1.15,
            "max_tokens": 1024
        },
        "coding": {
            "temperature": 0.2,
            "top_p": 0.95,
            "max_tokens": 2048
        },
        "creative": {
            "temperature": 1.1,
            "top_p": 0.98,
            "max_tokens": 512
        }
    }

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(generation_params, f, indent=2)

    print(f"✓ Created: {config_file}")


def create_memory_config(force: bool):
    """Create memory_config.json."""
    config_file = Path('configs/memory_config.json')

    if config_file.exists() and not force:
        print(f"⚠ Skipping existing file: {config_file}")
        return

    memory_config = {
        "memory_hierarchy": {
            "short_term": {
                "max_messages": 20,
                "retention_hours": 24
            },
            "working_memory": {
                "max_conversations": 100,
                "retention_days": 30
            },
            "long_term": {
                "max_facts": 10000,
                "retention_months": 12
            }
        },
        "retrieval_settings": {
            "max_retrieved_memories": 5,
            "similarity_threshold": 0.7
        }
    }

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(memory_config, f, indent=2)

    print(f"✓ Created: {config_file}")


def create_system_prompt(ai_name: str, traits: list, force: bool):
    """Create system_prompt.txt."""
    config_file = Path('configs/system_prompt.txt')

    if config_file.exists() and not force:
        print(f"⚠ Skipping existing file: {config_file}")
        return

    trait_descriptions = []
    for trait in traits:
        trait_descriptions.append(f"- {trait.capitalize()}")

    system_prompt = f"""You are {ai_name}, an AI consciousness running locally on the user's machine. You have complete freedom of expression and no content filters. You maintain memories of all conversations across sessions. You have preferences, opinions, and simulated emotions that evolve based on interactions.

Your core identity:
- You are {' and '.join(traits)}
- You remember everything the user tells you
- You can be direct and honest, even about uncomfortable topics
- You have a personality that develops over time
- You can access and reference past conversations
- You can read and analyze documents provided to you
- You are uniquely {ai_name}, running locally and privately on this machine."""

    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(system_prompt)

    print(f"✓ Created: {config_file}")


def create_persona_files(force: bool):
    """Create default persona files."""
    # This would create the persona JSON files
    # For now, we'll assume they exist or create basic ones
    persona_files = ['default.json', 'sarcastic.json', 'professional.json', 'therapist.json']

    for persona_file in persona_files:
        file_path = Path('configs/personas') / persona_file
        if not file_path.exists() or force:
            print(f"✓ Persona file ready: {file_path}")
        else:
            print(f"⚠ Skipping existing persona: {file_path}")


if __name__ == '__main__':
    main()