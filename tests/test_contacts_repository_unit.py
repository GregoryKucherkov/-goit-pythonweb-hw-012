from typing import List
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas import ContactBase, ContactUpdate
from datetime import date, timedelta
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.repo.contacts import ContactRepo
from src.database.models import UserRole
from datetime import datetime, date


@pytest.fixture
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def contacts_repo(mock_session):
    return ContactRepo(mock_session)


@pytest.fixture
def user():
    user = User(
        id=1,
        username="testuser",
        email="testuser@example.com",
        hashed_password="pass_test",
        created_at=datetime.now(),
        avatar="some_ava",
        refresh_token=None,
        confirmed=False,
        role=UserRole.USER,  # Enum field
    )
    user.contacts = []
    return user


@pytest.mark.asyncio
async def test_get_contacts(contacts_repo, mock_session, user):
    # Setup mock
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Contact(
            id=1,
            name="test_name",
            lastname="test_lastname",
            email="test_mail",
            phone="test_phone",
            birthdate="2000-01-01",
            notes="Some notes",
            user_id=user.id,
        )
    ]
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    contacts = await contacts_repo.get_contacts(skip=0, limit=10, user=user)

    # Assertions
    assert len(contacts) == 1
    assert contacts[0].id == 1
    assert contacts[0].name == "test_name"

    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_contacts_id(contacts_repo, mock_session, user):
    # Setup mock
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Contact(
        id=1,
        name="test_name",
        lastname="test_lastname",
        email="test_mail",
        phone="test_phone",
        birthdate="2000-01-01",
        notes="Some notes",
        user_id=user.id,
    )
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    contact = await contacts_repo.get_contact_id(contact_id=1, user=user)

    # Assertions
    assert contact is not None
    assert contact.id == 1
    assert contact.email == "test_mail"


@pytest.mark.asyncio
async def test_create_contact(contacts_repo, mock_session, user):
    # Setup
    contact_data = ContactBase(
        name="test_contact",
        lastname="test_lastname",
        email="test_mail@gmail.com",
        phone="123-34-45",
        birthdate=date(2000, 1, 1),
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Contact(
        id=1,
        name="test_contact",
        lastname="test_lastname",
        email="test_mail@gmail.com",
        phone="123-34-45",
        birthdate=date(2000, 1, 1),
        notes="some_notes",
        user_id=1,
    )
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await contacts_repo.create_contact(body=contact_data, user=user)

    # Assertions
    assert isinstance(result, Contact)
    assert result.name == "test_contact"
    assert result.lastname == "test_lastname"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_contact(contacts_repo, mock_session, user):
    # Setup
    contact_data = ContactUpdate(name="test_updated_name")
    existing_contact = Contact(
        id=1,
        name="old_contact",
        lastname="test_lastname",
        email="test_mail@gmail.com",
        phone="123-34-45",
        birthdate=date(2000, 1, 1),
        user=user,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await contacts_repo.update_contact(
        contact_id=1, body=contact_data, user=user
    )

    # Assertions
    assert result is not None
    assert result.name == "test_updated_name"
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(existing_contact)


@pytest.mark.asyncio
async def test_remove_contact(contacts_repo, mock_session, user):
    # Setup
    existing_contact = Contact(
        id=1,
        name="delete_contact",
        lastname="test_lastname",
        email="test_mail",
        phone="test_phone",
        birthdate=date(2000, 1, 1),
        notes="Some notes",
        user_id=user.id,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await contacts_repo.remove_contact(contact_id=1, user=user)

    print(f"Deleting contact: {existing_contact}")
    # Assertions
    assert result is not None
    assert result.name == "delete_contact"
    mock_session.delete.assert_awaited_once_with(existing_contact)
    mock_session.commit.assert_awaited_once()
    # mock_session.delete.assert_called_with(existing_contact)


@pytest.mark.asyncio
async def test_search_contact_atr(contacts_repo, mock_session, user):
    # Setup
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Contact(
            id=1,
            name="contact_2_search",
            lastname="test",
            email="test@example.com",
            phone="test_phone",
            birthdate=date(2000, 1, 1),
            notes="important",
            user_id=1,
        ),
        Contact(
            id=2,
            name="another_contact",
            lastname="test2",
            email="contact@example.com",
            phone="test_phone_2",
            birthdate=date(2000, 1, 2),
            notes="random",
            user_id=2,
        ),
    ]
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await contacts_repo.search_contact_atr(
        text="contact", skip=0, limit=10, user=user
    )

    # Assertions
    assert len(result) == 2
    assert result[0].id == 1
    assert result[0].name == "contact_2_search"
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_week_birthdays(contacts_repo, mock_session, user):
    # Setup
    start_date = date.today()
    end_date = start_date + timedelta(days=7)
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [
        Contact(
            id=1,
            name="birthday_contact",
            lastname="test",
            email="test@example.com",
            phone="test_phone",
            birthdate=start_date + timedelta(days=1),
            notes="important",
            user_id=1,
        ),
        Contact(
            id=2,
            name="another_contact",
            lastname="test2",
            email="contact@example.com",
            phone="test_phone_2",
            birthdate=end_date,
            notes="random",
            user_id=2,
        ),
    ]
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call method
    result = await contacts_repo.get_week_birthdays(start_date, end_date, user)

    # Assertations
    assert len(result) == 2
    assert result[0].birthdate >= start_date and result[0].birthdate <= end_date
    assert result[1].birthdate >= start_date and result[1].birthdate <= end_date

    mock_session.execute.assert_called_once()
