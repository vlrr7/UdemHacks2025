import datetime
from bson.objectid import ObjectId
import pymongo
from werkzeug.security import generate_password_hash, check_password_hash
import streamlit as st


def login(username, password):
    user_data = users_collection.find_one({"username": username})
    if not user_data or not check_password_hash(user_data['password'], password):
        return None
    return User(**user_data)

def register(username, password, email):
    if users_collection.find_one({"$or": [{"username": username}, {"email": email}]}):
        return None, "Username or email already exists"
    
    hashed_pw = generate_password_hash(password)
    user = User(username=username, password=hashed_pw, email=email)
    user.save()
    return user, "Registration successful"


# -------------------------------------------------------------------------------
# 1. CONNEXION À MONGODB ATLAS
# -------------------------------------------------------------------------------
MONGO_URI = f"mongodb+srv://dbUser:{st.secrets["MONGO_DB_PASSWORD"]}@healthprodb.eptzn.mongodb.net/?retryWrites=true&w=majority&appName=healthprodb"
client = pymongo.MongoClient(MONGO_URI)
db = client["healthpro"]  # Nom de la base de données (à modifier si nécessaire)

# Collections (équivalent des tables en SQL)
users_collection = db["users"]
data_entries_collection = db["data_entries"]
follows_collection = db["follows"]

# -------------------------------------------------------------------------------
# 2. CLASSE USER (remplace le modèle SQLAlchemy "User")
# -------------------------------------------------------------------------------
class User:
    def __init__(self, username, password, email, created_at=None, _id=None):
        self._id = _id or ObjectId()
        self.username = username
        self.password = password
        self.email = email
        self.created_at = created_at or datetime.datetime.utcnow()

    @property
    def id(self):
        return str(self._id)

    def save(self):
        users_collection.update_one(
            {"_id": self._id},
            {"$set": self.__dict__},
            upsert=True
        )

    @staticmethod
    def find_by_email(email):
        return users_collection.find_one({"email": email})
    
    @staticmethod
    def find_by_username(username):
        return users_collection.find_one({"username": username})

# Modified DataEntry Class
class DataEntry:
    def __init__(self, user_id, **kwargs):
        self.user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        self.date = kwargs.get('date', datetime.datetime.utcnow())
        self.pushups = kwargs.get('pushups', 0)
        self.meals_count = kwargs.get('meals_count', 0)
        self.meals_details = kwargs.get('meals_details', {})
        self.water_intake = kwargs.get('water_intake', 0.0)
        self.sleep_hours = kwargs.get('sleep_hours', 0.0)
        self.time_spent = kwargs.get('time_spent', 0.0)
        self._id = kwargs.get('_id', ObjectId())

    def save(self):
        data_entries_collection.update_one(
            {"_id": self._id},
            {"$set": self.__dict__},
            upsert=True
        )

# -------------------------------------------------------------------------------
# 3. CLASSE DATAENTRY (remplace le modèle SQLAlchemy "DataEntry")
# -------------------------------------------------------------------------------
class DataEntry:
    def __init__(self, user_id, date=None, pushups=0, meals_count=0, meals_details=None,
                 water_intake=0.0, sleep_hours=0.0, time_spent=0.0, _id=None):
        self._id = _id
        self.user_id = user_id  # Conservez en tant que chaîne ou ObjectId (choisissez et soyez cohérent)
        self.date = date or datetime.datetime.utcnow()
        self.pushups = pushups
        self.meals_count = meals_count
        self.meals_details = meals_details or {}
        self.water_intake = water_intake
        self.sleep_hours = sleep_hours
        self.time_spent = time_spent

    def save(self):
        """Insère ou met à jour cette entrée de données dans MongoDB."""
        doc = {
            "user_id": self.user_id,
            "date": self.date,
            "pushups": self.pushups,
            "meals_count": self.meals_count,
            "meals_details": self.meals_details,
            "water_intake": self.water_intake,
            "sleep_hours": self.sleep_hours,
            "time_spent": self.time_spent
        }
        if self._id:
            data_entries_collection.update_one({"_id": self._id}, {"$set": doc})
        else:
            result = data_entries_collection.insert_one(doc)
            self._id = result.inserted_id

    @staticmethod
    def find_by_user_id(user_id):
        docs = data_entries_collection.find({"user_id": user_id}).sort("date", -1)
        entries = []
        for doc in docs:
            entries.append(DataEntry(
                _id=doc["_id"],
                user_id=doc["user_id"],
                date=doc["date"],
                pushups=doc["pushups"],
                meals_count=doc["meals_count"],
                meals_details=doc["meals_details"],
                water_intake=doc["water_intake"],
                sleep_hours=doc["sleep_hours"],
                time_spent=doc["time_spent"]
            ))
        return entries

# -------------------------------------------------------------------------------
# 4. CLASSE FOLLOW (remplace le modèle SQLAlchemy "Follow")
# -------------------------------------------------------------------------------
class Follow:
    def __init__(self, follower_id, followed_id, _id=None):
        self._id = _id
        self.follower_id = follower_id
        self.followed_id = followed_id

    def save(self):
        """Insère ou met à jour ce document de suivi dans MongoDB."""
        doc = {
            "follower_id": self.follower_id,
            "followed_id": self.followed_id
        }
        if self._id:
            follows_collection.update_one({"_id": self._id}, {"$set": doc})
        else:
            result = follows_collection.insert_one(doc)
            self._id = result.inserted_id

    @staticmethod
    def find_by_follower_id(follower_id):
        docs = follows_collection.find({"follower_id": follower_id})
        follows = []
        for doc in docs:
            follows.append(Follow(
                _id=doc["_id"],
                follower_id=doc["follower_id"],
                followed_id=doc["followed_id"]
            ))
        return follows

    @staticmethod
    def find_one(follower_id, followed_id):
        doc = follows_collection.find_one({
            "follower_id": follower_id,
            "followed_id": followed_id
        })
        if doc:
            return Follow(
                _id=doc["_id"],
                follower_id=doc["follower_id"],
                followed_id=doc["followed_id"]
            )
        return None

    @staticmethod
    def delete(follower_id, followed_id):
        follows_collection.delete_one({
            "follower_id": follower_id,
            "followed_id": followed_id
        })
