from unittest.mock import patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from src.database.models import Contact, User

app = FastAPI()

from conftest import test_user
from fastapi.testclient import TestClient
from src.database.models import UserRole


@pytest.fixture
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def mock_user():
    return User(
        id=4,
        username=test_user["username"],
        email=test_user["email"],
        hashed_password="hash_password",
        confirmed=True,
        avatar="<https://twitter.com/gravatar>",
        role=UserRole.USER,
    )


@pytest.fixture
def mock_admin_user():
    return User(
        id=4,
        username=test_user["username"],
        email=test_user["email"],
        hashed_password="hash_password",
        confirmed=True,
        avatar="<https://twitter.com/gravatar>",
        role=UserRole.ADMIN,
    )


def test_get_me(client, get_token):
    token = get_token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("api/me", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]
    assert "avatar" in data


@patch("src.services.upload_file.UploadFileService.upload_file")
def test_update_avatar_user(mock_upload_file, client, get_token):

    fake_url = "<http://example.com/avatar.jpg>"
    mock_upload_file.return_value = fake_url

    headers = {"Authorization": f"Bearer {get_token}"}

    file_data = {"file": ("avatar.jpg", b"fake image content", "image/jpeg")}

    response = client.patch("/api/me/avatar", headers=headers, files=file_data)

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]
    assert data["avatar"] == fake_url

    mock_upload_file.assert_called_once()


def test_update_contact(client, get_token):
    updated_test_contact = test_user.copy()
    updated_test_contact["name"] = "New_name"
    updated_test_contact["avatar"] = updated_test_contact.get("avatar", "")

    response = client.patch(
        "/api/me/1",
        json=updated_test_contact,
        headers={"Authorization": f"Bearer {get_token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == updated_test_contact["username"]
    assert "id" in data
    assert data["id"] == 1
