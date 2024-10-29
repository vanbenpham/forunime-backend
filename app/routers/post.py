# routes/post.py

from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session, joinedload, subqueryload
from typing import List, Optional
from .. import models, schemas, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/posts",
    tags=['Posts']
)

@router.get("/", response_model=List[schemas.PostOut])
def get_posts(
    thread_id: Optional[int] = None,
    profile_user_id: Optional[int] = None,
    search: Optional[str] = "",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    posts_query = db.query(models.Post).options(
        joinedload(models.Post.user),
        subqueryload(models.Post.comments).joinedload(models.Comment.replies),
        joinedload(models.Post.thread)
    )

    if thread_id is not None:
        posts_query = posts_query.filter(models.Post.thread_id == thread_id)
    elif profile_user_id is not None:
        posts_query = posts_query.filter(models.Post.profile_user_id == profile_user_id)
    else:
        posts_query = posts_query.filter(models.Post.thread_id == None)

    if search:
        posts_query = posts_query.filter(models.Post.content.contains(search))

    posts = posts_query.all()
    return posts

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.PostOut)
def create_post(
    post: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    if post.thread_id:
        thread = db.query(models.Thread).filter(models.Thread.thread_id == post.thread_id).first()
        if not thread:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    new_post = models.Post(
        user_id=current_user.user_id,
        **post.dict(exclude_unset=True)
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    post_with_user = db.query(models.Post).options(
        joinedload(models.Post.user),
        subqueryload(models.Post.comments).joinedload(models.Comment.replies),
        joinedload(models.Post.thread)
    ).filter(models.Post.post_id == new_post.post_id).first()

    return post_with_user

@router.get("/{id}", response_model=schemas.PostOut)
def get_post(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    post = db.query(models.Post).options(
        joinedload(models.Post.user),
        subqueryload(models.Post.comments).joinedload(models.Comment.replies)
    ).filter(models.Post.post_id == id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id: {id} was not found"
        )
    return post

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    post_query = db.query(models.Post).filter(models.Post.post_id == id)
    post = post_query.first()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id: {id} does not exist"
        )

    # Allow deletion if the user is the owner or an admin
    if post.user_id != current_user.user_id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform the requested action"
        )

    post_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{id}", response_model=schemas.PostOut)
def update_post(
    id: int,
    updated_post: schemas.PostUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    post_query = db.query(models.Post).filter(models.Post.post_id == id)
    post = post_query.first()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id: {id} does not exist"
        )

    # Allow update if the user is the owner or an admin
    if post.user_id != current_user.user_id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform the requested action"
        )

    post_query.update(updated_post.dict(exclude_unset=True), synchronize_session=False)
    db.commit()

    updated_post_with_user = db.query(models.Post).options(
        joinedload(models.Post.user),
        subqueryload(models.Post.comments).joinedload(models.Comment.replies)
    ).filter(models.Post.post_id == id).first()

    return updated_post_with_user
