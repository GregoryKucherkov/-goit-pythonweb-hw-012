from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.services.auth import create_email_token
from src.config.config import settings


# Configuration for email connection
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(email: EmailStr, username: str, host: str):
    """
    Sends an email with a verification token to the user.

    This function generates a verification token using `create_email_token` and sends
    the email to the provided `email` address. The email contains a link to verify
    the user's email and uses the `verify_email.html` template for the message body.

    Args:
        email (EmailStr): The email address to send the verification link to.
        username (str): The username of the user requesting email verification.
        host (str): The host URL for the email verification page.

    Returns:
        None

    Raises:
        ConnectionError: If there is an issue connecting to the email server or sending the email.

    Example:
        ```python
        await send_email(email="user@example.com", username="user1", host="https://example.com")
        ```
    """
    try:
        token_verification = await create_email_token({"sub": email})

        message = MessageSchema(
            subject="Confirm youe email",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )
        fm = FastMail(conf)

        await fm.send_message(message, template_name="verify_email.html")
        return "Email sent successfully"

    except ConnectionErrors as e:
        print(e)


async def send_reset_email(email: EmailStr, username: str, reset_token: str, host: str):
    try:
        message = MessageSchema(
            subject="Password Reset Request",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": reset_token,
            },
            subtype=MessageType.html,
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset_email.html")

    except ConnectionError as e:
        print(e)
