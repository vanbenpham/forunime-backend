# routes/review.py

from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from .. import models, schemas, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/reviews",
    tags=['Reviews']
)

@router.get("/", response_model=List[schemas.ReviewOut])
def get_reviews(
    search: Optional[str] = "",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    reviews_query = db.query(models.Review).options(
        joinedload(models.Review.user),
        joinedload(models.Review.comments)  # Eagerly load comments
    )

    if search:
        reviews_query = reviews_query.filter(models.Review.description.contains(search))

    reviews = reviews_query.all()
    return reviews

@router.get("/{id}", response_model=schemas.ReviewOut)
def get_review(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    review = db.query(models.Review).options(
        joinedload(models.Review.user),
        joinedload(models.Review.comments)  # Eagerly load comments
    ).filter(models.Review.review_id == id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with id: {id} was not found"
        )
    return review

# The rest of the router code remains the same


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.ReviewOut)
def create_review(
    review: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    new_review = models.Review(
        feedback_owner_id=current_user.user_id,
        **review.dict(exclude_unset=True)
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    review_with_user = db.query(models.Review).options(
        joinedload(models.Review.user)
    ).filter(models.Review.review_id == new_review.review_id).first()

    return review_with_user


@router.put("/{id}", response_model=schemas.ReviewOut)
def update_review(
    id: int,
    updated_review: schemas.ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    review_query = db.query(models.Review).filter(models.Review.review_id == id)
    review = review_query.first()

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with id: {id} does not exist"
        )

    # Authorization check: Only owner or admin can update
    if review.feedback_owner_id != current_user.user_id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform the requested action"
        )

    review_query.update(updated_review.dict(exclude_unset=True), synchronize_session=False)
    db.commit()

    updated_review_with_user = db.query(models.Review).options(
        joinedload(models.Review.user)
    ).filter(models.Review.review_id == id).first()

    return updated_review_with_user

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    review_query = db.query(models.Review).filter(models.Review.review_id == id)
    review = review_query.first()

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with id: {id} does not exist"
        )

    # Authorization check: Only owner or admin can delete
    if review.feedback_owner_id != current_user.user_id and current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform the requested action"
        )

    review_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
