#!/usr/bin/env python3
"""
Direct launcher for easydl.
Usage:
  python easydl.py
"""
import sys
from pathlib import Path

# Add package root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from easydl.cli import main

if __name__ == "__main__":
    main()
