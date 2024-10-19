from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.orm import relationship, backref
from .database import Base


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    profile_picture_url = Column(
        String,
        default='https://static.vecteezy.com/system/resources/thumbnails/009/292/244/small/default-avatar-icon-of-social-media-user-vector.jpg'
    )
    date_created = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text('now()')
    )
    role = Column(String, default='user')
    # Relationships
    posts = relationship(
        'Post',
        back_populates='user',
        cascade='all, delete-orphan',
        foreign_keys='Post.user_id'  # Specify the foreign key
    )
    profile_posts = relationship(
        'Post',
        back_populates='profile_user',
        foreign_keys='Post.profile_user_id'
    )
    comments = relationship('Comment', back_populates='user', cascade='all, delete-orphan')

class Post(Base):
    __tablename__ = "posts"
    post_id = Column(Integer, primary_key=True, nullable=False)
    content = Column(String, nullable=False)
    date_created = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text('now()')
    )
    photo = Column(String, nullable=True)
    profile_user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=True
    )
    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    user = relationship(
        "User",
        back_populates="posts",
        foreign_keys=[user_id]
    )
    profile_user = relationship(
        "User",
        back_populates="profile_posts",
        foreign_keys=[profile_user_id]
    )
    comments = relationship(
        'Comment',
        back_populates='post',
        cascade='all, delete-orphan'
    )

class Comment(Base):
    __tablename__ = "comments"
    comment_id = Column(Integer, primary_key=True, nullable=False)
    content = Column(String, nullable=False)
    date_created = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text('now()')
    )
    photo = Column(String, nullable=True)
    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    post_id = Column(
        Integer,
        ForeignKey("posts.post_id", ondelete="CASCADE"),
        nullable=False
    )
    parent_comment_id = Column(
        Integer,
        ForeignKey("comments.comment_id", ondelete="CASCADE"),
        nullable=True
    )
    # Relationships
    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
    replies = relationship(
        "Comment",
        backref=backref('parent', remote_side=[comment_id]),
        cascade="all, delete-orphan"
    )


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