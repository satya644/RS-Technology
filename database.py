import os
from pymongo import MongoClient
from dotenv import load_dotenv

# .env file se variables load karein
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("Error: MONGO_URI .env file me set nahi hai!")

# MongoDB Atlas Client
client = MongoClient(MONGO_URI)

# Database Name: RS_Technology
db = client["RS_Technology"]

# Agency Collections
leads_collection = db["leads"]
reviews_collection = db["reviews"]
projects_collection = db["projects"]