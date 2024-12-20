from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from .database import Base

# Association Table for Group Members
group_members = Table(
    "group_members",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("groups.group_id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.user_id"), primary_key=True)
)

# Association Table for Group Co-Owners
group_co_owners = Table(
    "group_co_owners",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("groups.group_id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.user_id"), primary_key=True)
)

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
        foreign_keys='Post.user_id'
    )
    profile_posts = relationship(
        'Post',
        back_populates='profile_user',
        foreign_keys='Post.profile_user_id'
    )
    comments = relationship('Comment', back_populates='user', cascade='all, delete-orphan')

    reviews = relationship(
        'Review',
        back_populates='user',
        cascade='all, delete-orphan',
        foreign_keys='Review.feedback_owner_id'
    )
    
    # Relationships for Groups and Messages
    messages_sent = relationship("Message", foreign_keys='Message.sender_id', back_populates="sender")
    messages_received = relationship("Message", foreign_keys='Message.receiver_id', back_populates="receiver")
    owned_groups = relationship("Group", foreign_keys='Group.owner_id', back_populates="owner")
    groups = relationship("Group", secondary="group_members", back_populates="members")
    co_owned_groups = relationship("Group", secondary="group_co_owners", back_populates="co_owners")

class Group(Base):
    __tablename__ = "groups"
    group_id = Column(Integer, primary_key=True, nullable=False)
    group_name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    date_created = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text('now()')
    )

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_groups")
    members = relationship("User", secondary=group_members, back_populates="groups")
    co_owners = relationship("User", secondary=group_co_owners, back_populates="co_owned_groups")

class Message(Base):
    __tablename__ = "messages"
    message_id = Column(Integer, primary_key=True, nullable=False)
    content = Column(String, nullable=False)
    photo = Column(String, nullable=True)
    date_created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    sender_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.group_id"), nullable=True)
    deleted_for_receiver = Column(Boolean, default=False)
    
    # Add these relationships to match what's in User model
    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="messages_received")
    group = relationship("Group", backref="messages")


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
    thread_id = Column(
        Integer,
        ForeignKey("threads.thread_id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Relationships
    user = relationship("User", back_populates="posts", foreign_keys=[user_id])
    profile_user = relationship("User", back_populates="profile_posts", foreign_keys=[profile_user_id])
    comments = relationship('Comment', back_populates='post', cascade='all, delete-orphan')
    thread = relationship('Thread', back_populates='posts', foreign_keys=[thread_id])

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
        nullable=True
    )
    review_id = Column(
        Integer,
        ForeignKey("reviews.review_id", ondelete="CASCADE"),
        nullable=True
    )
    parent_comment_id = Column(
        Integer,
        ForeignKey("comments.comment_id", ondelete="CASCADE"),
        nullable=True
    )
    rate = Column(Integer, nullable=True)  # Add this line

    # Relationships
    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
    review = relationship("Review", back_populates="comments")
    replies = relationship(
        "Comment",
        backref=backref('parent', remote_side=[comment_id]),
        cascade="all, delete-orphan"
    )


class Thread(Base):
    __tablename__ = "threads"
    thread_id = Column(Integer, primary_key=True, nullable=False)
    thread_name = Column(String, nullable=False, unique=True)
    date_created = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text('now()')
    )
    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Relationships
    posts = relationship('Post', back_populates='thread', cascade='all, delete-orphan')
    
    __table_args__ = (
        UniqueConstraint('thread_name', name='unique_thread_name'),
    )




# models.py

class Review(Base):
    __tablename__ = "reviews"
    review_id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    feedback = Column(String, nullable=True)
    date_created = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text('now()')
    )
    feedback_owner_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    photo_url = Column(String, nullable=True)

    # Relationships
    comments = relationship(
        "Comment",
        back_populates="review",
        cascade="all, delete-orphan"
    )

    # Relationship to the user who wrote the review
    user = relationship(
        "User",
        back_populates="reviews",
        foreign_keys=[feedback_owner_id]
    )

    # Computed properties
    @property
    def review_count(self):
        return len(self.comments)

    @property
    def average_rate(self):
        rates = [comment.rate for comment in self.comments if comment.rate is not None]
        return sum(rates) / len(rates) if rates else 0


