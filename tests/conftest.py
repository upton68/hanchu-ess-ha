import asyncio
import os
import sys

# Allow `import custom_components.hanchuess...` from the repo root without an
# install step (shared by all test modules).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# aiohttp's async DNS resolver does not work with Windows' default ProactorEventLoop.
# Switching to WindowsSelectorEventLoopPolicy restores normal DNS resolution.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
