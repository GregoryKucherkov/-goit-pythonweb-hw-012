from pydantic import ConfigDict, EmailStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Settings class for application configuration.

    Inherits from `pydantic.BaseSettings` to automatically load environment variables
    or configuration files. This class is used to configure settings for database
    connections, JWT authentication, email setup, and Cloudinary integration.

    Attributes:
        DB_URL (str): The database connection URL.
        JWT_SECRET (str): Secret key used for JWT encoding and decoding.
        JWT_ALGORITHM (str): Algorithm used for JWT encoding and decoding.
        JWT_EXPIRATION_SECONDS (int): Expiration time for JWT tokens in seconds.
        MAIL_USERNAME (EmailStr): The username for email authentication.
        MAIL_PASSWORD (str): The password for email authentication.
        MAIL_FROM (EmailStr): The "from" email address used in outgoing emails.
        MAIL_PORT (int): The port number for the email server.
        MAIL_SERVER (str): The email server address.
        MAIL_FROM_NAME (str): The "from" name in email headers. Defaults to "Rest API Service".
        MAIL_STARTTLS (bool): Whether to use STARTTLS for email connections. Defaults to False.
        MAIL_SSL_TLS (bool): Whether to use SSL/TLS for email connections. Defaults to True.
        USE_CREDENTIALS (bool): Whether to use credentials for email sending. Defaults to True.
        VALIDATE_CERTS (bool): Whether to validate email server certificates. Defaults to False.
        CLD_NAME (str): Cloudinary cloud name for file uploads.
        CLD_API_KEY (int): Cloudinary API key for authentication.
        CLD_API_SECRET (str): Cloudinary API secret for authentication.

    Config:
        This class is configured to read environment variables from the `.env` file,
        and it includes settings for handling extra variables, file encoding, and
        case sensitivity.
    """

    DB_URL: str = "sqlite+aiosqlite:///./test.db"

    JWT_SECRET: str = "secret"

    JWT_ALGORITHM: str = "HS256"

    JWT_EXPIRATION_SECONDS: int = 3600

    MAIL_USERNAME: EmailStr = "example@meta.ua"
    MAIL_PASSWORD: str = "secretPassword"
    MAIL_FROM: EmailStr = "example@meta.ua"
    MAIL_PORT: int = 465
    MAIL_SERVER: str = "smtp.meta.ua"
    MAIL_FROM_NAME: str = "Rest API Service"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = False

    CLD_NAME: str = "meta"
    CLD_API_KEY: int = 12345678
    CLD_API_SECRET: str = "secret"

    model_config = ConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


# Instantiate the settings class to load environment variables
settings = Settings()


# Check the values from the settings object
# print(settings.DB_URL)
# print(settings.JWT_SECRET)
