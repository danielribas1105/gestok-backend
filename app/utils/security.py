import bcrypt


# Hash context — uses bcrypt by default
def get_hash_password(password: str) -> str:
    """Transforms the password into a secure hash for storage in the database."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compares the entered password with the stored hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )
