from fastapi import Response, status, HTTPException, Depends, APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from .. import models, schemas, oauth2
from ..database import get_db

router = APIRouter(
    prefix="/messages",
    tags=['Messages']
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}  # Maps user_id to WebSocket

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json(message)

    async def broadcast_to_group(self, message: dict, group_id: int, db: Session):
        # Fetch all group members
        group = db.query(models.Group).filter(models.Group.group_id == group_id).first()
        if group:
            for member in group.members:
                websocket = self.active_connections.get(member.user_id)
                if websocket:
                    await websocket.send_json(message)


manager = ConnectionManager()

@router.websocket("/ws/messages/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            # Determine if the message is for a group or personal chat
            if 'group_id' in data and data['group_id']:
                await manager.broadcast_to_group(data, data['group_id'], db)
            else:
                # For personal messages, send to the receiver
                receiver_id = data.get('receiver_id')
                if receiver_id:
                    await manager.send_personal_message(data, receiver_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)



@router.get("/chat-list", response_model=List[schemas.UserOut])
def get_chatted_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    # Query messages where current_user is sender or receiver and collect unique users
    messages = db.query(models.Message).filter(
        (models.Message.sender_id == current_user.user_id) | 
        (models.Message.receiver_id == current_user.user_id)
    ).all()

    chatted_user_ids = set()
    for msg in messages:
        if msg.sender_id != current_user.user_id:
            chatted_user_ids.add(msg.sender_id)
        if msg.receiver_id and msg.receiver_id != current_user.user_id:
            chatted_user_ids.add(msg.receiver_id)
    
    if chatted_user_ids:
        users = db.query(models.User).filter(models.User.user_id.in_(chatted_user_ids)).all()
    else:
        users = []
    return users

@router.get("/", response_model=List[schemas.MessageOut])
def get_messages(
    group_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    if group_id:
        # Verify that the current user is a member of the group
        group = db.query(models.Group).filter(models.Group.group_id == group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Group with id: {group_id} not found."
            )
        if current_user not in group.members and current_user != group.owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this group."
            )

        # Fetch all messages associated with the group
        messages = db.query(models.Message).options(
            joinedload(models.Message.sender),
            joinedload(models.Message.receiver),
            joinedload(models.Message.group)
        ).filter(models.Message.group_id == group_id).order_by(models.Message.date_created.asc()).all()
    else:
        # Fetch one-on-one messages where the user is either sender or receiver
        messages = db.query(models.Message).options(
            joinedload(models.Message.sender),
            joinedload(models.Message.receiver),
            joinedload(models.Message.group)
        ).filter(
            (models.Message.sender_id == current_user.user_id) | 
            (models.Message.receiver_id == current_user.user_id)
        ).order_by(models.Message.date_created.asc()).all()
    
    return messages




@router.get("/{id}", response_model=schemas.MessageOut)
def get_message(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    message = db.query(models.Message).options(
        joinedload(models.Message.sender),
        joinedload(models.Message.receiver),
        joinedload(models.Message.group)
    ).filter(
        models.Message.message_id == id,
        (models.Message.sender_id == current_user.user_id) | 
        (models.Message.receiver_id == current_user.user_id)
    ).first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message with id: {id} was not found"
        )
    return message




@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.MessageOut)
async def create_message(
    message: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    if message.group_id:
        # Validate that the group exists
        group = db.query(models.Group).filter(models.Group.group_id == message.group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found."
            )
        # Validate that the current user is a member of the group
        if current_user not in group.members and current_user != group.owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this group."
            )
        # Ensure receiver_id is not set for group messages
        if message.receiver_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot set receiver_id for group messages."
            )
    else:
        # For one-on-one messages, ensure receiver exists
        if not message.receiver_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="receiver_id is required for one-on-one messages."
            )
        receiver = db.query(models.User).filter(models.User.user_id == message.receiver_id).first()
        if not receiver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receiver not found."
            )
    
    new_message = models.Message(
        sender_id=current_user.user_id,
        **message.dict(exclude_unset=True)
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    message_with_details = db.query(models.Message).options(
        joinedload(models.Message.sender),
        joinedload(models.Message.receiver),
        joinedload(models.Message.group)
    ).filter(models.Message.message_id == new_message.message_id).first()
    
    # Broadcast the new message
    if message_with_details.group:
        await manager.broadcast_to_group({
            "message_id": message_with_details.message_id,
            "content": message_with_details.content,
            "date_created": message_with_details.date_created.isoformat(),
            "sender": {
                "user_id": message_with_details.sender.user_id,
                "username": message_with_details.sender.username,
                "profile_picture_url": message_with_details.sender.profile_picture_url
            },
            "group": {
                "group_id": message_with_details.group.group_id,
                "group_name": message_with_details.group.group_name
            }
        }, message_with_details.group.group_id, db)
    elif message_with_details.receiver:
        await manager.send_personal_message({
            "message_id": message_with_details.message_id,
            "content": message_with_details.content,
            "date_created": message_with_details.date_created.isoformat(),
            "sender": {
                "user_id": message_with_details.sender.user_id,
                "username": message_with_details.sender.username,
                "profile_picture_url": message_with_details.sender.profile_picture_url
            },
            "receiver": {
                "user_id": message_with_details.receiver.user_id,
                "username": message_with_details.receiver.username,
                "profile_picture_url": message_with_details.receiver.profile_picture_url
            }
        }, message_with_details.receiver.user_id)

    return message_with_details




@router.put("/{id}", response_model=schemas.MessageOut)
def update_message(
    id: int,
    updated_message: schemas.MessageUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    message_query = db.query(models.Message).filter(models.Message.message_id == id)
    message = message_query.first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message with id: {id} does not exist"
        )

    if message.sender_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this message"
        )

    message_query.update(updated_message.dict(exclude_unset=True), synchronize_session=False)
    db.commit()

    return message_query.first()

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    message_query = db.query(models.Message).filter(models.Message.message_id == id)
    message = message_query.first()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message with id: {id} does not exist"
        )

    if message.sender_id == current_user.user_id:
        message_query.delete(synchronize_session=False)
    elif message.receiver_id == current_user.user_id:
        message.deleted_for_receiver = True
        db.commit()
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this message"
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)