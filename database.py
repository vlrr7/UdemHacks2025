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
    
    @staticmethod
    def find_by_id(user_id):
        return users_collection.find_one({"_id": ObjectId(user_id)})

    @staticmethod
    def update_password(user_id, old_password, new_password):
        """Updates the user's password if the old password matches."""
        user_data = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user_data or not check_password_hash(user_data["password"], old_password):
            return False  # Incorrect old password

        # Hash the new password
        hashed_new_password = generate_password_hash(new_password)

        # Update the password in MongoDB
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password": hashed_new_password}}
        )
        return True  # Password updated successfully


# -------------------------------------------------------------------------------
# 2. CLASSE DATAENTRY (version modifiée)
# -------------------------------------------------------------------------------
class DataEntry:
    def __init__(self, user_id, **kwargs):
        self.user_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
        self.date = kwargs.get('date') or datetime.datetime.utcnow()
        
        # Nouveaux champs généraux
        self.age = kwargs.get('age', 0)
        self.height = kwargs.get('height', 0)  # Taille en cm
        self.weight = kwargs.get('weight', 0.0)  # Poids en kg
        self.bmi = kwargs.get('bmi', 0.0)  # Calculé automatiquement
        
        # Données quotidiennes
        self.water = kwargs.get('water', 0.0)  # Eau en litres
        self.calories = kwargs.get('calories', 0)  # Calories consommées
        self.sleep = kwargs.get('sleep', 0.0)  # Heures de sommeil
        self.activity_time = kwargs.get('activity_time', 0)  # Temps d'activité en min
        
        # Données pour seniors (optionnelles)
        self.timed_up_and_go_test = kwargs.get('timed_up_and_go_test', 0.0)  # Test timed_up_and_go_test en secondes
        self.amsler = kwargs.get('amsler', "Normal")  # Résultat Amsler
        self.hearing = kwargs.get('hearing', "Normal")  # Résultat auditif
        
        self._id = kwargs.get('_id', ObjectId())

    def save(self):
        doc = {
            "user_id": self.user_id,
            "date": self.date,
            "age": self.age,
            "height": self.height,
            "weight": self.weight,
            "bmi": self.bmi,
            "water": self.water,
            "calories": self.calories,
            "sleep": self.sleep,
            "activity_time": self.activity_time,
            "timed_up_and_go_test": self.timed_up_and_go_test,
            "amsler": self.amsler,
            "hearing": self.hearing
        }
        if self._id:
            data_entries_collection.update_one({"_id": self._id}, {"$set": doc})
        else:
            result = data_entries_collection.insert_one(doc)
            self._id = result.inserted_id
            print(f"DataEntry inserted with id: {self._id}")
        print(f"DataEntry saved: {doc}")

    @staticmethod
    def find_by_user_id(user_id):
        docs = data_entries_collection.find({"user_id": ObjectId(user_id)}).sort("date", -1)
        entries = []
        for doc in docs:
            entries.append(DataEntry(
                user_id=doc["user_id"],
                date=doc["date"],
                age=doc.get("age", 0),
                height=doc.get("height", 0),
                weight=doc.get("weight", 0.0),
                bmi=doc.get("bmi", 0.0),
                water=doc.get("water", 0.0),
                calories=doc.get("calories", 0),
                sleep=doc.get("sleep", 0.0),
                activity_time=doc.get("activity_time", 0),
                timed_up_and_go_test=doc.get("timed_up_and_go_test", 0.0),
                amsler=doc.get("amsler", "Normal"),
                hearing=doc.get("hearing", "Normal"),
                _id=doc["_id"]
            ))
        return entries
# -------------------------------------------------------------------------------
# 3. CLASSE FOLLOW (remplace le modèle SQLAlchemy "Follow")
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
    
