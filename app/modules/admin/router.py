"""Admin router for user-management endpoints used by the admin panel."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AuditAction, UserRole, UserStatus
from app.modules.admin.service import (
    AdminRoleChangeError,
    AdminUserDeleteConflictError,
    AdminUserNotFoundError,
    delete_admin_user,
    list_admin_users,
    update_admin_user_role,
)
from app.modules.audit.service import AuditLogger
from app.modules.auth.middleware import ROLE_ADMIN, require_role
from app.modules.auth.tokens import TokenData
from app.redis_client import delete_refresh_token
from app.schemas import AdminUserListResponse, AdminUserRoleUpdateRequest, UserResponse


def _get_client_ip(request: Request) -> str:
    return request.client.host if request.client else ""


def _get_user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "")


def get_admin_router(prefix: str = "/api/v1/admin", tags: list[str] | None = None) -> APIRouter:
    """Create and configure the admin router."""
    router = APIRouter(prefix=prefix, tags=tags or ["admin"])

    @router.get(
        "/users",
        response_model=AdminUserListResponse,
        summary="List users for the admin panel",
    )
    async def get_users(
        request: Request,
        current_user: Annotated[TokenData, Depends(require_role(ROLE_ADMIN))],
        db: Annotated[AsyncSession, Depends(get_db)],
        search: Annotated[str | None, Query(max_length=100)] = None,
        role: Annotated[UserRole | None, Query()] = None,
        user_status: Annotated[UserStatus | None, Query(alias="status")] = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> AdminUserListResponse:
        users, total = await list_admin_users(
            db,
            search=search,
            role=role,
            status=user_status,
            limit=limit,
            offset=offset,
        )

        return AdminUserListResponse(
            users=[UserResponse.model_validate(user) for user in users],
            total=total,
            limit=limit,
            offset=offset,
        )

    @router.patch(
        "/users/{user_id}/role",
        response_model=UserResponse,
        summary="Change a user's role",
    )
    async def patch_user_role(
        user_id: UUID,
        payload: AdminUserRoleUpdateRequest,
        request: Request,
        current_user: Annotated[TokenData, Depends(require_role(ROLE_ADMIN))],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> UserResponse:
        try:
            user, previous_role, changed = await update_admin_user_role(
                db,
                target_user_id=user_id,
                new_role=payload.role,
                actor_user_id=current_user.user_id,
            )
        except AdminUserNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except AdminRoleChangeError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        if changed:
            await AuditLogger.log_action(
                session=db,
                action=AuditAction.ROLE_CHANGED,
                user_id=current_user.user_id,
                resource_type="user",
                resource_id=str(user.id),
                metadata={
                    "old_role": previous_role.value,
                    "new_role": user.role.value,
                    "target_user_id": str(user.id),
                    "target_email": user.email,
                },
                ip_address=_get_client_ip(request),
                user_agent=_get_user_agent(request),
            )
            await db.commit()
            await db.refresh(user)

        return UserResponse.model_validate(user)

    @router.delete(
        "/users/{user_id}",
        response_model=UserResponse,
        summary="Delete a user account",
    )
    async def delete_user(
        user_id: UUID,
        request: Request,
        current_user: Annotated[TokenData, Depends(require_role(ROLE_ADMIN))],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> UserResponse:
        try:
            user, previous_email, previous_username = await delete_admin_user(
                db,
                target_user_id=user_id,
                actor_user_id=current_user.user_id,
            )
        except AdminUserNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except AdminUserDeleteConflictError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

        await AuditLogger.log_action(
            session=db,
            action=AuditAction.USER_DELETED_BY_ADMIN,
            user_id=current_user.user_id,
            resource_type="user",
            resource_id=str(user.id),
            metadata={
                "target_user_id": str(user.id),
                "previous_email": previous_email,
                "previous_username": previous_username,
                "new_status": user.status.value,
            },
            ip_address=_get_client_ip(request),
            user_agent=_get_user_agent(request),
        )
        await delete_refresh_token(str(user.id))
        await db.commit()
        await db.refresh(user)
        return UserResponse.model_validate(user)

    return router
