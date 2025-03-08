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


def login(username: str, password: str):
    """Authenticates a user by checking the password hash."""
    user = session.query(User).filter_by(username=username).first()
    if user and bcrypt.checkpw(password.encode(), user.password.encode()):
        return user  # Login successful
    return None  # Login failed


def register(username: str, password: str, email: str):
    """Registers a new user with a hashed password."""
    if session.query(User).filter_by(username=username).first():
        return None, "Le nom d'utilisateur existe déjà."

    hashed_password = hash_password(password)  # Hash password before storing
    new_user = User(username=username, password=hashed_password, email=email)
    session.add(new_user)
    session.commit()

    return new_user, "Utilisateur enregistré avec succès."
