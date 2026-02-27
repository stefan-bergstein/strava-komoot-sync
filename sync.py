#!/usr/bin/env python3
"""Main entry point for Strava to Komoot sync tool."""

import sys
from src.strava_komoot_sync.cli import main

if __name__ == "__main__":
    sys.exit(main())