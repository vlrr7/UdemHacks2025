import bcrypt
from sqlalchemy.exc import IntegrityError
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

    # Check if the username or email already exists
    if session.query(User).filter_by(username=username).first():
        return None, "Le nom d'utilisateur existe déjà."
    if session.query(User).filter_by(email=email).first():
        return None, "L'email est déjà utilisé."

    try:
        # Hash password before storing
        hashed_password = hash_password(password)
        new_user = User(username=username,
                        password=hashed_password, email=email)
        session.add(new_user)
        session.commit()
        return new_user, "Utilisateur enregistré avec succès."

    except IntegrityError as e:
        session.rollback()  # Rollback the transaction if an error occurs
        return None, "Erreur d'inscription: email ou nom d'utilisateur déjà utilisé."
