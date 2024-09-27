from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash(passwod: str):
    return pwd_context.hash(passwod)

def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


