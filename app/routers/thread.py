from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, oauth2
from ..database import get_db
from typing import List

router = APIRouter(
    prefix="/threads",
    tags=['Threads']
)

# Get all threads or threads by a specific user

# Get all threads or threads by a specific user
@router.get("/", response_model=List[schemas.ThreadOut])
def get_threads(user_id: int = None, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if user_id:  
        # If user_id is provided, filter threads by that user
        threads = db.query(models.Thread).filter(models.Thread.user_id == user_id).all()
    else:
        # Otherwise, return all threads
        threads = db.query(models.Thread).all()
    
    if not threads:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No threads found")
    
    return threads


# Get a specific thread by ID
@router.get("/{id}", response_model=schemas.ThreadOut)
def get_thread(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    thread = db.query(models.Thread).filter(models.Thread.thread_id == id).first()
    
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Thread with id: {id} was not found")
    
    return thread


# Create a new thread
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.ThreadOut)
def create_thread(thread: schemas.ThreadCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    new_thread = models.Thread(user_id=current_user.user_id, **thread.dict())
    db.add(new_thread)
    db.commit()
    db.refresh(new_thread)
    return new_thread


# Delete a thread by ID
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    thread_query = db.query(models.Thread).filter(models.Thread.thread_id == id)
    thread = thread_query.first()
    
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Thread with id: {id} does not exist")

    if thread.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform requested action")
    
    thread_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Update a thread by ID
@router.put("/{id}", response_model=schemas.ThreadOut)
def update_thread(id: int, updated_thread: schemas.ThreadCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    thread_query = db.query(models.Thread).filter(models.Thread.thread_id == id)
    thread = thread_query.first()

    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Thread with id: {id} does not exist")
    
    if thread.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform requested action")
    
    thread_query.update(updated_thread.dict(), synchronize_session=False)
    db.commit()

    return thread_query.first()
