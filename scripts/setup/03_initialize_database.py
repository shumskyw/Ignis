#!/usr/bin/env python3
"""
Initialize database script for Ignis AI.
Sets up ChromaDB vector database for memory storage.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Main initialization function."""
    parser = argparse.ArgumentParser(description='Initialize Ignis AI database')
    parser.add_argument('--chroma-path', default='./data/memories/chroma',
                       help='ChromaDB storage path')
    parser.add_argument('--reset', action='store_true',
                       help='Reset existing database')

    args = parser.parse_args()

    try:
        initialize_database(args.chroma_path, args.reset)
        print("✓ Database initialized successfully!")
        print(f"Database location: {args.chroma_path}")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        print(f"✗ Failed to initialize database: {e}")
        sys.exit(1)


def initialize_database(chroma_path: str, reset: bool = False):
    """
    Initialize ChromaDB database.

    Args:
        chroma_path: Path for ChromaDB storage
        reset: Whether to reset existing database
    """
    chroma_dir = Path(chroma_path)

    try:
        import chromadb
        from chromadb.config import Settings

        print("Initializing ChromaDB...")

        # Remove existing database if reset requested
        if reset and chroma_dir.exists():
            import shutil
            shutil.rmtree(chroma_dir)
            print("✓ Reset existing database")

        # Create ChromaDB client
        client = chromadb.PersistentClient(
            path=str(chroma_dir),
            settings=Settings(anonymized_telemetry=False)
        )

        # Test database by creating a test collection
        test_collection = client.get_or_create_collection(
            name="test_initialization",
            metadata={"description": "Test collection for initialization"}
        )

        # Add a test document
        test_collection.add(
            documents=["This is a test document for database initialization."],
            metadatas=[{"test": True, "timestamp": "2024-01-01T00:00:00Z"}],
            ids=["test_doc_001"]
        )

        # Verify the document was added
        results = test_collection.query(
            query_texts=["test"],
            n_results=1
        )

        if results['documents']:
            print("✓ Database test successful")
        else:
            raise RuntimeError("Database test failed")

        # Clean up test collection
        client.delete_collection("test_initialization")

        print("✓ Database initialized and tested")

        # Create expected collections
        collections = ['conversations', 'facts', 'documents']
        for collection_name in collections:
            client.get_or_create_collection(
                name=collection_name,
                metadata={"description": f"{collection_name} collection for Ignis memory"}
            )
            print(f"✓ Created collection: {collection_name}")

    except ImportError:
        print("✗ chromadb not installed. Install with: pip install chromadb")
        raise
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        raise


if __name__ == '__main__':
    main()