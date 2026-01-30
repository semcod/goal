#!/usr/bin/env python3
"""
Goal CLI - Unified version control and package publishing

Usage:
    python3 -m goal [command] [options]
    
When working with the goal source repository, run it directly:
    python3 -m goal

This ensures you're using the latest local version with all fixes.
"""

from goal.cli import main

if __name__ == '__main__':
    main()
