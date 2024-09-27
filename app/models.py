from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    profile_picture_url = Column(String, default='https://static.vecteezy.com/system/resources/thumbnails/009/292/244/small/default-avatar-icon-of-social-media-user-vector.jpg')
    date_created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    role = Column(String, default='user')


class Post(Base):
    __tablename__ = "posts"
    post_id = Column(Integer, primary_key=True, nullable=False)
    content = Column(String, nullable=False)
    date_created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    photo = Column(String, nullable=True)
    profile_user_id = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    thread_id = Column(Integer, ForeignKey("threads.thread_id", ondelete="CASCADE"), nullable=True)
    user = relationship("User", backref="posts")


class Comment(Base):
    __tablename__ = "comments"
    comment_id = Column(Integer, primary_key=True, nullable=False)
    content = Column(String, nullable=False)
    date_created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    photo = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.post_id", ondelete="CASCADE"), nullable=False)


class Thread(Base):
    __tablename__ = "threads"
    thread_id = Column(Integer, primary_key=True, nullable=False)
    thread_name = Column(String, nullable=False)
    date_created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)

class Message(Base):
    __tablename__ = "messages"
    message_id = Column(Integer, primary_key=True, nullable=False)
    content = Column(String, nullable=False)
    photo = Column(String, nullable=True)
    date_created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    user_id_sender = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    user_id_receiver = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)


class Rating(Base):
    __tablename__ = "ratings"
    rating_id = Column(Integer, primary_key=True, nullable=False)
    description = Column(String, nullable=False)
    feedback = Column(String, nullable=True)
    rate = Column(Integer, nullable=False)
    date_created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    post_owner_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.post_id", ondelete="CASCADE"), nullable=False)
    feedback_owner_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)