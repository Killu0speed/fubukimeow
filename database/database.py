# database/database.py

import json
from motor.motor_asyncio import AsyncIOMotorClient

# ============================================================= #
# 🔹 Load DB config from setup.json
# ============================================================= #
with open("setup.json", "r") as f:
    config = json.load(f)

# Handle both dict and list formats
if isinstance(config, list):
    config = config[0]

MONGO_URI = config.get("db_uri")
DB_NAME = config.get("db_name", "filesharexbot")

# ============================================================= #
# 🔹 Setup MongoDB
# ============================================================= #
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client[DB_NAME]

# Clicks collection
clicks = db["clicks"]

# ============================================================= #
# 🔹 Functions
# ============================================================= #

async def add_click(user_id: int, base64_string: str):
    """
    Store a unique base64 string per user (no duplicates).
    """
    try:
        await clicks.update_one(
            {"_id": user_id},
            {"$addToSet": {"base64_strings": base64_string}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"[DB] Failed to store base64 string for {user_id}: {e}")
        return False


async def total_click(base64_string: str) -> int:
    """
    Count how many unique users clicked a given base64_string.
    """
    try:
        count = await clicks.count_documents({"base64_strings": base64_string})
        return count
    except Exception as e:
        print(f"[DB] Failed to count clicks for {base64_string}: {e}")
        return 0
