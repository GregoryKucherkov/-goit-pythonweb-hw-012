from fastapi import (
    APIRouter,
    Depends,
    File,
    Request,
    HTTPException,
    status,
    UploadFile,
    BackgroundTasks,
    Form,
)
from src.schemas import User, UserUpdate
from src.services.auth import (
    get_curent_user,
    get_current_admin_user,
    create_reset_token,
    reset_user_password,
)
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.database.models import UserRole
from src.services.upload_file import UploadFileService
from src.config.config import settings
from src.services.users import UserService
from src.services.email import send_reset_email


router = APIRouter(prefix="/me", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/", response_model=User, description="No more than 15 requests per minute")
@limiter.limit("15/minute")
async def me(request: Request, user: User = Depends(get_curent_user)):
    # return {"message": "Logged user:", "owner": user}

    """
    Get the details of the currently authenticated user.

    Args:
        request: The request object.
        user: The authenticated user, retrieved via dependency.

    Returns:
        The details of the authenticated user.
    """
    return user


@router.patch("/avatar", response_model=User)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the avatar for the authenticated user.

    Args:
        file: The new avatar file to upload.
        user: The authenticated user, retrieved via dependency.
        db: The database session dependency.

    Returns:
        The updated user with the new avatar.
    """
    avatar_url = UploadFileService(
        settings.CLD_NAME, settings.CLD_API_KEY, settings.CLD_API_SECRET
    ).upload_file(file, user.username)

    user_service = UserService(db)
    updated_user = await user_service.update_avatar_url(user.email, avatar_url)

    return updated_user


@router.patch("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    body: UserUpdate,
    user: User = Depends(get_curent_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user details for a specific user.

    Args:
        user_id: The ID of the user to update.
        body: The user data to update.
        user: The authenticated user, retrieved via dependency.
        db: The database session dependency.

    Returns:
        The updated user.
    """
    # print(f"user id: {user['id']}")

    user_service = UserService(db)
    user_to_update = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if body.username:
        user_to_update.username = body.username
    if body.email:
        user_to_update.email = body.email

    updated_user = await user_service.update_user(user_to_update)

    return updated_user


@router.patch("/assign-role/", response_model=User)
async def set_role(
    user_id: int,
    role: UserRole,
    user: User = Depends(get_curent_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Promote a user to admin role.

    Args:
        user_id: The ID of the user to promote to admin.
        user: The authenticated admin user.
        db: The database session.

    Returns:
        The updated user.
    """

    user_service = UserService(db)
    target_user = await user_service.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    target_user.role = role
    updated_user = await user_service.update_user(target_user)
    return updated_user


@router.post("/request-password-reset")
async def request_password_reset(
    email: str,
    background_tasks: BackgroundTasks,
    request: Request,
    user: User = Depends(get_curent_user),
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    reset_token = await create_reset_token(user.email)

    # send_reset_email(user.email, user.username, reset_token)  # Email reset link
    background_tasks.add_task(
        send_reset_email, user.email, user.username, reset_token, request.base_url
    )

    return {"message": "Password reset link sent", "token": reset_token}


@router.post("/reset-password")
async def reset_password(
    token: str, new_password: str, db: AsyncSession = Depends(get_db)
):
    await reset_user_password(token, new_password, db)
    return {"message": "Password updated successfully"}


@router.post("/reset-password-email/{token}")
async def reset_password_email(
    token: str, new_password: str = Form(...), db: AsyncSession = Depends(get_db)
):
    await reset_user_password(token, new_password, db)
    return {"message": "Password updated successfully"}
