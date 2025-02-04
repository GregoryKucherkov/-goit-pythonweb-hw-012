from unittest.mock import Mock, patch
from src.services.email import send_email
import asyncio
from fastapi import Request

import pytest
from sqlalchemy import select

from src.database.models import User
from tests.conftest import TestingSessionLocal


user_data = {
    "username": "agent008",
    "email": "agent008@gmail.com",
    "password": "12345678",
}


def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    response = client.post("api/auth/register", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "hashed_password" not in data
    mock_send_email.assert_called_once()
    assert "id" in data
    assert "avatar" in data
    assert isinstance(data["id"], int)
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "User with that email is already exists"


@pytest.mark.asyncio
async def test_repeat_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)
    response = client.post("api/auth/register", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "User with that email is already exists"
    assert "detail" in data

    # async with TestingSessionLocal() as session:
    #     current_user = await session.execute(
    #         select(User).where(User.email == user_data.get("email"))
    #     )
    #     current_user = current_user.scalar_one_or_none()
    # assert current_user is not None


def test_not_confirmed_login(client):
    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("username"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email is not confirmed"


@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(
            select(User).where(User.email == user_data.get("email"))
        )
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    response = client.post(
        "api/auth/login",
        data={
            "username": user_data.get("username"),
            "password": user_data.get("password"),
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data

    assert data["token_type"] == "bearer", "Expected token type to be 'bearer'"
    assert isinstance(data["access_token"], str), "Access token should be a string"
    assert len(data["access_token"]) > 10, "Access token seems too short"


def test_wrong_password_login(client):
    response = client.post(
        "api/auth/login",
        data={"username": user_data.get("username"), "password": "password"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Wrong login or password"


def test_wrong_username_login(client):
    response = client.post(
        "api/auth/login",
        data={"username": "username", "password": user_data.get("password")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Wrong login or password"


def test_validation_error_login(client):
    response = client.post(
        "api/auth/login", data={"password": user_data.get("password")}
    )
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data


def test_refresh_token(client, get_refresh_token):
    response = client.post(
        "api/auth/refresh-token",
        json={"refresh_token": get_refresh_token},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


def test_invalid_token_type(client, get_token):
    response = client.post(
        "/api/auth/refresh-token",
        json={"refresh_token": get_token},
    )
    assert response.status_code == 401, response.text
    assert "Invalid or expired refresh token" in response.json()["detail"]
