from typing import List
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas import ContactBase, ContactUpdate
from datetime import date


class ContactRepo:
    def __init__(self, session: AsyncSession):
        """
        Initialize a ContactRepository.

        Args:
            session: An AsyncSession object connected to the database.
        """
        self.db = session

    async def get_contacts(self, skip: int, limit: int, user: User) -> List[Contact]:
        """
        Get a list of Contacts owned by `user` with pagination.

        Args:
            skip: The number of Contacts to skip.
            limit: The maximum number of Contacts to return.
            user: The owner of the Contacts to retrieve.

        Returns:
            A list of Contacts.
        """
        req = select(Contact).filter_by(user=user).offset(skip).limit(limit)
        contacts = await self.db.execute(req)
        return contacts.scalars().all()

    async def get_contact_id(self, contact_id, user: User) -> Contact | None:
        """
        Get a Contact by its id.

        Args:
            contact_id: The id of the Contact to retrieve.
            user: The owner of the Contact to retrieve.

        Returns:
            The Contact with the specified id, or None if no such Contact exists.
        """
        req = select(Contact).filter_by(id=contact_id, user=user)
        # req = select(Contact).filter(Contact.id == contact_id, user=user)
        contact = await self.db.execute(req)
        return contact.scalar_one_or_none()

    async def create_contact(self, body: ContactBase, user: User) -> Contact:
        """
        Create a new Contact with the given attributes.

        Args:
            body: A ContactBase with the attributes to assign to the Contact.
            user: The User who owns the Contact.

        Returns:
            A Contact with the assigned attributes.
        """

        contact = Contact(**body.model_dump(exclude_unset=True), user=user)

        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)

        return await self.get_contact_id(contact.id, user)

    async def update_contact(
        self, contact_id: int, body: ContactUpdate, user: User
    ) -> Contact | None:
        """
        Update a Contact with the given attributes.

        Args:
            contact_id: The id of the Contact to update.
            body: A ContactUpdate with the attributes to assign to the Contact.
            user: The User who owns the Contact.

        Returns:
            The updated Contact, or None if no Contact with the given id exists.
        """
        contact = await self.get_contact_id(contact_id, user)
        if contact:
            for key, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def remove_contact(self, contact_id: int, user: User) -> Contact | None:
        """
        Delete a Contact by its id.

        Args:
            contact_id: The id of the Contact to delete.
            user: The owner of the Contact to delete.

        Returns:
            The deleted Contact, or None if no Contact with the given id exists.
        """
        contact = await self.get_contact_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def search_contact_atr(
        self, text: str, skip: int, limit: int, user: User
    ) -> List[Contact]:
        """
        Search for contacts by matching attributes with pagination.

        Args:
            text:  A search query to match against contact attributes (e.g., name, email, phone).
            skip: The number of Contacts to skip (for pagination).
            limit: The maximum number of Contacts to return.
            user: The owner of the Contacts to retrieve.


        Returns:
            A list of contacts that match the search criteria.
        """
        req = (
            select(Contact)
            .filter(
                Contact.user == user,
                or_(
                    Contact.name.ilike(f"%{text}%"),
                    Contact.lastname.ilike(f"%{text}%"),
                    Contact.email.ilike(f"%{text}%"),
                    Contact.notes.ilike(f"%{text}%"),
                ),
            )
            .offset(skip)
            .limit(limit)
        )
        # option2
        # req = (
        #     select(Contact)
        #     .filter_by(user=user)
        #     .where(
        #         or_(
        #             Contact.name.ilike(f"%{text}%"),
        #             Contact.lastname.ilike(f"%{text}%"),
        #             Contact.email.ilike(f"%{text}%"),
        #             Contact.notes.ilike(f"%{text}%"),
        #         )
        #     )
        #     .offset(skip)
        #     .limit(limit)
        # )
        result = await self.db.execute(req)
        return result.scalars().all()

    # option 2
    # async def search_contact_atr(self, name: str, lastname: str, email: str) -> Contact:
    #     req = select(Contact).where(
    #         or_(
    #             Contact.name == name,
    #             Contact.lastname == lastname,
    #             Contact.email == email,
    #         )
    #     )
    #     contact = await self.db.execute(req)
    #     return contact.scalar_one_or_none()

    async def get_week_birthdays(
        self, start_date: date, end_date: date, user: User
    ) -> list[Contact] | None:
        """
        Retrieve contacts whose birthdays fall within a given week range.

        Parameters:
            start_date : The start date of the range.
            end_date : The end date of the range.
            user : The owner of the contacts.


        Returns:
            A list of contacts with birthdays in the specified week range, or None if no contacts are found.
        """

        # query = select(Contact).where(
        #     func.floor((start_date - Contact.birthdate).label("days_diff") / 365.25)
        #     != func.floor((end_date - Contact.birthdate).label("days_diff") / 365.25)
        # )

        # for User
        query = (
            select(Contact)
            .filter(Contact.user == user)  # Filter contacts belonging to the given user
            .filter(
                func.floor((start_date - Contact.birthdate).label("days_diff") / 365.25)
                != func.floor(
                    (end_date - Contact.birthdate).label("days_diff") / 365.25
                )
            )
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    # option 2, less eficien, but works
    # async def get_week_birthdays(
    #     self, start_date: date, end_date: date
    # ) -> list[Contact] | None:

    #     query_1 = select(Contact).filter(
    #         func.to_char(Contact.birthdate, "MM-DD").between(
    #             start_date.strftime("%m-%d"), end_date.strftime("%m-%d")
    #         )
    #     )

    #     result = await self.db.execute(query_1)
    #     return result.scalars().all()
