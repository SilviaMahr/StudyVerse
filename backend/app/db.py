import os
import asyncpg
from dotenv import load_dotenv
import ssl

# Load environment variables
load_dotenv(dotenv_path=".env")
DATABASE_URL = os.getenv("DATABASE_URL")

# Global pool variable
pool = None

# Create SSL context for NeonDB
ssl_context = ssl.create_default_context()

# Initialize the asyncpg connection pool
async def init_db_pool():
    global pool
    if pool is None:
        print("📡 Connecting to DB:", DATABASE_URL)
        pool = await asyncpg.create_pool(DATABASE_URL, ssl=ssl_context)
    return pool

# Close the pool on shutdown
async def close_db_pool():
    global pool
    if pool is not None:
        await pool.close()
        pool = None