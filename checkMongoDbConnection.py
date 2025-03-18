import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Debug: Print loaded credentials
MONGO_ConnectionString = os.getenv("MONGO_ConnectionString")
MONGO_DBNAME = os.getenv("MONGO_DBNAME")

print("🔍 MONGO_CREDENTIALS:", MONGO_ConnectionString)
print("🔍 MONGO_DBNAME:", MONGO_DBNAME)

# Ensure they are correctly loaded
if not MONGO_ConnectionString or not MONGO_DBNAME:
    raise ValueError("MONGO_CREDENTIALS or MONGO_DBNAME is missing. Check your .env file!")

# Construct MongoDB URI
MONGO_URI = f"mongodb+srv://{MONGO_ConnectionString}"
print(" Constructed MONGO_URI:", MONGO_URI)
