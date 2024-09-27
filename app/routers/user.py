from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, utils, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/users",
    tags=['Users']
)

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed_password = utils.hash(user.password)
    user.password = hashed_password

    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get('/{id}', response_model=schemas.UserOut)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {id} does not exist")

    # Ensure the date_created is formatted as YYYY-MM-DD
    user_data = {
        "user_id": user.user_id,
        "email": user.email,
        "username": user.username,
        "date_created": user.date_created.date().isoformat(),  # Strictly format as YYYY-MM-DD
        "profile_picture_url": user.profile_picture_url
    }

    return user_data




@router.put('/{id}', response_model=schemas.UserOut)
def update_user(id: int, updated_user: schemas.UserUpdate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    user_query = db.query(models.User).filter(models.User.user_id == id)
    user = user_query.first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {id} does not exist")

    if user.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform requested action")

    # If the user is updating the password, hash the new password
    if updated_user.password:
        hashed_password = utils.hash(updated_user.password)
        updated_user.password = hashed_password

    # Update user info
    user_query.update(updated_user.dict(exclude_unset=True), synchronize_session=False)
    db.commit()

    return user_query.first()


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    user_query = db.query(models.User).filter(models.User.user_id == id)
    user = user_query.first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {id} does not exist")

    # Print statements for debugging
    print(f"Current user: {current_user.user_id}, User to delete: {user.user_id}")
    
    # Check if the current user is the owner or admin
    if current_user.user_id != id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this account")

    # Delete user from the database
    user_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)