from fastapi import Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session, joinedload
from typing import List
from .. import models, schemas, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/groups",
    tags=['Groups']
)

@router.get("/", response_model=List[schemas.GroupOut])
def get_groups(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    groups = db.query(models.Group).options(
        joinedload(models.Group.members), 
        joinedload(models.Group.co_owners), 
        joinedload(models.Group.owner)
    ).all()
    return groups

@router.get("/{id}", response_model=schemas.GroupOut)
def get_group(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    group = db.query(models.Group).options(
        joinedload(models.Group.members), 
        joinedload(models.Group.co_owners), 
        joinedload(models.Group.owner)
    ).filter(models.Group.group_id == id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with id: {id} was not found"
        )
    return group

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.GroupOut)
def create_group(
    group: schemas.GroupCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # Ensure the owner is part of the members
    member_ids = set(group.member_ids)
    member_ids.add(current_user.user_id)  # Include owner

    # Fetch all users to add
    users = db.query(models.User).filter(models.User.user_id.in_(member_ids)).all()

    if len(users) != len(member_ids):
        existing_ids = {user.user_id for user in users}
        missing_ids = member_ids - existing_ids
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Users with IDs {missing_ids} do not exist."
        )

    new_group = models.Group(
        group_name=group.group_name,
        owner_id=current_user.user_id,
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    # Add members to the group
    new_group.members.extend(users)
    db.commit()

    # Fetch the group with all relationships
    group_with_members = db.query(models.Group).options(
        joinedload(models.Group.members), 
        joinedload(models.Group.co_owners), 
        joinedload(models.Group.owner)
    ).filter(models.Group.group_id == new_group.group_id).first()
    return group_with_members

@router.put("/{id}", response_model=schemas.GroupOut)
def update_group(
    id: int,
    updated_group: schemas.GroupUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    group_query = db.query(models.Group).filter(models.Group.group_id == id)
    group = group_query.first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with id: {id} does not exist"
        )

    if group.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform the requested action"
        )

    if updated_group.group_name:
        group_query.update({"group_name": updated_group.group_name}, synchronize_session=False)

    if updated_group.add_member_ids:
        for member_id in updated_group.add_member_ids:
            user = db.query(models.User).filter(models.User.user_id == member_id).first()
            if user and user not in group.members:
                group.members.append(user)

    if updated_group.remove_member_ids:
        for member_id in updated_group.remove_member_ids:
            user = db.query(models.User).filter(models.User.user_id == member_id).first()
            if user and user in group.members:
                group.members.remove(user)

    if updated_group.add_co_owner_ids:
        for co_owner_id in updated_group.add_co_owner_ids:
            user = db.query(models.User).filter(models.User.user_id == co_owner_id).first()
            if user and user not in group.co_owners:
                group.co_owners.append(user)

    if updated_group.remove_co_owner_ids:
        for co_owner_id in updated_group.remove_co_owner_ids:
            user = db.query(models.User).filter(models.User.user_id == co_owner_id).first()
            if user and user in group.co_owners:
                group.co_owners.remove(user)

    db.commit()

    updated_group_with_members = db.query(models.Group).options(
        joinedload(models.Group.members), 
        joinedload(models.Group.co_owners), 
        joinedload(models.Group.owner)
    ).filter(models.Group.group_id == id).first()

    return updated_group_with_members

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    group_query = db.query(models.Group).filter(models.Group.group_id == id)
    group = group_query.first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with id: {id} does not exist"
        )

    if group.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this group"
        )

    group_query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
