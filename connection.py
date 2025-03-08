import bcrypt
from database import session, User


def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    return hashed_password.decode()

# -----------------------------
# Fonctions d'authentification
# -----------------------------
def login(username, password):
    user = session.query(User).filter_by(
        username=username, password=password).first()
    return user


def register(username, password, email):
    if session.query(User).filter_by(username=username).first():
        return None, "Le nom d'utilisateur existe déjà."
    new_user = User(username=username, password=password, email=email)
    session.add(new_user)
    session.commit()
    return new_user, "Utilisateur enregistré avec succès."
