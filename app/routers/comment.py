# # routes/comment.py

# from fastapi import Response, status, HTTPException, Depends, APIRouter
# from sqlalchemy.orm import Session, joinedload
# from typing import List
# from .. import models, schemas, oauth2
# from ..database import get_db

# router = APIRouter(
#     prefix="/comments",
#     tags=['Comments']
# )

# def build_comment_tree(comments):
#     comment_dict = {}
#     for comment in comments:
#         comment.replies = []
#         comment_dict[comment.comment_id] = comment

#     for comment in comments:
#         if comment.parent_comment_id:
#             parent = comment_dict.get(comment.parent_comment_id)
#             if parent:
#                 parent.replies.append(comment)

#     tree = [comment for comment in comments if comment.parent_comment_id is None]
#     return tree

# def has_circular_reference(db, parent_id, child_id):
#     current_id = parent_id
#     while current_id:
#         if current_id == child_id:
#             return True
#         parent_comment = db.query(models.Comment).filter(
#             models.Comment.comment_id == current_id
#         ).first()
#         if parent_comment:
#             current_id = parent_comment.parent_comment_id
#         else:
#             break
#     return False

# # Get comments for a post
# @router.get("/posts/{post_id}", response_model=List[schemas.CommentOut])
# def get_post_comments(
#     post_id: int,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(oauth2.get_current_user)
# ):
#     comments = db.query(models.Comment).options(
#         joinedload(models.Comment.user)
#     ).filter(
#         models.Comment.post_id == post_id
#     ).all()

#     comment_tree = build_comment_tree(comments)
#     return comment_tree

# # Get comments for a review
# @router.get("/reviews/{review_id}", response_model=List[schemas.CommentOut])
# def get_review_comments(
#     review_id: int,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(oauth2.get_current_user)
# ):
#     comments = db.query(models.Comment).options(
#         joinedload(models.Comment.user)
#     ).filter(
#         models.Comment.review_id == review_id
#     ).all()

#     comment_tree = build_comment_tree(comments)
#     return comment_tree

# # Create a comment for a post or review
# @router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.CommentOut)
# def create_comment(
#     comment: schemas.CommentCreate,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(oauth2.get_current_user)
# ):
#     if not comment.post_id and not comment.review_id:
#         raise HTTPException(
#             status_code=400,
#             detail="Either post_id or review_id must be provided."
#         )

#     if comment.post_id and comment.review_id:
#         raise HTTPException(
#             status_code=400,
#             detail="Only one of post_id or review_id should be provided."
#         )

#     if comment.parent_comment_id:
#         parent_comment = db.query(models.Comment).filter(
#             models.Comment.comment_id == comment.parent_comment_id
#         ).first()
#         if not parent_comment:
#             raise HTTPException(status_code=404, detail="Parent comment not found")

#         if has_circular_reference(db, comment.parent_comment_id, child_id=None):
#             raise HTTPException(
#                 status_code=400,
#                 detail="Circular reference detected in comment ancestry."
#             )

#     new_comment = models.Comment(
#         user_id=current_user.user_id,
#         **comment.dict()
#     )
#     db.add(new_comment)
#     db.commit()
#     db.refresh(new_comment)

#     if comment.parent_comment_id:
#         if has_circular_reference(db, comment.parent_comment_id, child_id=new_comment.comment_id):
#             db.delete(new_comment)
#             db.commit()
#             raise HTTPException(
#                 status_code=400,
#                 detail="Circular reference detected in comment ancestry."
#             )

#     # Load user data
#     new_comment.user = current_user

#     return new_comment

# # Get a specific comment
# @router.get("/comment/{id}", response_model=schemas.CommentOut)
# def get_comment(
#     id: int,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(oauth2.get_current_user)
# ):
#     comment = db.query(models.Comment).options(
#         joinedload(models.Comment.user)
#     ).filter(models.Comment.comment_id == id).first()
#     if not comment:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Comment with id: {id} was not found"
#         )
#     return comment

# # Delete a comment
# @router.delete("/comment/{id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_comment(
#     id: int,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(oauth2.get_current_user)
# ):
#     comment_query = db.query(models.Comment).filter(models.Comment.comment_id == id)
#     comment = comment_query.first()

#     if comment is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Comment with id: {id} does not exist"
#         )

#     # Allow deletion if the user is the owner or an admin
#     if comment.user_id != current_user.user_id and current_user.role != 'admin':
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not authorized to perform the requested action"
#         )

#     comment_query.delete(synchronize_session=False)
#     db.commit()

#     return Response(status_code=status.HTTP_204_NO_CONTENT)

# # Update a comment
# @router.put("/comment/{id}", response_model=schemas.CommentOut)
# def update_comment(
#     id: int,
#     updated_comment: schemas.CommentUpdate,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(oauth2.get_current_user)
# ):
#     comment_query = db.query(models.Comment).filter(models.Comment.comment_id == id)
#     comment = comment_query.first()

#     if comment is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Comment with id: {id} does not exist"
#         )

#     # Allow update if the user is the owner or an admin
#     if comment.user_id != current_user.user_id and current_user.role != 'admin':
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not authorized to perform the requested action"
#         )

#     comment_query.update(updated_comment.dict(exclude_unset=True), synchronize_session=False)
#     db.commit()

#     updated_comment = comment_query.first()
#     return updated_comment


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

def update_review_rate(review_id: int, db: Session):
    pass

# Get comments for a post
@router.get("/posts/{post_id}", response_model=List[schemas.CommentOut])
def get_post_comments(
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

# Get comments for a review
@router.get("/reviews/{review_id}", response_model=List[schemas.CommentOut])
def get_review_comments(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    comments = db.query(models.Comment).options(
        joinedload(models.Comment.user)
    ).filter(
        models.Comment.review_id == review_id
    ).all()

    comment_tree = build_comment_tree(comments)
    return comment_tree

# Create a comment for a post or review
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.CommentOut)
def create_comment(
    comment: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    if not comment.post_id and not comment.review_id:
        raise HTTPException(
            status_code=400,
            detail="Either post_id or review_id must be provided."
        )

    if comment.post_id and comment.review_id:
        raise HTTPException(
            status_code=400,
            detail="Only one of post_id or review_id should be provided."
        )

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

    # Update the review's rate after adding the comment
    if comment.review_id:
        update_review_rate(comment.review_id, db)

    # Load user data
    new_comment.user = current_user

    return new_comment

# Get a specific comment
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

# Delete a comment
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

    # Allow deletion if the user is the owner or an admin
    if comment.user_id != current_user.user_id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform the requested action"
        )

    review_id = comment.review_id
    comment_query.delete(synchronize_session=False)
    db.commit()

    # Update the review's rate after deleting the comment
    if review_id:
        update_review_rate(review_id, db)

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Update a comment
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

    # Allow update if the user is the owner or an admin
    if comment.user_id != current_user.user_id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform the requested action"
        )

    comment_query.update(updated_comment.dict(exclude_unset=True), synchronize_session=False)
    db.commit()

    # Update the review's rate after updating the comment
    if comment.review_id:
        update_review_rate(comment.review_id, db)

    updated_comment = comment_query.first()
    return updated_comment
