import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

pool = None

async def connect_db():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, statement_cache_size=0)

async def close_db():
    global pool
    await pool.close()

def get_pool():
    return pool