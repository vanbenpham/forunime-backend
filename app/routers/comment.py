# routes/comment.py

from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session, joinedload
from typing import List
from .. import models, schemas, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/comments",
    tags=['Comments']
)

def build_comment_tree(comments):
    comment_dict = {}
    for comment in comments:
        comment.replies = []
        comment_dict[comment.comment_id] = comment

    for comment in comments:
        if comment.parent_comment_id:
            parent = comment_dict.get(comment.parent_comment_id)
            if parent:
                parent.replies.append(comment)

    tree = [comment for comment in comments if comment.parent_comment_id is None]
    return tree

def has_circular_reference(db, parent_id, child_id):
    current_id = parent_id
    while current_id:
        if current_id == child_id:
            return True
        parent_comment = db.query(models.Comment).filter(
            models.Comment.comment_id == current_id
        ).first()
        if parent_comment:
            current_id = parent_comment.parent_comment_id
        else:
            break
    return False

@router.get("/{post_id}", response_model=List[schemas.CommentOut])
def get_comments(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    comments = db.query(models.Comment).options(
        joinedload(models.Comment.user)
    ).filter(
        models.Comment.post_id == post_id
    ).all()

    comment_tree = build_comment_tree(comments)
    return comment_tree

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.CommentOut)
def create_comment(
    comment: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    if comment.parent_comment_id:
        parent_comment = db.query(models.Comment).filter(
            models.Comment.comment_id == comment.parent_comment_id
        ).first()
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Parent comment not found")

        if has_circular_reference(db, comment.parent_comment_id, child_id=None):
            raise HTTPException(
                status_code=400,
                detail="Circular reference detected in comment ancestry."
            )

    new_comment = models.Comment(
        user_id=current_user.user_id,
        **comment.dict()
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    if comment.parent_comment_id:
        if has_circular_reference(db, comment.parent_comment_id, child_id=new_comment.comment_id):
            db.delete(new_comment)
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="Circular reference detected in comment ancestry."
            )

    return new_comment

@router.get("/comment/{id}", response_model=schemas.CommentOut)
def get_comment(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    comment = db.query(models.Comment).options(
        joinedload(models.Comment.user)
    ).filter(models.Comment.comment_id == id).first()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with id: {id} was not found"
        )
    return comment

@router.delete("/comment/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    comment_query = db.query(models.Comment).filter(models.Comment.comment_id == id)
    comment = comment_query.first()

    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with id: {id} does not exist"
        )

    if comment.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action"
        )

    comment_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/comment/{id}", response_model=schemas.CommentOut)
def update_comment(
    id: int,
    updated_comment: schemas.CommentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    comment_query = db.query(models.Comment).filter(models.Comment.comment_id == id)
    comment = comment_query.first()

    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with id: {id} does not exist"
        )

    if comment.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action"
        )

    comment_query.update(updated_comment.dict(exclude_unset=True), synchronize_session=False)
    db.commit()

    return comment_query.first()
