from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import cast, Integer
from .. import models, schemas, oauth2
from ..database import get_db
from typing import List, Optional

router = APIRouter(
    prefix="/posts",
    tags=['Posts']
)

@router.get("/", response_model=List[schemas.PostOut])
def get_posts(
    profile_user_id: Optional[int] = None, 
    thread_id: Optional[int] = None,  # New parameter for thread filtering
    search: Optional[str] = "",
    db: Session = Depends(get_db),
    current_user: int = Depends(oauth2.get_current_user)
):
    # If thread_id is provided, ignore profile_user_id
    if thread_id is not None:
        profile_user_id = None
    # If profile_user_id is still None, default to the current_user's ID
    elif profile_user_id is None:
        profile_user_id = current_user.id

    # Query to fetch posts with user info (using joinedload to load user details)
    posts_query = db.query(models.Post).options(joinedload(models.Post.user))

    # Filter by thread_id if provided
    if thread_id:
        posts_query = posts_query.filter(models.Post.thread_id == thread_id)
    # Filter by profile_user_id if thread_id is not provided
    elif profile_user_id:
        posts_query = posts_query.filter(models.Post.profile_user_id == profile_user_id)

    # Add the search filter only if search is provided
    if search:
        posts_query = posts_query.filter(models.Post.content.contains(search))

    # Fetch all posts
    posts = posts_query.all()
    
    return posts




@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.PostOut)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    new_post = models.Post(user_id=current_user.user_id, **post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    # Reload the post with the user relationship
    post_with_user = db.query(models.Post).options(joinedload(models.Post.user)).filter(models.Post.post_id == new_post.post_id).first()

    return post_with_user

@router.get("/{id}", response_model=schemas.PostOut)
def get_post(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    post = db.query(models.Post).filter(models.Post.post_id == id).first()  # Changed from user_id to post_id
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} was not found")
    return post

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.post_id == id)  # Changed from user_id to post_id
    post = post_query.first()
    
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} does not exist")

    if post.user_id != current_user.user_id:  # Corrected user_id check
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform requested action")
    
    post_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{id}", response_model=schemas.PostOut)
def update_post(id: int, updated_post: schemas.PostCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.post_id == id)  # Changed from user_id to post_id
    post = post_query.first()

    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {id} does not exist")
    
    if post.user_id != current_user.user_id:  # Corrected user_id check
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform requested action")
    
    post_query.update(updated_post.dict(), synchronize_session=False)
    db.commit()

    return post_query.first()
