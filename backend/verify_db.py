import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from database import init_db
from utils.logger import get_logger

log = get_logger("test_db")

async def test():
    try:
        log.info("Starting database initialization...")
        await init_db()
        log.info("Database initialization successful!")
    except Exception as e:
        log.error(f"Database initialization failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test())
