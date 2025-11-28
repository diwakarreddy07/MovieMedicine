"""
MongoDB Database Connection and Models
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
import os
from datetime import datetime
from bson import ObjectId

# MongoDB Atlas connection string from environment variable
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGODB_DB_NAME", "moviemood")

# Initialize MongoDB client
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Test connection
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB Atlas!")
except (ConnectionFailure, Exception) as e:
    print(f"❌ Failed to connect to MongoDB Atlas: {e}")
    print("⚠️  Make sure MONGODB_URI is set in your .env file")
    client = None

# Get database
db = client[DB_NAME] if client is not None else None

# Collections
users_collection = db.users if db is not None else None
watchlist_collection = db.watchlist if db is not None else None
ratings_collection = db.ratings if db is not None else None

# Create indexes
if db is not None:
    try:
        # Unique index on email for users
        users_collection.create_index("email", unique=True)
        users_collection.create_index("username", unique=True)
        
        # Indexes for watchlist
        watchlist_collection.create_index([("user_id", 1), ("tmdb_id", 1), ("content_type", 1)], unique=True)
        watchlist_collection.create_index("user_id")
        
        # Indexes for ratings
        ratings_collection.create_index([("user_id", 1), ("tmdb_id", 1), ("content_type", 1)], unique=True)
        ratings_collection.create_index("user_id")
        
        print("✅ Database indexes created successfully!")
    except Exception as e:
        print(f"⚠️ Error creating indexes: {e}")

def get_db():
    """Get database instance"""
    return db

def get_user_by_email(email):
    """Get user by email"""
    if users_collection is None:
        return None
    return users_collection.find_one({"email": email.lower()})

def get_user_by_username(username):
    """Get user by username"""
    if users_collection is None:
        return None
    return users_collection.find_one({"username": username.lower()})

def get_user_by_id(user_id):
    """Get user by ID"""
    if users_collection is None:
        return None
    try:
        return users_collection.find_one({"_id": ObjectId(user_id)})
    except:
        return None

def create_user(username, email, password_hash, preferences=None):
    """Create a new user"""
    if users_collection is None:
        return None
    
    user_doc = {
        "username": username.lower(),
        "email": email.lower(),
        "password_hash": password_hash,
        "preferences": preferences or {
            "genres": ["action", "comedy", "drama"],
            "mood_preferences": ["happy", "excited"],
            "content_types": ["movies", "series"]
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    try:
        result = users_collection.insert_one(user_doc)
        return str(result.inserted_id)
    except DuplicateKeyError:
        return None

def update_user_preferences(user_id, preferences):
    """Update user preferences"""
    if users_collection is None:
        return False
    
    try:
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "preferences": preferences,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return True
    except:
        return False

def add_to_watchlist(user_id, tmdb_id, content_type, title, poster_path):
    """Add item to watchlist"""
    if watchlist_collection is None:
        return False
    
    try:
        watchlist_collection.update_one(
            {
                "user_id": user_id,
                "tmdb_id": tmdb_id,
                "content_type": content_type
            },
            {
                "$set": {
                    "user_id": user_id,
                    "tmdb_id": tmdb_id,
                    "content_type": content_type,
                    "title": title,
                    "poster_path": poster_path,
                    "added_date": datetime.utcnow()
                }
            },
            upsert=True
        )
        return True
    except:
        return False

def remove_from_watchlist(user_id, tmdb_id, content_type):
    """Remove item from watchlist"""
    if watchlist_collection is None:
        return False
    
    try:
        result = watchlist_collection.delete_one({
            "user_id": user_id,
            "tmdb_id": tmdb_id,
            "content_type": content_type
        })
        return result.deleted_count > 0
    except:
        return False

def get_watchlist(user_id):
    """Get user's watchlist"""
    if watchlist_collection is None:
        return []
    
    try:
        items = list(watchlist_collection.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("added_date", -1))
        return items
    except:
        return []

def add_rating(user_id, tmdb_id, content_type, rating, review=""):
    """Add or update rating"""
    if ratings_collection is None:
        return False
    
    try:
        ratings_collection.update_one(
            {
                "user_id": user_id,
                "tmdb_id": tmdb_id,
                "content_type": content_type
            },
            {
                "$set": {
                    "user_id": user_id,
                    "tmdb_id": tmdb_id,
                    "content_type": content_type,
                    "rating": rating,
                    "review": review,
                    "created_date": datetime.utcnow()
                }
            },
            upsert=True
        )
        return True
    except:
        return False

def get_rating(user_id, tmdb_id, content_type):
    """Get user's rating for a specific item"""
    if ratings_collection is None:
        return None
    
    try:
        rating = ratings_collection.find_one({
            "user_id": user_id,
            "tmdb_id": tmdb_id,
            "content_type": content_type
        }, {"_id": 0})
        return rating
    except:
        return None

def get_all_ratings(user_id):
    """Get all user's ratings"""
    if ratings_collection is None:
        return []
    
    try:
        ratings = list(ratings_collection.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("created_date", -1))
        return ratings
    except:
        return []

