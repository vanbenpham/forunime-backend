from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, oauth2
from ..database import get_db
from typing import List, Optional

router = APIRouter(
    prefix="/comments",
    tags=['Comments']
)

# Get comments for a specific post
@router.get("/{post_id}", response_model=List[schemas.CommentOut])
def get_comments(post_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user), limit: int = 10, skip: int = 0):
    comments = db.query(models.Comment).filter(models.Comment.post_id == post_id).limit(limit).offset(skip).all()
    return comments

# Create a comment for a specific post
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.CommentOut)
def create_comment(comment: schemas.CommentCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    new_comment = models.Comment(user_id=current_user.user_id, **comment.dict())
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

# Get a specific comment by ID
@router.get("/comment/{id}", response_model=schemas.CommentOut)
def get_comment(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    comment = db.query(models.Comment).filter(models.Comment.comment_id == id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Comment with id: {id} was not found")
    return comment

# Delete a comment by ID
@router.delete("/comment/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    comment_query = db.query(models.Comment).filter(models.Comment.comment_id == id)
    comment = comment_query.first()
    
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Comment with id: {id} does not exist")

    if comment.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform requested action")
    
    comment_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Update a comment by ID
@router.put("/comment/{id}", response_model=schemas.CommentOut)
def update_comment(id: int, updated_comment: schemas.CommentCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    comment_query = db.query(models.Comment).filter(models.Comment.comment_id == id)
    comment = comment_query.first()

    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Comment with id: {id} does not exist")
    
    if comment.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform requested action")
    
    comment_query.update(updated_comment.dict(), synchronize_session=False)
    db.commit()

    return comment_query.first()
