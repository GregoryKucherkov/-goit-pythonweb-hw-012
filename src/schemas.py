from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator
from typing import Optional

# from enum import Enum

from src.database.models import UserRole


class ContactBase(BaseModel):
    """
    Schema for creating or updating a contact.

    Attributes:
        name (str): First name of the contact (max 50 characters).
        lastname (str): Last name of the contact (max 50 characters).
        email (EmailStr): Email address of the contact.
        phone (str): Phone number of the contact (6 to 20 characters).
        birthdate (date): Birthdate of the contact.
        notes (Optional[str]): Additional notes about the contact (optional).
    """

    name: str = Field(..., max_length=50)
    lastname: str = Field(..., max_length=50)
    email: EmailStr
    phone: str = Field(min_length=6, max_length=20)
    birthdate: date
    notes: Optional[str] = None

    @field_validator("birthdate")
    def validate_birthday(cls, v):
        """
        Validator to ensure the birthdate is not in the future.

        Args:
            v (date): The birthdate value to validate.

        Raises:
            ValueError: If the birthdate is in the future.

        Returns:
            date: The validated birthdate.
        """
        if v > date.today():
            raise ValueError("Birthday cannot be in the future")
        return v


class ContactUpdate(BaseModel):
    """
    Schema for updating an existing contact. All fields are optional.

    Attributes:
        name (Optional[str]): First name of the contact (max 50 characters, optional).
        lastname (Optional[str]): Last name of the contact (max 50 characters, optional).
        email (Optional[EmailStr]): Email address of the contact (optional).
        phone (Optional[str]): Phone number of the contact (optional).
        birthdate (Optional[date]): Birthdate of the contact (optional).
        notes (Optional[str]): Additional notes about the contact (optional).
    """

    name: Optional[str] = Field(None, max_length=50)
    lastname: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    birthdate: Optional[date] = None
    notes: Optional[str] = None


class ContactResponse(ContactBase):
    """
    Schema for representing a contact response, including the contact ID.

    Inherits from `ContactBase` and includes the ID of the contact.

    Attributes:
        id (int): The unique identifier for the contact.
    """

    id: int

    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    """
    Schema for representing a user.

    Attributes:
        id (int): The unique identifier for the user.
        username (str): The username of the user.
        email (str): The email address of the user.
        avatar (str): URL of the user's avatar image.
    """

    id: int
    username: str
    email: str
    avatar: str

    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    # id: Optional[int]
    username: Optional[str]
    email: Optional[str]
    avatar: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# class UserRole(str, Enum):
#     USER = "user"
#     MODERATOR = "moderator"
#     ADMIN = "admin"


class UserCreate(BaseModel):
    """
    Schema for creating a new user.

    Attributes:
        username (str): The username of the new user.
        email (str): The email address of the new user.
        password (str): The password for the new user.
    """

    username: str
    email: str
    password: str


class Token(BaseModel):
    """
    Schema for representing authentication tokens.

    Attributes:
        access_token (str): The access token for authentication.
        refresh_token (str): The refresh token for obtaining new access tokens.
        token_type (str): The type of the token (usually 'bearer').
    """

    access_token: str
    refresh_token: str
    token_type: str


class TokenRefreshRequest(BaseModel):
    """
    Schema for requesting a token refresh.

    Attributes:
        refresh_token (str): The refresh token used to obtain a new access token.
    """

    refresh_token: str


class RequestEmail(BaseModel):
    """
    Schema for representing an email request, typically used for sending password resets or similar actions.

    Attributes:
        email (EmailStr): The email address to perform the action on.
    """

    email: EmailStr
