from src.database.models import User
from src.schemas import UserCreate, UserUpdate
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.repo.users import UserRepo
from datetime import date, datetime
from src.database.models import UserRole


@pytest.fixture
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def user_repo(mock_session):
    return UserRepo(mock_session)


@pytest.mark.asyncio
async def test_get_user_by_id(user_repo, mock_session):
    # Setup
    mock_user = User(
        id=1,
        username="test_user",
        email="test_user@gmail.com",
        hashed_password="hashed_password",
        created_at=datetime(2024, 1, 5, 12, 0, 0),
        avatar="avatar_url",
        refresh_token="refresh_token",
        confirmed=True,
        role=UserRole.USER,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call
    result = await user_repo.get_user_by_id(mock_user.id)

    # Assertions
    assert result == mock_user
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_name(user_repo, mock_session):
    mock_user = User(
        id=1,
        username="test_user",
        email="test_user@gmail.com",
        hashed_password="hashed_password",
        created_at=datetime(2024, 1, 5, 12, 0, 0),
        avatar="avatar_url",
        refresh_token="refresh_token",
        confirmed=True,
        role=UserRole.USER,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call
    result = await user_repo.get_user_by_name(mock_user.username)

    # Assertions
    assert result == mock_user
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_email(user_repo, mock_session):
    mock_user = User(
        id=1,
        username="test_user",
        email="test_user@gmail.com",
        hashed_password="hashed_password",
        created_at=datetime(2024, 1, 5, 12, 0, 0),
        avatar="avatar_url",
        refresh_token="refresh_token",
        confirmed=True,
        role=UserRole.USER,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call
    result = await user_repo.get_user_by_email(mock_user.email)

    # Assertions
    assert result == mock_user
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_user(user_repo, mock_session):
    user_data = UserCreate(
        username="test_user", email="test@gamil.com", password="test_pass"
    )
    # Mock the expected behavior when creating a user
    mock_session.add = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    # Call method
    result = await user_repo.create_user(body=user_data)

    # Assertions
    assert isinstance(result, User)
    assert result.username == "test_user"
    mock_session.add.assert_called_once()
    mock_session.add.assert_called_once_with(result)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_update_user(user_repo, mock_session):
    # Setup
    user_data = UserUpdate(
        username="update_user", email="new_email@gmail.com", avatar="new_avatar_url"
    )
    existed_user = User(
        id=1,
        username="test_user",
        email="test_user@gmail.com",
        hashed_password="hashed_password",
        created_at=datetime(2024, 1, 5, 11, 0, 0),
        avatar="avatar_url",
        refresh_token="refresh_token",
        confirmed=True,
        role=UserRole.USER,
    )

    updated_user = existed_user
    updated_user.username = user_data.username
    updated_user.email = user_data.email
    # updated_user.avatar = user_data.avatar

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existed_user

    mock_session.execute = AsyncMock(return_value=mock_result)
    # Call method
    result = await user_repo.update_user(updated_user)

    # Assertions
    assert result is not None
    assert result.username == "update_user"
    assert result.email == "new_email@gmail.com"
    mock_session.commit.assert_awaited_once()

    mock_session.refresh.assert_awaited_once_with(updated_user)


@pytest.mark.asyncio
async def test_get_user_token_by_name(user_repo, mock_session):
    # Setup
    username = "test_user"
    expected_token = "mock_refresh_token"

    mock_session.execute = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = AsyncMock(return_value=expected_token)
    mock_session.execute.return_value = mock_result

    # Call
    result = await user_repo.get_user_token_by_name(username)

    # Assertions
    assert result == expected_token  # Check that the refresh token is returned
    mock_session.execute.assert_awaited_once()
    # mock_session.execute.assert_called_once_with(
    #     select(User.refresh_token).filter_by(username=username)
    # )  # Ensure the query was executed correctly


@pytest.mark.asyncio
async def test_confirmed_email(user_repo, mock_session):
    # Setup
    email = "test_email"
    existing_user = User(
        id=1,
        username="test_user",
        email="test_user@gmail.com",
        hashed_password="hashed_password",
        created_at=datetime(2024, 1, 5, 11, 0, 0),
        avatar="avatar_url",
        refresh_token="refresh_token",
        confirmed=True,
        role=UserRole.USER,
    )

    user_repo.get_user_by_email = AsyncMock(return_value=existing_user)

    mock_session.commit = AsyncMock()

    await user_repo.confirmed_email(email)

    # Assertions
    assert existing_user.confirmed is True
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_avatar_url(user_repo, mock_session):
    # Setup
    email = "test_user@gmail.com"
    new_url = "https://new_avatar_url.com"
    existing_user = User(
        id=1,
        username="test_user",
        email="test_user@gmail.com",
        hashed_password="hashed_password",
        created_at=datetime(2024, 1, 5, 11, 0, 0),
        avatar="avatar_url",
        refresh_token="refresh_token",
        confirmed=True,
        role=UserRole.USER,
    )

    user_repo.get_user_by_email = AsyncMock(return_value=existing_user)

    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    # Call
    updated_user = await user_repo.update_avatar_url(email, new_url)

    # Assertions
    assert updated_user.avatar == new_url  # Check that the avatar URL is updated
    mock_session.commit.assert_awaited_once()  # Ensure that commit was called
    mock_session.refresh.assert_awaited_once_with(updated_user)
