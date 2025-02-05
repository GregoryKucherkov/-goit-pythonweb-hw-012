import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from src.services.auth import (
    create_token,
    create_reset_token,
    reset_user_password,
    create_email_token,
)
from src.config.config import settings
from fastapi import HTTPException
from jose import jwt, JWTError
from src.database.models import UserRole, Contact, User
from src.services.auth import Hash
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def fixed_datetime():
    """Fixture to provide a fixed datetime for consistent token expiration testing."""
    return datetime(2025, 2, 4, 10, 0, 0, tzinfo=ZoneInfo("UTC"))


@pytest.fixture
def mock_settings():
    """Fixture to provide mock JWT settings."""

    class MockSettings:
        JWT_SECRET = "test_secret"
        JWT_ALGORITHM = "HS256"

    return MockSettings()


@pytest.fixture
def mock_user():
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


@pytest.fixture
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.mark.asyncio
async def test_create_token(mock_settings, fixed_datetime):
    data = {"user_id": 123}
    expires_delta = timedelta(hours=1)
    token_type = "access"

    with patch("src.services.auth.datetime", autospec=True) as mock_datetime, patch(
        "src.config.config.settings.JWT_SECRET", "test_secret"
    ), patch("src.config.config.settings.JWT_ALGORITHM", "HS256"), patch(
        "src.services.auth.jwt.encode", return_value="mocked_token"
    ) as mock_encode:

        mock_datetime.now.return_value = fixed_datetime

        token = await create_token(data, expires_delta, token_type)

        mock_encode.assert_called_once_with(
            {
                "user_id": 123,
                "exp": fixed_datetime + expires_delta,
                "iat": fixed_datetime,
                "token_type": "access",
            },
            "test_secret",  # Ensure the correct secret is passed
            algorithm="HS256",  # Ensure the correct algorithm is used
        )

        assert token == "mocked_token"
        assert token_type == "access"

        # Case 2: When expires_delta is not provided (should default to 1 hour)
        access_token = await create_token(data, None, "access")
        assert access_token == "mocked_token"


@pytest.mark.asyncio
async def test_create_reset_token(fixed_datetime):
    email = "test@example.com"

    with patch("src.services.auth.datetime", autospec=True) as mock_datetime, patch(
        "src.config.config.settings.JWT_SECRET", "test_secret"
    ), patch("src.config.config.settings.JWT_ALGORITHM", "HS256"), patch(
        "src.services.auth.jwt.encode", return_value="mocked_token"
    ) as mock_encode:

        # Mock datetime to return a fixed datetime
        mock_datetime.now.return_value = fixed_datetime

        # Call the function under test
        token = await create_reset_token(email)

        # Check that jwt.encode was called with the expected payload
        mock_encode.assert_called_once_with(
            {
                "sub": email,
                "exp": fixed_datetime + timedelta(hours=1),  # Expires in 1 hour
            },
            "test_secret",  # Ensure the correct secret is passed
            algorithm="HS256",  # Ensure the correct algorithm is used
        )

        # Assert that the returned token is the mocked token
        assert token == "mocked_token"


@pytest.mark.asyncio
async def test_create_email_token(mock_settings, fixed_datetime):
    data = {"sub": "test@gmail.com"}

    # Setup the expected expiration time
    expires_delta = timedelta(days=7)  # 7 days for expiration
    expected_expiration = fixed_datetime + expires_delta

    with patch("src.services.auth.datetime", autospec=True) as mock_datetime, patch(
        "src.config.config.settings.JWT_SECRET", "test_secret"
    ), patch("src.config.config.settings.JWT_ALGORITHM", "HS256"), patch(
        "src.services.auth.jwt.encode", return_value="mocked_token"
    ) as mock_encode:

        # Mock the current time to be `fixed_datetime`
        mock_datetime.now.return_value = fixed_datetime

        # Call the function under test
        token = await create_email_token(data)

        # Ensure jwt.encode was called with the correct payload
        mock_encode.assert_called_once_with(
            {
                "sub": "test@gmail.com",
                "iat": fixed_datetime,  # The 'issued at' time
                "exp": expected_expiration,  # Expiration time is 7 days from now
            },
            "test_secret",  # Ensure the correct secret is passed
            algorithm="HS256",  # Ensure the correct algorithm is used
        )

        # Ensure the returned token is the mocked one
        assert token == "mocked_token"


@pytest.mark.asyncio
async def test_reset_user_password(mock_user):
    token = "mocked_valid_token"
    new_password = "new_password"
    db = AsyncMock()  # Mock AsyncSession

    # Mock the jwt.decode method to return a payload
    with patch(
        "src.services.auth.jwt.decode", return_value={"sub": "test@example.com"}
    ), patch(
        "src.services.auth.UserService", autospec=True
    ) as mock_user_service, patch.object(
        Hash, "get_pass_hash", return_value="new_hashed_password"
    ):

        # Mock UserService's get_user_by_email method to return the mock user
        mock_user_service_instance = mock_user_service.return_value
        mock_user_service_instance.get_user_by_email = AsyncMock(return_value=mock_user)
        mock_user_service_instance.update_user = AsyncMock()

        # Call the function under test
        response = await reset_user_password(token, new_password, db)

        # Ensure jwt.decode was called with the correct arguments
        jwt.decode.assert_called_once_with(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )

        # Ensure the user service's get_user_by_email method was called with the correct email
        mock_user_service_instance.get_user_by_email.assert_called_once_with(
            "test@example.com"
        )

        # Ensure the password was hashed with the new password
        mock_user_service_instance.update_user.assert_called_once()
        mock_user_service_instance.update_user.assert_called_once_with(mock_user)

        # Ensure the response is as expected
        assert response == {"message": "Password updated successfully"}


@pytest.mark.asyncio
async def test_reset_user_password_invalid_token(mock_session):
    token = "mocked_invalid_token"
    new_password = "new_password"

    # Mock the jwt.decode method to raise JWTError
    with patch("src.services.auth.jwt.decode", side_effect=JWTError):
        with pytest.raises(HTTPException) as excinfo:
            await reset_user_password(token, new_password, mock_session)

        # Assert that the HTTPException is raised with the expected details
        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Invalid token"


@pytest.mark.asyncio
async def test_reset_user_password_user_not_found(mock_user, mock_session):
    token = "mocked_valid_token"
    new_password = "new_password"

    # Mock the jwt.decode method to return a valid payload
    with patch(
        "src.services.auth.jwt.decode", return_value={"sub": "test@example.com"}
    ), patch("src.services.auth.UserService", autospec=True) as mock_user_service:

        # Mock UserService's get_user_by_email method to return None (user not found)
        mock_user_service_instance = mock_user_service.return_value
        mock_user_service_instance.get_user_by_email = AsyncMock(return_value=None)

        # Call the function under test and assert that it raises the expected exception
        with pytest.raises(HTTPException) as excinfo:
            await reset_user_password(token, new_password, mock_session)

        assert excinfo.value.status_code == 404
        assert excinfo.value.detail == "User not found"
