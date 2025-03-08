from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///health_app.db")

# -----------------------------
# Configuration de la base de données
# -----------------------------
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# -----------------------------
# Définition des modèles de données
# -----------------------------


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    # Pour production, utilisez un hash de mot de passe
    password = Column(String)
    email = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    # Relation avec les entrées de données
    data_entries = relationship("DataEntry", back_populates="user")
    # Relations pour le suivi social
    following = relationship(
        "Follow", back_populates="follower", foreign_keys='Follow.follower_id')
    followers = relationship(
        "Follow", back_populates="followed", foreign_keys='Follow.followed_id')


class DataEntry(Base):
    __tablename__ = 'data_entries'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(DateTime, default=datetime.datetime.utcnow)
    pushups = Column(Integer)
    meals_count = Column(Integer)
    meals_details = Column(Text)  # Stocké au format JSON
    water_intake = Column(Float)   # en litres
    sleep_hours = Column(Float)
    time_spent = Column(Float)     # Temps passé sur activités (en minutes)
    user = relationship("User", back_populates="data_entries")


class Follow(Base):
    __tablename__ = 'follows'
    id = Column(Integer, primary_key=True)
    follower_id = Column(Integer, ForeignKey('users.id'))
    followed_id = Column(Integer, ForeignKey('users.id'))
    follower = relationship(
        "User", back_populates="following", foreign_keys=[follower_id])
    followed = relationship(
        "User", back_populates="followers", foreign_keys=[followed_id])


# Création des tables si elles n'existent pas déjà
Base.metadata.create_all(engine)
