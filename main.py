# Ignis AI Assistant
# A completely offline, self-contained AI with persistent memory and evolving personality

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Set debug logging
os.environ['IGNIS_LOG_LEVEL'] = 'DEBUG'

# Add current directory to path to enable src imports
sys.path.insert(0, str(Path(__file__).parent))

# Set working directory to script location for relative paths
os.chdir(Path(__file__).parent)

def main():
    parser = argparse.ArgumentParser(description='Ignis AI Assistant - Offline AI with Memory')
    parser.add_argument('--interface', choices=['cli', 'web', 'api'], default='cli',
                       help='Interface to launch (default: cli)')
    parser.add_argument('--config', default='./configs',
                       help='Path to config directory')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Set environment
    os.environ['IGNIS_CONFIG_PATH'] = args.config
    if args.debug:
        os.environ['IGNIS_DEBUG'] = '1'
    
    try:
        # Import here to allow path setup
        from src.core.ignis import IgnisAI
        
        ignis = IgnisAI(args.config)
        
        if args.interface == 'cli':
            from src.interfaces.cli.terminal_ui import run_cli
            asyncio.run(run_cli(ignis))
        elif args.interface == 'web':
            from src.interfaces.web_ui.custom_app import run_web
            run_web(ignis)
        elif args.interface == 'api':
            from src.interfaces.api.rest_api import run_api
            run_api(ignis)
            
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting Ignis: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()