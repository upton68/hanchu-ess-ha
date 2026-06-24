import asyncio
import sys

# aiohttp's async DNS resolver does not work with Windows' default ProactorEventLoop.
# Switching to WindowsSelectorEventLoopPolicy restores normal DNS resolution.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())