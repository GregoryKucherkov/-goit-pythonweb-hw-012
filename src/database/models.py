from sqlalchemy import Column, Integer, String, Boolean, Date, func, Enum as SqlEnum
from sqlalchemy.orm import mapped_column, Mapped, DeclarativeBase, relationship
from datetime import date
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.sql.schema import ForeignKey, UniqueConstraint
from typing import Optional

from enum import Enum


class Base(DeclarativeBase):
    """
    BaseClass for all database models.

    Inherits from SQLAlchemy's DeclarativeBase to allow for easy model
    creation and mapping to database tables.
    """

    pass


class Contact(Base):
    """
    Contact model represents a user's contact information.

    Attributes:
        id (int): Unique identifier for the contact.
        name (str): First name of the contact.
        lastname (str): Last name of the contact.
        email (str): Email address of the contact.
        phone (str): Phone number of the contact.
        birthdate (date): Birthdate of the contact.
        notes (str): Additional notes about the contact.
        user_id (int): Foreign key reference to the user who owns this contact.
    """

    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint("name", "lastname", "user_id", name="unique_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    lastname: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    birthdate: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str] = mapped_column(String(250))
    user_id = Column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), default=None
    )


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """
    User model represents a registered user in the system.

    Attributes:
        id (int): Unique identifier for the user.
        username (str): Username chosen by the user (must be unique).
        email (str): Email address of the user (must be unique).
        hashed_password (str): Hashed password for authentication.
        created_at (datetime): Date and time the user was created.
        avatar (str): Avatar image URL of the user (optional).
        contacts (list): List of contacts associated with the user.
        refresh_token (str): Refresh token for session management (optional).
        confirmed (bool): Flag indicating whether the user has confirmed their email.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=func.now())
    avatar = Column(String(255), nullable=True)
    contacts = relationship("Contact", backref="user")
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confirmed = Column(Boolean, default=False)
    role = Column(SqlEnum(UserRole), default=UserRole.USER, nullable=False)

    # def __repr__(self):
    #     return f"User(username={self.username}, email={self.email}, role = {self.role})"
