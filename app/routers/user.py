# routes/user.py

from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session, joinedload
from .. import models, schemas, utils, oauth2
from ..database import get_db
from typing import List, Optional


router = APIRouter(
    prefix="/users",
    tags=['Users']
)

@router.get("/", response_model=List[schemas.UserOut])
def get_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
    username: Optional[str] = None
):
    # If username is provided, filter by username
    if username:
        users = db.query(models.User).filter(models.User.username.ilike(f"%{username}%")).all()
        if not users:
            # Return empty list if no matches found
            return []
        return users
    
    # If no username is provided, return all users
    users = db.query(models.User).all()
    return users

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if email or username already exists
    existing_user = db.query(models.User).filter(
        (models.User.email == user.email) | (models.User.username == user.username)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )

    # Hash the password
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {id} does not exist"
        )

    return user

@router.put('/{id}', response_model=schemas.UserOut)
def update_user(
    id: int,
    updated_user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    user_query = db.query(models.User).filter(models.User.user_id == id)
    user = user_query.first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {id} does not exist"
        )

    if user.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action"
        )

    # If the user is updating the password, hash the new password
    if updated_user.password:
        hashed_password = utils.hash(updated_user.password)
        updated_user.password = hashed_password

    # Update user info
    user_query.update(updated_user.dict(exclude_unset=True), synchronize_session=False)
    db.commit()

    return user_query.first()

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    user_query = db.query(models.User).filter(models.User.user_id == id)
    user = user_query.first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {id} does not exist"
        )

    # Allow deletion if the current user is the owner or an admin
    if current_user.user_id != id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this account"
        )

    # Handling group ownership
    owned_groups = db.query(models.Group).filter(models.Group.owner_id == id).all()
    for group in owned_groups:
        if group.co_owners:
            # Promote the first co-owner to be the new owner
            new_owner = group.co_owners[0]
            group.owner_id = new_owner.user_id
            db.commit()
        else:
            # If no co-owners, delete the group
            db.delete(group)
            db.commit()

    # Remove the user from groups where they are a member
    user_groups = db.query(models.Group).filter(models.Group.members.any(models.User.user_id == id)).all()
    for group in user_groups:
        group.members.remove(user)
    db.commit()

    # Handling message deletion
    messages_sent = db.query(models.Message).filter(models.Message.sender_id == id).all()
    for message in messages_sent:
        message.content = "[deleted]"
        message.sender_id = None
    db.commit()

    # For messages where the user is the receiver, set deleted_for_receiver to True
    messages_received = db.query(models.Message).filter(models.Message.receiver_id == id).all()
    for message in messages_received:
        message.deleted_for_receiver = True
    db.commit()

    # Delete user from the database
    user_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
