# database/database.py

import json
import pymongo

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
dbclient = pymongo.MongoClient(MONGO_URI)
db = dbclient[DB_NAME]

# Collections
user_data = db["users"]
premium_users = db["pros"]
clicks = db["clicks"]


async def add_click(user_id: int, base64_string: str):
    try:
        clicks.update_one(
            {"_id": user_id},
            {"$addToSet": {"base64_strings": base64_string}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"[DB] Failed to store base64 string: {e}")
        return False

async def total_click(base64_string: str):
    try:
        return clicks.count_documents({"base64_strings": base64_string})
    except Exception as e:
        print(f"[DB] Failed to count clicks: {e}")
        return 0
