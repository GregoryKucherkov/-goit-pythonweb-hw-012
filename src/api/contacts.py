from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from src.database.db import get_db
from src.schemas import ContactBase, ContactResponse, ContactUpdate

from src.services.contacts import ContactService
from src.database.models import User
from src.services.auth import get_curent_user


router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=List[ContactResponse], status_code=status.HTTP_200_OK)
async def read_contacts(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_curent_user),
):
    """
    Get a list of contacts for the authenticated user with pagination.

    Args:
        skip: The number of contacts to skip.
        limit: The maximum number of contacts to return.
        db: The database session dependency.
        user: The authenticated user, retrieved via dependency.

    Returns:
        A list of contacts.
    """
    contacts_service = ContactService(db)
    contacts = await contacts_service.get_contacts(skip, limit, user)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def read_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_curent_user),
):
    """
    Retrieve a contact by its ID for the authenticated user.

    Args:
        contact_id: The ID of the contact to retrieve.
        db: The database session dependency.
        user: The authenticated user, retrieved via dependency.

    Returns:
        The contact corresponding to the provided ID.
    """
    contacts_service = ContactService(db)
    contact = await contacts_service.get_contact(contact_id, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact is not found!"
        )
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: ContactBase,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_curent_user),
):
    """
    Create a new contact for the authenticated user.

    Args:
        body: The contact data to create.
        db: The database session dependency.
        user: The authenticated user, retrieved via dependency.

    Returns:
        The newly created contact.
    """
    contacts_service = ContactService(db)
    return await contacts_service.create_contact(body, user)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    body: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_curent_user),
):
    """
    Update an existing contact for the authenticated user.

    Args:
        contact_id: The ID of the contact to update.
        body: The updated contact data.
        db: The database session dependency.
        user: The authenticated user, retrieved via dependency.

    Returns:
        The updated contact.
    """
    contacts_service = ContactService(db)
    contact = await contacts_service.update_contact(contact_id, body, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact is not found!"
        )
    return contact


@router.delete("/{contact_id}", response_model=ContactResponse)
async def remove_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_curent_user),
):
    """
    Delete a contact for the authenticated user.

    Args:
        contact_id: The ID of the contact to delete.
        db: The database session dependency.
        user: The authenticated user, retrieved via dependency.

    Returns:
        The deleted contact.
    """
    contacts_service = ContactService(db)
    contact = await contacts_service.remove_contact(contact_id, user)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact is not found!"
        )
    return contact


# additional functionality
@router.get("/search/", response_model=List[ContactResponse])
async def search_contacts(
    text: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_curent_user),
):
    """
    Search for contacts based on a text query.

    Args:
        text: The search query to filter contacts.
        skip: The number of contacts to skip.
        limit: The maximum number of contacts to return.
        db: The database session dependency.
        user: The authenticated user, retrieved via dependency.

    Returns:
        A list of contacts matching the search criteria.
    """
    contacts_service = ContactService(db)
    contacts = await contacts_service.search_contacts(text, skip, limit, user)
    if not contacts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contacts with you criteria wasn`t found!",
        )
    return contacts


# option 2
# @router.get("/search/", response_model=List[ContactResponse])
# async def search_contact(
#     name: Optional[str] = None,
#     lastname: Optional[str] = None,
#     email: Optional[str] = None,
#     db: AsyncSession = Depends(get_db),
# ):
#     contacts_service = ContactService(db)
#     contact = await contacts_service.search_contact(
#         name=name, lastname=lastname, email=email
#     )
#     if contact is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Contact with you criteria wasn`t found!",
#         )
#     return contact


@router.get("/birthdays/", response_model=List[ContactResponse])
async def week_birthdays(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_curent_user),
):
    """
    Get contacts with birthdays in the next 7 days for the authenticated user.

    Args:
        db: The database session dependency.
        user: The authenticated user, retrieved via dependency.

    Returns:
        A list of contacts with birthdays in the next 7 days.
    """
    contacts_service = ContactService(db)
    today = datetime.today().date()
    end_date = today + timedelta(days=7)

    contacts = await contacts_service.get_week_birthdays(today, end_date, user)
    if not contacts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No contacts with upcoming birtdays in 7 days",
        )
    return contacts
