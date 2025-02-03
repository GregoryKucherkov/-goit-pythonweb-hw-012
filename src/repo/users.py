from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas import UserCreate, UserUpdate
from typing import Optional


class UserRepo:
    def __init__(self, session: AsyncSession):
        """
        Initialize a UserRepository.

        Args:
            session: An AsyncSession object connected to the database.
        """
        self.db = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieve a user by their unique ID.

        Parameters:
            user_id: The ID of the user.

        Returns:
            The User object if found, otherwise None.
        """
        req = select(User).filter(User.id == user_id)
        user = await self.db.execute(req)
        return user.scalar_one_or_none()

    async def get_user_by_name(self, username: str) -> User | None:
        """
        Retrieve a user by their username.

        Parameters:
            username: The username of the user.

        Returns:
            The User object if found, otherwise None.
        """
        req = select(User).filter_by(username=username)
        user = await self.db.execute(req)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by their email address.

        Parameters:
            email: The email of the user.

        Returns:
            The User object if found, otherwise None.
        """
        req = select(User).filter_by(email=email)
        user = await self.db.execute(req)
        return user.scalar_one_or_none()

    async def create_user(self, body: UserCreate, avatar: str = None) -> User:
        """
        Create a new user in the database.

        Parameters:
            body: The user creation data.
            avatar: Optional avatar URL for the user.

        Returns:
            The newly created User object.
        """
        user = User(
            **body.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=body.password,
            avatar=avatar,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user(self, user: User) -> User:
        """
        Update an existing user in the database.

        Parameters:
            user: The user object with updated details.

        Returns:
            The updated User object.
        """

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_user_token_by_name(self, username: str) -> Optional[str]:
        """
        Retrieve a user's refresh token by their username.

        Parameters:
            username: The username of the user.

        Returns:
            The refresh token if found, otherwise None.
        """
        # req = select(User.refresh_token).filter_by(username=username)
        req = select(User.refresh_token).where(User.username == username)
        result = await self.db.execute(req)
        return await result.scalar_one_or_none()

    async def confirmed_email(self, email: str) -> None:
        """
        Mark a user's email as confirmed.

        Parameters:
            email: The email address of the user.
        """
        user = await self.get_user_by_email(email)
        user.confirmed = True
        await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        """
        Update a user's avatar URL.

        Parameters:
            email: The email of the user.
            url: The new avatar URL.

        Returns:
            The updated User object.
        """
        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user
