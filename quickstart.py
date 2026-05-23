#!/usr/bin/env python
"""
Quick start script for GitAgent Interviewer.

Sets up environment and runs demo interview.
"""

import os
import sys
import subprocess


def check_requirements():
    """Check if required packages are installed."""
    required = ['github', 'requests', 'dotenv']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return missing


def main():
    """Run quick start."""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║           GitAgent Interviewer — Quick Start Setup                 ║
╚════════════════════════════════════════════════════════════════════╝
""")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("✗ Python 3.11+ required")
        return 1
    
    print("✓ Python version OK")
    
    # Check requirements
    missing = check_requirements()
    if missing:
        print(f"✗ Missing packages: {', '.join(missing)}")
        print("\nRun: pip install -r requirements.txt")
        return 1
    
    print("✓ All packages installed")
    
    # Check .env file
    if not os.path.exists('.env'):
        print("\n✗ .env file not found")
        print("Run: cp .env.example .env")
        print("Then edit .env and add your GITHUB_TOKEN")
        return 1
    
    print("✓ .env file exists")
    
    # Check GITHUB_TOKEN
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('GITHUB_TOKEN'):
        print("✗ GITHUB_TOKEN not set in .env")
        return 1
    
    print("✓ GITHUB_TOKEN configured")
    
    # All checks passed
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                    Ready to run interviews!                        ║
╚════════════════════════════════════════════════════════════════════╝

Try the demo:
    python demo.py

Or run an interview:
    python main.py <github_username>

Examples:
    python demo.py                  # Demo with default user
    python main.py torvalds         # Interview Linus Torvalds
    python main.py octocat          # Interview GitHub's Octocat

See README.md for more information.
""")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
