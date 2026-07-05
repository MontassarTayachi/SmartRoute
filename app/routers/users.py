from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.dependencies import get_current_user, require_admin
from app.schemas.user import DriverUserCreate, UserCreate, UserResponse, UserUpdate
from app.services.user_service import create_driver_user_account, create_user, delete_user, get_user_by_id, list_users, update_user

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/", response_model=dict)
async def get_users(page: int = 1, size: int = 10, role: str | None = None, request: Request = None, current_user: dict = Depends(get_current_user)):
    db = request.app.state.mongodb
    return await list_users(db, page=page, size=size, role=role)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_route(payload: UserCreate, request: Request = None, current_user: dict = Depends(require_admin)):
    db = request.app.state.mongodb
    return await create_user(db, payload)


@router.post("/driver-account", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_driver_user_account_route(
    payload: DriverUserCreate,
    request: Request = None,
    current_user: dict = Depends(require_admin),
):
    db = request.app.state.mongodb
    return await create_driver_user_account(db, payload)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, request: Request = None, current_user: dict = Depends(get_current_user)):
    db = request.app.state.mongodb
    user = await get_user_by_id(db, user_id)
    if not user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Utilisateur introuvable."})
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_route(user_id: str, payload: UserUpdate, request: Request = None, current_user: dict = Depends(require_admin)):
    db = request.app.state.mongodb
    return await update_user(db, user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_route(user_id: str, request: Request = None, current_user: dict = Depends(require_admin)):
    db = request.app.state.mongodb
    await delete_user(db, user_id)

