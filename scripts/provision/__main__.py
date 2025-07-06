"""
Entry point for python -m provision
"""

import asyncio

from .cli import main


if __name__ == "__main__":
    asyncio.run(main())