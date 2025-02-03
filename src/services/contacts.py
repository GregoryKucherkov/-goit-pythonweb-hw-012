from sqlalchemy.ext.asyncio import AsyncSession

from src.repo.contacts import ContactRepo
from src.schemas import ContactBase, ContactUpdate
from datetime import date
from src.database.models import User


class ContactService:
    def __init__(self, db: AsyncSession):
        self.contact_repo = ContactRepo(db)

    async def create_contact(self, body: ContactBase, user: User):
        return await self.contact_repo.create_contact(body, user)

    async def get_contacts(self, skip: int, limit: int, user: User):
        return await self.contact_repo.get_contacts(skip, limit, user)

    async def get_contact(self, contact_id: int, user: User):
        return await self.contact_repo.get_contact_id(contact_id, user)

    async def update_contact(self, contact_id: int, body: ContactUpdate, user: User):
        return await self.contact_repo.update_contact(contact_id, body, user)

    async def remove_contact(self, contact_id: int, user: User):
        return await self.contact_repo.remove_contact(contact_id, user)

    async def search_contacts(self, search: str, skip: int, limit: int, user: User):
        return await self.contact_repo.search_contact_atr(search, skip, limit, user)

    # async def search_contact(self, name: str, lastname: str, email: str):
    #     return await self.contact_repo.search_contact_atr(name, lastname, email)

    async def get_week_birthdays(self, start_date: date, end_date: date, user: User):
        return await self.contact_repo.get_week_birthdays(start_date, end_date, user)
