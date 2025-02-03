from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.repo.users import UserRepo
from src.schemas import UserCreate


class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepo(db)

    async def create_user(self, body: UserCreate):
        avatar: None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)

        return await self.repo.create_user(body, avatar)

    async def get_user_by_id(self, user_id: int):
        return await self.repo.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str):
        return await self.repo.get_user_by_name(username)

    async def get_user_by_email(self, email: str):
        return await self.repo.get_user_by_email(email)

    async def get_users_token(self, username: str):
        return await self.repo.get_user_token_by_name(username)

    async def confirmed_email(self, email):
        return await self.repo.confirmed_email(email)

    async def update_avatar_url(self, email: str, url: str):
        return await self.repo.update_avatar_url(email, url)

    async def update_user(self, user):
        return await self.repo.update_user(user)
