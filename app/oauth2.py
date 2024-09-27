from jose import JWTError, jwt
from datetime import datetime, timedelta
from . import schemas, database, models
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings

# OAuth2 password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

# Secret key, algorithm, and expiration time
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "user_id": data["user_id"]})  # Ensure "user_id" is in the token payload
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception  # Invalid token if no user_id is found
        token_data = schemas.TokenData(id=str(user_id))

    except JWTError as e:
        print(f"JWTError occurred: {str(e)}")  # Print for debugging
        raise credentials_exception
 
    return token_data


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    print(f"Received token: {token}")  # Check the token received in the request
    token_data = verify_access_token(token, credentials_exception)
    print(f"Token data: {token_data}")  # Check what is decoded from the token

    user = db.query(models.User).filter(models.User.user_id == token_data.id).first()
    if user is None:
        raise credentials_exception

    print(f"Authenticated user: {user}")  # Ensure a user is found
    return user

