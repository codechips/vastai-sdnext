#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "aiohttp",
#     "tomli",
#     "huggingface_hub[hf_transfer]",
#     "pydantic>=2.0.0",
# ]
# ///
"""
VastAI SD.Next Provisioning System - Entry Point

Run with: ./provision.py or uv run --script provision.py
"""

import asyncio
import os
import sys

# Fix imports when running as a script
if __package__ is None:
    # Add current directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from cli import main
else:
    from .cli import main


if __name__ == "__main__":
    asyncio.run(main())