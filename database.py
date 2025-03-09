# database.py
import datetime
from bson.objectid import ObjectId
import pymongo
from werkzeug.security import generate_password_hash, check_password_hash
import streamlit as st

# -------------------------------------------------------------------------------
# 1. CONNEXION À MONGODB ATLAS
# -------------------------------------------------------------------------------
MONGO_URI = f"mongodb+srv://dbUser:{st.secrets['MONGO_DB_PASSWORD']}@healthprodb.eptzn.mongodb.net/?retryWrites=true&w=majority&appName=healthprodb"
client = pymongo.MongoClient(MONGO_URI)
db = client["healthpro"]

# Collections (équivalent des tables SQL)
users_collection = db["users"]
data_entries_collection = db["data_entries"]
follows_collection = db["follows"]

# -------------------------------------------------------------------------------
# Fonctions d'authentification
# -------------------------------------------------------------------------------
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

def update_session_state():
    user_id = st.session_state.get('user_id')
    if not user_id:
        return
    # Récupérer la dernière saisie de l'utilisateur
    entries = DataEntry.find_by_user_id(user_id)
    latest_entry = entries[0] if entries else None

    if latest_entry:
        st.session_state['age'] = latest_entry.age
        st.session_state['height'] = latest_entry.height
    else:
        st.session_state['age'] = 0
        st.session_state['height'] = 50

    try:
        if latest_entry:
            st.session_state['sexe_index'] = ["Homme", "Femme"].index(latest_entry.sexe)
        else:
            st.session_state['sexe_index'] = 0
    except ValueError:
        st.session_state['sexe_index'] = 0

# -------------------------------------------------------------------------------
# CLASSE USER
# -------------------------------------------------------------------------------
class User:
    def __init__(self, username, password, email, created_at=None, _id=None, age=25, sexe='M', weight=70, height=175):
        self._id = _id or ObjectId()
        self.age = age
        self.sexe = sexe
        self.weight = weight
        self.height = height
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
        user_data = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user_data or not check_password_hash(user_data["password"], old_password):
            return False  # Ancien mot de passe incorrect
        hashed_new_password = generate_password_hash(new_password)
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password": hashed_new_password}}
        )
        return True

# -------------------------------------------------------------------------------
# CLASSE DATAENTRY
# -------------------------------------------------------------------------------
class DataEntry:
    def __init__(self, user_id, date, age, sexe, height, weight, bmi, water, calories, sleep, activity_time, timed_up_and_go_test, amsler, hearing, _id=None):
        self._id = _id
        self.user_id = user_id
        self.date = date or datetime.datetime.utcnow()
        self.age = age
        self.sexe = sexe
        self.height = height
        self.weight = weight
        self.bmi = bmi
        self.water = water
        self.calories = calories
        self.sleep = sleep
        self.activity_time = activity_time
        self.timed_up_and_go_test = timed_up_and_go_test
        self.amsler = amsler
        self.hearing = hearing

    def save(self):
        doc = {
            "user_id": self.user_id,
            "date": self.date,
            "age": self.age,
            "sexe": self.sexe,
            "height": self.height,
            "weight": self.weight,
            "bmi": self.bmi,
            "water": self.water,
            "calories": self.calories,
            "sleep": self.sleep,
            "activity_time": self.activity_time,
            "timed_up_and_go_test": self.timed_up_and_go_test,
            "amsler": self.amsler,
            "hearing": self.hearing,
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
                user_id=doc["user_id"],
                date=doc["date"],
                age=doc["age"],
                sexe=doc["sexe"],
                height=doc["height"],
                weight=doc["weight"],
                bmi=doc["bmi"],
                water=doc["water"],
                calories=doc["calories"],
                sleep=doc["sleep"],
                activity_time=doc["activity_time"],
                timed_up_and_go_test=doc["timed_up_and_go_test"],
                amsler=doc["amsler"],
                hearing=doc["hearing"],
                _id=doc["_id"],
            ))
        return entries

# -------------------------------------------------------------------------------
# CLASSE FOLLOW
# -------------------------------------------------------------------------------
class Follow:
    def __init__(self, follower_id, followed_id, _id=None):
        self._id = _id
        self.follower_id = follower_id
        self.followed_id = followed_id

    def save(self):
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
