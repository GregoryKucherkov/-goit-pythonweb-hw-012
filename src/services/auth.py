from datetime import datetime, timedelta, UTC
from typing import Optional, Literal


from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError, ExpiredSignatureError
from src.schemas import User

from src.database.db import get_db
from src.database.models import UserRole, User as UserSQLAlchemy
from src.config.config import settings
from src.services.users import UserService

import redis
import json

# Connecting to Redis
r = redis.Redis(host="localhost", port=6379, db=0)


class Hash:
    """
    A utility class for hashing passwords and verifying password hashes using bcrypt.

    Methods:
        verify_pass(plain_pass, hashed_pass): Verifies if a plain password matches the hashed password.
        get_pass_hash(password): Hashes a given plain password.
    """

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_pass(self, plain_pass, hashed_pass):
        """
        Verifies if a plain password matches the hashed password.

        Args:
            plain_pass (str): The plain password to check.
            hashed_pass (str): The hashed password to compare against.

        Returns:
            bool: True if the passwords match, otherwise False.
        """
        return self.pwd_context.verify(plain_pass, hashed_pass)

    def get_pass_hash(self, password: str):
        """
        Hashes a plain password.

        Args:
            password (str): The plain password to hash.

        Returns:
            str: The hashed password.
        """
        return self.pwd_context.hash(password)


# OAuth2 password bearer token for authentication
oath2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def create_token(
    data: dict, expires_delta: timedelta, token_type: Literal["access", "refresh"]
):
    """
    Creates a JWT token with the given data and expiration time.

    Args:
        data (dict): The data to encode into the token.
        expires_delta (timedelta): The expiration time of the token.
        token_type (Literal["access", "refresh"]): The type of the token, either "access" or "refresh".

    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + expires_delta
    to_encode.update({"exp": expire, "iat": now, "token_type": token_type})
    encode_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encode_jwt


async def create_access_token(data: dict, expires_delta: Optional[float] = None):
    """
    Creates an access token for the user.

    Args:
        data (dict): The data to encode into the token.
        expires_delta (Optional[float]): Optional expiration time in seconds. Defaults to None.

    Returns:
        str: The generated access token.
    """
    if expires_delta:
        access_token = await create_token(data, expires_delta, "access")
    else:
        access_token = await create_token(
            data, timedelta(seconds=settings.JWT_EXPIRATION_SECONDS), "access"
        )
        return access_token


async def create_refresh_token(data: dict, expires_delta: Optional[int] = None):
    """
    Creates a refresh token for the user.

    Args:
        data (dict): The data to encode into the token.
        expires_delta (Optional[int]): Optional expiration time in seconds. Defaults to None.

    Returns:
        str: The generated refresh token.
    """
    if expires_delta:
        refresh_token = await create_token(data, expires_delta, "refresh")
    else:
        refresh_token = await create_token(
            data, timedelta(seconds=settings.JWT_EXPIRATION_SECONDS), "refresh"
        )
    return refresh_token


async def create_reset_token(email: str):
    payload = {
        "sub": email,
        "exp": datetime.now(UTC) + timedelta(hours=1),  # Expires in 1 hour
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


async def reset_user_password(token: str, new_password: str, db: AsyncSession):
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload.get("sub")

    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")

    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = Hash().get_pass_hash(new_password)  # Hash new password
    await user_service.update_user(user)

    return {"message": "Password updated successfully"}


async def get_curent_user(
    token: str = Depends(oath2_scheme), db: AsyncSession = Depends(get_db)
):
    """
    Retrieves the current user from the JWT token.

    This function does the following:
        - Decodes the JWT token to extract the username.
        - Checks the Redis cache to see if the user data is already stored.
        - If the user data is not in cache, it fetches the user from the database.
        - Caches the user data in Redis for future requests.

    Args:
        token (str): The JWT token for authentication.
        db (Session): The database session to query the user.

    Returns:
        User: The authenticated user object.

    Raises:
        HTTPException: If the token is invalid or the user does not exist.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": " Bearer"},
    )
    try:
        # decode jwt
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username = payload["sub"]
        token_type: str = payload.get("token_type")
        if username is None or token_type != "access":
            raise credentials_exception

    except ExpiredSignatureError as e:
        print(e)
        # Handle expired token case explicitly
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except JWTError as e:
        raise credentials_exception

    user_cached = r.get(f"user:{username}")
    if user_cached:
        #     # If user is cached, load from cache and convert to User object
        #     # user_data = json.loads(user_cached)
        #     # user_data["role"] = UserRole(user_data["role"])
        #     # return User(**user_data) #User object
        return json.loads(user_cached)

    user_service = UserService(db)

    user = await user_service.get_user_by_username(username)

    if user is None:
        raise credentials_exception

    user_schema = User.model_validate(user)
    r.set(f"user:{user.username}", user_schema.model_dump_json())

    r.expire(f"user:{user.username}", 3600)

    return user


async def verify_refresh_token(refresh_token: str, db: Session):
    """
    Verifies the refresh token and checks if it is valid.

    Args:
        refresh_token (str): The refresh token to validate.
        db (Session): The database session to query the user.

    Returns:
        User | None: The user object if the token is valid, otherwise None.
    """
    try:
        payload = jwt.decode(
            refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload["sub"]
        token_type: str = payload.get("token_type")
        if username is None or token_type != "refresh":
            return None

        user_service = UserService(db)
        user = await user_service.get_user_by_username(username)
        stored_refresh_token = user.refresh_token
        # stored_refresh_token = await user_service.get_users_token(username)

        if stored_refresh_token != refresh_token:
            return None

        return user
    except JWTError:
        return None


async def create_email_token(data: dict):
    """
    Creates a token for email verification.

    Args:
        data (dict): The data to encode into the email verification token.

    Returns:
        str: The encoded email verification token.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(), "exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


async def get_email_from_token(token: str):
    """
    Decodes the email verification token to retrieve the user's email.

    Args:
        token (str): The email verification token.

    Returns:
        str: The decoded email from the token.

    Raises:
        HTTPException: If the token is invalid or the email cannot be decoded.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Wrong token for checking email",
        )


async def get_current_admin_user(current_user: User = Depends(get_curent_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Restricted! No access rights")
    return current_user
