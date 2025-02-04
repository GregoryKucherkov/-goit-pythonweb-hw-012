from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    status,
    Security,
    BackgroundTasks,
    Request,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from src.database.db import get_db
from src.services.auth import (
    create_access_token,
    create_refresh_token,
    Hash,
    verify_refresh_token,
    get_email_from_token,
)
from src.services.users import UserService
from src.schemas import User, UserCreate, Token, TokenRefreshRequest, RequestEmail
from src.services.email import send_email


router = APIRouter(prefix="/auth", tags=["auth"])


# user register
@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Register a new user in the system.

    This endpoint receives user information and creates a new user record in the database.
    It also sends a confirmation email for the user to verify their account.

    Args:
        user_data (UserCreate): The user information including username, email, and password.
        background_tasks (BackgroundTasks): The background task to send a confirmation email.
        request (Request): The request object, used for building the confirmation URL.
        db (Session): The database session dependency.

    Returns:
        User: A user object with the id, username, email, and confirmation status.

    Raises:
        HTTPException: If the user with the given email or username already exists.
    """
    user_service = UserService(db)

    email_user = await user_service.get_user_by_email(user_data.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with that email is already exists",
        )
    username_user = await user_service.get_user_by_username(user_data.username)
    if username_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this name is already exists",
        )
    user_data.password = Hash().get_pass_hash(user_data.password)
    new_user = await user_service.create_user(user_data)

    # email verifivation
    background_tasks.add_task(
        send_email, new_user.email, new_user.username, request.base_url
    )
    return new_user


@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login a user by verifying their username and password, and returning an access and refresh token.

    This endpoint is used for user authentication. It checks the provided credentials,
    generates an access token and a refresh token if valid, and returns them.

    Args:
        form_data (OAuth2PasswordRequestForm): The form data containing the username and password.
        db (Session): The database session dependency.

    Returns:
        dict: A dictionary containing the access token, refresh token, and token type.

    Raises:
        HTTPException: If the login credentials are incorrect or the user is not found.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)
    if not user or not Hash().verify_pass(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong login or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # if you want user won't be able to login without email confirmation
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email is not confirmed",
        )

    # Generate JWT
    access_token = await create_access_token(data={"sub": user.username})
    refresh_token = await create_refresh_token(data={"sub": user.username})
    user.refresh_token = refresh_token
    await db.commit()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def re_send_confirmation_email(
    user: User, request: Request, background_tasks: BackgroundTasks
):
    """
    Resend the confirmation email to the user.

    This helper function adds a task to the background queue to send the confirmation email again.

    Args:
        user (User): The user object to resend the confirmation to.
        request (Request): The request object, used to build the confirmation URL.
        background_tasks (BackgroundTasks): Background task to send email.

    Returns:
        dict: A message confirming that the email has been sent.
    """
    background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    return {"message": "Confirmation has been sent", "user": user}


@router.post("/refresh-token", response_model=Token)
async def new_token(request: TokenRefreshRequest, db: Session = Depends(get_db)):
    """
    Refresh the user's access token using a valid refresh token.

    This endpoint generates a new access token when the user provides a valid refresh token.

    Args:
        request (TokenRefreshRequest): The request containing the refresh token.
        db (Session): The database session dependency.

    Returns:
        dict: A dictionary containing the new access token, the original refresh token, and the token type.

    Raises:
        HTTPException: If the refresh token is invalid or expired.
    """
    user = await verify_refresh_token(request.refresh_token, db)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    new_access_token = await create_access_token(data={"sub": user.username})
    return {
        "access_token": new_access_token,
        "refresh_token": request.refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Confirm the user's email using a confirmation token.

    This endpoint is called when the user clicks on the confirmation link in the email.
    It verifies the token and confirms the user's email.

    Args:
        token (str): The confirmation token received by the user.
        db (Session): The database session dependency.

    Returns:
        dict: A message indicating whether the email has been confirmed or already confirmed.

    Raises:
        HTTPException: If the token is invalid or verification fails.
    """
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": " Your email already confirmed"}
    await user_service.confirmed_email(email)
    return {"message": "Your email has been confirmed"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Request to resend the email confirmation for a user.

    If the user has not confirmed their email yet, this endpoint will send a new confirmation email.

    Args:
        body (RequestEmail): The request containing the user's email.
        background_tasks (BackgroundTasks): Background task to send email.
        request (Request): The request object, used to build the confirmation URL.
        db (Session): The database session dependency.

    Returns:
        dict: A message confirming the email has been sent or already confirmed.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)
    if user.confirmed:
        return {"message": "Your email has already been confirmed"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url
        )
    return {"message": "Check your email for the confirmation"}
