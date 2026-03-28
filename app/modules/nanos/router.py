"""
Router for Nano metadata endpoints.

This module provides API endpoints for managing Nano metadata, including
creating, reading, and updating metadata for learning content.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.auth.middleware import (
    ROLE_ADMIN,
    ROLE_CREATOR,
    ROLE_MODERATOR,
    get_current_user,
    get_current_user_id,
    get_optional_current_user,
    require_any_role,
    require_role,
)
from app.modules.auth.tokens import TokenData
from app.modules.nanos.schemas import (
    AdminTakedownRequest,
    AdminTakedownResponse,
    CreatorNanoListResponse,
    FeedbackModerationRequest,
    MetadataUpdateRequest,
    MetadataUpdateResponse,
    ModeratorQueueListResponse,
    NanoCommentListResponse,
    NanoCommentModerationResponse,
    NanoCommentMutationResponse,
    NanoCommentUpsertRequest,
    NanoDeleteResponse,
    NanoDetailResponse,
    NanoDownloadInfoResponse,
    NanoMetadataResponse,
    NanoRatingModerationResponse,
    NanoRatingMutationResponse,
    NanoRatingReadResponse,
    NanoRatingUpsertRequest,
    StatusUpdateRequest,
    StatusUpdateResponse,
)
from app.modules.nanos.service import (
    admin_takedown_nano,
    create_nano_comment,
    create_nano_rating,
    delete_nano,
    get_creator_nanos,
    get_nano_comments,
    get_nano_detail,
    get_nano_download_info,
    get_nano_metadata,
    get_nano_ratings,
    get_pending_review_nanos,
    moderate_nano_comment,
    moderate_nano_rating,
    update_nano_comment,
    update_nano_metadata,
    update_nano_rating,
    update_nano_status,
)
from app.monitoring import FeedbackMetricsRoute, record_feedback_moderation_decision


def get_nanos_router(prefix: str = "/api/v1/nanos", tags: list[str] | None = None) -> APIRouter:
    """
    Create and configure the nanos router.

    Args:
        prefix: URL prefix for all nanos endpoints
        tags: OpenAPI tags for documentation

    Returns:
        Configured APIRouter instance
    """
    if tags is None:
        tags = ["Nanos"]

    router = APIRouter(prefix=prefix, tags=tags, route_class=FeedbackMetricsRoute)

    @router.get(
        "/pending-moderation",
        response_model=ModeratorQueueListResponse,
        status_code=status.HTTP_200_OK,
        summary="Get moderation queue (moderator/admin only)",
        description="""
        Retrieve all Nanos currently in 'pending_review' status for content moderation.

        **Requirements:**
        - Authentication required (Bearer token)
        - User must have 'moderator' or 'admin' role

        **Query Parameters:**
        - `page`: Page number (1-indexed, default 1)
        - `limit`: Results per page (default 20, max 100)

        **Response:**
        - List of pending-review Nanos with creator info, ordered oldest-first (FIFO queue)
        - Pending ratings and comments that require moderation decisions

        **Error Cases:**
        - 401: Not authenticated
        - 403: User does not have moderator or admin role
        """,
        responses={
            200: {"description": "Moderation queue retrieved successfully"},
            401: {"description": "Not authenticated"},
            403: {"description": "User does not have moderator or admin role"},
        },
    )
    async def get_moderation_queue(
        page: Annotated[int, Query(ge=1, description="Page number")] = 1,
        limit: Annotated[int, Query(ge=1, le=100, description="Results per page")] = 20,
        current_user: Annotated[
            TokenData,
            Depends(
                require_any_role(
                    ROLE_MODERATOR,
                    ROLE_ADMIN,
                    detail="Only moderators and admins can access the moderation queue",
                )
            ),
        ] = None,
        db: Annotated[AsyncSession, Depends(get_db)] = None,
    ) -> ModeratorQueueListResponse:
        """Get moderation queue — moderator/admin only."""
        _ = current_user
        return await get_pending_review_nanos(db=db, page=page, limit=limit)

    @router.get(
        "/my-nanos",
        response_model=CreatorNanoListResponse,
        summary="Get creator's Nanos list",
        description="""
        Retrieve list of Nanos owned by the authenticated creator.

        **Requirements:**
        - Authentication required (Bearer token)
        - User must have 'creator' role or higher

        **Query Parameters:**
        - `page`: Page number (1-indexed, default 1)
        - `limit`: Results per page (default 20, max 100)
        - `status`: Optional status filter (draft, published, archived, etc.)

        **Response:**
        - List of creator's Nanos with pagination metadata
        - Results ordered by updated_at (newest first)

        **Error Cases:**
        - 401: Not authenticated
        - 403: User is not a creator
        - 404: Creator not found
        """,
        responses={
            200: {"description": "Creator's Nanos list retrieved successfully"},
            401: {"description": "Not authenticated"},
            403: {"description": "User is not a creator"},
            404: {"description": "Creator not found"},
        },
    )
    async def get_my_nanos(
        page: Annotated[int, Query(ge=1, description="Page number")] = 1,
        limit: Annotated[int, Query(ge=1, le=100, description="Results per page")] = 20,
        status: Annotated[str | None, Query(description="Optional status filter")] = None,
        current_user: Annotated[
            TokenData,
            Depends(
                require_any_role(
                    ROLE_CREATOR,
                    ROLE_MODERATOR,
                    ROLE_ADMIN,
                    detail="User must have creator or higher role to access their Nanos",
                )
            ),
        ] = None,
        db: Annotated[AsyncSession, Depends(get_db)] = None,
    ) -> CreatorNanoListResponse:
        """Get creator's Nano list with pagination."""
        return await get_creator_nanos(
            creator_id=current_user.user_id,
            db=db,
            page=page,
            limit=limit,
            status_filter=status,
        )

    @router.get(
        "/{nano_id}",
        response_model=NanoMetadataResponse,
        summary="Get Nano metadata",
        description="""
        Retrieve full metadata for a Nano by its ID.

        **Returns:**
        - Nano metadata including title, description, categories, status, etc.

        **Visibility Rules:**
        - Published Nanos are publicly visible
        - Non-published Nanos are visible only to creator, admin, or moderator

        **Error Cases:**
        - 401: Authentication required for non-published Nano
        - 403: Authenticated user lacks permission for non-published Nano
        - 404: Nano not found
        """,
        responses={
            200: {
                "description": "Nano metadata retrieved successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "nano_id": "123e4567-e89b-12d3-a456-426614174000",
                            "creator_id": "987e6543-e21b-12d3-a456-426614174000",
                            "title": "Introduction to Python",
                            "description": "Learn Python basics in 30 minutes",
                            "duration_minutes": 30,
                            "competency_level": "beginner",
                            "language": "de",
                            "format": "video",
                            "status": "draft",
                            "version": "1.0.0",
                            "categories": [
                                {
                                    "id": "456e7890-e12b-34d5-a678-901234567890",
                                    "name": "Programming",
                                    "rank": 0,
                                }
                            ],
                            "license": "CC-BY",
                            "uploaded_at": "2026-03-08T10:00:00Z",
                            "updated_at": "2026-03-08T10:00:00Z",
                        }
                    }
                },
            },
            401: {"description": "Authentication required for non-published Nano"},
            403: {"description": "Not authorized to access non-published Nano"},
            404: {"description": "Nano not found"},
        },
    )
    async def get_nano(
        nano_id: UUID,
        current_user: Annotated[TokenData | None, Depends(get_optional_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> NanoMetadataResponse:
        """Get Nano metadata by ID."""
        return await get_nano_metadata(nano_id=nano_id, db=db, current_user=current_user)

    @router.get(
        "/{nano_id}/detail",
        response_model=NanoDetailResponse,
        summary="Get Nano detail view payload",
        description="""
        Retrieve Nano detail payload for frontend detail pages with RBAC-aware visibility.

        **Visibility Rules:**
        - Published Nanos are publicly visible
        - Non-published Nanos are visible only to creator, admin, or moderator

        **Download Rules:**
        - Download requires authentication
        - Download path is only included if current caller is allowed to download

        **Response Contract:**
        - Unified envelope: `success/data/meta/timestamp`

        **Error Cases:**
        - 401: Authentication required for non-published Nano
        - 403: Authenticated user lacks permission for non-published Nano
        - 404: Nano not found
        """,
        responses={
            200: {"description": "Nano detail retrieved successfully"},
            401: {"description": "Authentication required for non-published Nano"},
            403: {"description": "Not authorized to access non-published Nano"},
            404: {"description": "Nano not found"},
        },
    )
    async def get_nano_detail_view(
        nano_id: UUID,
        current_user: Annotated[TokenData | None, Depends(get_optional_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> NanoDetailResponse:
        """Get Nano detail payload with visibility and download-access hints."""
        return await get_nano_detail(nano_id=nano_id, db=db, current_user=current_user)

    @router.get(
        "/{nano_id}/ratings",
        response_model=NanoRatingReadResponse,
        status_code=status.HTTP_200_OK,
        summary="Get Nano rating aggregation",
        description="""
        Retrieve aggregated rating metrics (average, median, distribution, votes) for one Nano.

        **Rules:**
        - Aggregation is available only for published Nanos
        - Endpoint is public for published Nanos
        - If authenticated, response includes caller's own rating (if present)

        **Error Cases:**
        - 400: Nano is not published (ratings not allowed)
        - 404: Nano not found
        """,
        responses={
            200: {"description": "Rating aggregation retrieved successfully"},
            400: {"description": "Nano is not published"},
            404: {"description": "Nano not found"},
        },
    )
    async def get_nano_rating_summary(
        nano_id: UUID,
        current_user: Annotated[TokenData | None, Depends(get_optional_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> NanoRatingReadResponse:
        """Get aggregate rating metrics and optional caller rating for a Nano."""
        return await get_nano_ratings(nano_id=nano_id, db=db, current_user=current_user)

    @router.post(
        "/{nano_id}/ratings",
        response_model=NanoRatingMutationResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Create a Nano star rating",
        description="""
        Create a 1-5 star rating for the authenticated user.

        **Rules:**
        - Authentication required
        - Exactly one rating per user per Nano
        - Rating is allowed only for published Nanos

        **Error Cases:**
        - 400: Nano is not published
        - 401: Not authenticated
        - 404: Nano not found
        - 409: Rating by current user already exists
        - 422: Invalid score (must be 1-5)
        """,
        responses={
            201: {"description": "Rating created successfully"},
            400: {"description": "Nano is not published"},
            401: {"description": "Not authenticated"},
            404: {"description": "Nano not found"},
            409: {"description": "Rating already exists for this user and Nano"},
            422: {"description": "Invalid score value"},
        },
    )
    async def create_nano_rating_endpoint(
        nano_id: UUID,
        payload: NanoRatingUpsertRequest,
        current_user: Annotated[TokenData, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> NanoRatingMutationResponse:
        """Create a star rating for the authenticated user."""
        return await create_nano_rating(
            nano_id=nano_id,
            payload=payload,
            current_user=current_user,
            db=db,
        )

    @router.patch(
        "/{nano_id}/ratings/me",
        response_model=NanoRatingMutationResponse,
        status_code=status.HTTP_200_OK,
        summary="Update own Nano star rating",
        description="""
        Update the authenticated user's existing 1-5 star rating for a Nano.

        **Rules:**
        - Authentication required
        - User must already have a rating for this Nano
        - Rating is allowed only for published Nanos

        **Error Cases:**
        - 400: Nano is not published
        - 401: Not authenticated
        - 404: Nano not found or user has no rating yet
        - 422: Invalid score (must be 1-5)
        """,
        responses={
            200: {"description": "Rating updated successfully"},
            400: {"description": "Nano is not published"},
            401: {"description": "Not authenticated"},
            404: {"description": "Nano or rating not found"},
            422: {"description": "Invalid score value"},
        },
    )
    async def update_my_nano_rating_endpoint(
        nano_id: UUID,
        payload: NanoRatingUpsertRequest,
        current_user: Annotated[TokenData, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> NanoRatingMutationResponse:
        """Update the authenticated user's star rating."""
        return await update_nano_rating(
            nano_id=nano_id,
            payload=payload,
            current_user=current_user,
            db=db,
        )

    @router.patch(
        "/{nano_id}/ratings/{rating_id}/moderation",
        response_model=NanoRatingModerationResponse,
        status_code=status.HTTP_200_OK,
        summary="Moderate a Nano rating",
        description="""
        Approve or hide a rating for a published Nano.

        **Rules:**
        - Authentication required
        - Only moderators and admins may moderate ratings
        - Public rating aggregation includes approved ratings only

        **Error Cases:**
        - 400: Nano is not published
        - 401: Not authenticated
        - 403: User lacks moderator/admin role
        - 404: Nano or rating not found
        - 422: Invalid moderation status
        """,
        responses={
            200: {"description": "Rating moderated successfully"},
            400: {"description": "Nano is not published"},
            401: {"description": "Not authenticated"},
            403: {"description": "User lacks moderator/admin role"},
            404: {"description": "Nano or rating not found"},
            422: {"description": "Invalid moderation payload"},
        },
    )
    async def moderate_nano_rating_endpoint(
        nano_id: UUID,
        rating_id: UUID,
        payload: FeedbackModerationRequest,
        current_user: Annotated[
            TokenData,
            Depends(
                require_any_role(
                    ROLE_MODERATOR,
                    ROLE_ADMIN,
                    detail="Only moderators and admins can moderate ratings",
                )
            ),
        ],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> NanoRatingModerationResponse:
        """Moderate one rating as moderator/admin."""
        response = await moderate_nano_rating(
            nano_id=nano_id,
            rating_id=rating_id,
            moderation=payload,
            current_user=current_user,
            db=db,
        )
        record_feedback_moderation_decision(feedback_type="rating", decision=payload.status)
        return response

    @router.get(
        "/{nano_id}/comments",
        response_model=NanoCommentListResponse,
        status_code=status.HTTP_200_OK,
        summary="List Nano comments",
        description="""
        Retrieve paginated comments for one published Nano.

        **Rules:**
        - Listing is available only for published Nanos
        - Endpoint is public for published Nanos
        - Results are stably sorted by `updated_at DESC, id DESC`

        **Query Parameters:**
        - `page`: Page number (1-indexed, default 1)
        - `limit`: Results per page (default 20, max 100)

        **Error Cases:**
        - 400: Nano is not published (comments not allowed)
        - 404: Nano not found
        """,
        responses={
            200: {"description": "Comments retrieved successfully"},
            400: {"description": "Nano is not published"},
            404: {"description": "Nano not found"},
        },
    )
    async def list_nano_comments_endpoint(
        nano_id: UUID,
        db: Annotated[AsyncSession, Depends(get_db)],
        page: Annotated[int, Query(ge=1, description="Page number")] = 1,
        limit: Annotated[int, Query(ge=1, le=100, description="Results per page")] = 20,
    ) -> NanoCommentListResponse:
        """List comments for a published Nano with deterministic pagination."""
        return await get_nano_comments(nano_id=nano_id, db=db, page=page, limit=limit)

    @router.post(
        "/{nano_id}/comments",
        response_model=NanoCommentMutationResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Create a Nano comment",
        description="""
        Create a comment/review for the authenticated user on a published Nano.

        **Rules:**
        - Authentication required
        - One comment per user per Nano
        - Comment content is validated (non-empty, length-limited) and sanitized
        - Allowed only for published Nanos

        **Error Cases:**
        - 400: Nano is not published
        - 401: Not authenticated
        - 404: Nano not found
        - 409: Comment by current user already exists
        - 422: Invalid request payload
        """,
        responses={
            201: {"description": "Comment created successfully"},
            400: {"description": "Nano is not published"},
            401: {"description": "Not authenticated"},
            404: {"description": "Nano not found"},
            409: {"description": "Comment already exists for this user and Nano"},
            422: {"description": "Invalid content value"},
        },
    )
    async def create_nano_comment_endpoint(
        nano_id: UUID,
        payload: NanoCommentUpsertRequest,
        current_user: Annotated[TokenData, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> NanoCommentMutationResponse:
        """Create a comment for the authenticated user."""
        return await create_nano_comment(
            nano_id=nano_id,
            payload=payload,
            current_user=current_user,
            db=db,
        )

    @router.patch(
        "/{nano_id}/comments/{comment_id}",
        response_model=NanoCommentMutationResponse,
        status_code=status.HTTP_200_OK,
        summary="Update a Nano comment",
        description="""
        Update an existing comment on a published Nano.

        **Rules:**
        - Authentication required
        - Comment owner can update own comment
        - Moderators and admins can update any comment
        - Comment content is validated and sanitized
        - Allowed only for published Nanos

        **Error Cases:**
        - 400: Nano is not published
        - 401: Not authenticated
        - 403: Caller is not allowed to edit this comment
        - 404: Nano or comment not found
        - 422: Invalid request payload
        """,
        responses={
            200: {"description": "Comment updated successfully"},
            400: {"description": "Nano is not published"},
            401: {"description": "Not authenticated"},
            403: {"description": "Not allowed to edit comment"},
            404: {"description": "Nano or comment not found"},
            422: {"description": "Invalid content value"},
        },
    )
    async def update_nano_comment_endpoint(
        nano_id: UUID,
        comment_id: UUID,
        payload: NanoCommentUpsertRequest,
        current_user: Annotated[TokenData, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> NanoCommentMutationResponse:
        """Update one comment by owner or moderator/admin."""
        return await update_nano_comment(
            nano_id=nano_id,
            comment_id=comment_id,
            payload=payload,
            current_user=current_user,
            db=db,
        )

    @router.patch(
        "/{nano_id}/comments/{comment_id}/moderation",
        response_model=NanoCommentModerationResponse,
        status_code=status.HTTP_200_OK,
        summary="Moderate a Nano comment",
        description="""
        Approve or hide a comment for a published Nano.

        **Rules:**
        - Authentication required
        - Only moderators and admins may moderate comments
        - Public comment listings include approved comments only

        **Error Cases:**
        - 400: Nano is not published
        - 401: Not authenticated
        - 403: User lacks moderator/admin role
        - 404: Nano or comment not found
        - 422: Invalid moderation status
        """,
        responses={
            200: {"description": "Comment moderated successfully"},
            400: {"description": "Nano is not published"},
            401: {"description": "Not authenticated"},
            403: {"description": "User lacks moderator/admin role"},
            404: {"description": "Nano or comment not found"},
            422: {"description": "Invalid moderation payload"},
        },
    )
    async def moderate_nano_comment_endpoint(
        nano_id: UUID,
        comment_id: UUID,
        payload: FeedbackModerationRequest,
        current_user: Annotated[
            TokenData,
            Depends(
                require_any_role(
                    ROLE_MODERATOR,
                    ROLE_ADMIN,
                    detail="Only moderators and admins can moderate comments",
                )
            ),
        ],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> NanoCommentModerationResponse:
        """Moderate one comment as moderator/admin."""
        response = await moderate_nano_comment(
            nano_id=nano_id,
            comment_id=comment_id,
            moderation=payload,
            current_user=current_user,
            db=db,
        )
        record_feedback_moderation_decision(feedback_type="comment", decision=payload.status)
        return response

    @router.get(
        "/{nano_id}/download-info",
        response_model=NanoDownloadInfoResponse,
        summary="Get Nano download URL",
        description="""
        Resolve a presigned download URL for a Nano.

        **Access Rules:**
        - Authentication required
        - Published Nanos: any authenticated user
        - Non-published Nanos: creator, admin, moderator only

        **Response Contract:**
        - Unified envelope: `success/data/meta/timestamp`

        **Error Cases:**
        - 401: Missing or invalid authentication
        - 403: Authenticated user not allowed for this Nano
        - 404: Nano or download path not found
        - 503: Storage URL generation unavailable
        """,
        responses={
            200: {"description": "Download URL resolved successfully"},
            401: {"description": "Authentication required"},
            403: {"description": "Not authorized to download this Nano"},
            404: {"description": "Nano or download path not found"},
            503: {"description": "Download URL generation failed"},
        },
    )
    async def get_nano_download(
        nano_id: UUID,
        current_user: Annotated[TokenData, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> NanoDownloadInfoResponse:
        """Get a presigned Nano download URL with strict authentication and RBAC checks."""
        return await get_nano_download_info(
            nano_id=nano_id,
            db=db,
            current_user=current_user,
        )

    @router.get(
        "/{nano_id}/download",
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        summary="Download Nano file",
        description="""
        Resolve and redirect to a temporary download URL for a Nano file.

        **Access Rules:**
        - Authentication required
        - Published Nanos: any authenticated user
        - Non-published Nanos: creator, admin, moderator only

        **Error Cases:**
        - 401: Missing or invalid authentication
        - 403: Authenticated user not allowed for this Nano
        - 404: Nano or download path not found
        - 503: Storage URL generation unavailable
        """,
        responses={
            307: {"description": "Redirect to signed download URL"},
            401: {"description": "Authentication required"},
            403: {"description": "Not authorized to download this Nano"},
            404: {"description": "Nano or download path not found"},
            503: {"description": "Download URL generation failed"},
        },
    )
    async def download_nano_file(
        nano_id: UUID,
        current_user: Annotated[TokenData, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> RedirectResponse:
        """Redirect caller to a presigned object-storage download URL."""
        download_info = await get_nano_download_info(
            nano_id=nano_id,
            db=db,
            current_user=current_user,
        )

        return RedirectResponse(
            url=download_info.data.download_url,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    @router.post(
        "/{nano_id}/metadata",
        response_model=MetadataUpdateResponse,
        status_code=status.HTTP_200_OK,
        summary="Update Nano metadata",
        description="""
        Update metadata for a Nano in draft status.

        **Requirements:**
        - Authentication required (Bearer token)
        - User must be the creator of the Nano
        - Nano must be in draft status (published Nanos have immutable metadata)
        - At least one field must be provided

        **Validation:**
        - title: 1-200 characters
        - description: max 2000 characters
        - duration_minutes: 1-1440 (positive, max 24 hours)
        - competency_level: beginner, intermediate, or advanced
        - language: ISO 639-1 code (exactly 2 characters)
        - format: video, text, quiz, interactive, or mixed
        - category_ids: max 5 categories (must exist in database)
        - license: CC-BY, CC-BY-SA, CC0, or proprietary

        **Business Rules:**
        - Only draft Nanos can be edited
        - Published Nanos have immutable metadata
        - Only the creator can update metadata

        **Error Cases:**
        - 400: Invalid data, Nano not in draft status, or category not found
        - 401: Not authenticated
        - 403: Not the creator
        - 404: Nano not found
        """,
        responses={
            200: {
                "description": "Metadata updated successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "nano_id": "123e4567-e89b-12d3-a456-426614174000",
                            "status": "draft",
                            "message": "Metadata updated successfully",
                            "updated_fields": ["title", "description", "duration_minutes"],
                        }
                    }
                },
            },
            400: {"description": "Invalid data, Nano not in draft status, or category not found"},
            401: {"description": "Not authenticated"},
            403: {"description": "Not authorized (not the creator)"},
            404: {"description": "Nano not found"},
        },
    )
    async def update_metadata(
        nano_id: UUID,
        metadata: MetadataUpdateRequest,
        current_user_id: Annotated[UUID, Depends(get_current_user_id)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> MetadataUpdateResponse:
        """Update Nano metadata."""
        # Validate at least one field is provided (use model_fields_set to detect provided fields)
        if not metadata.model_fields_set:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one field must be provided for update",
            )

        nano, updated_fields = await update_nano_metadata(nano_id, metadata, current_user_id, db)

        return MetadataUpdateResponse(
            nano_id=nano.id,
            status=nano.status.value.lower(),
            message="Metadata updated successfully",
            updated_fields=updated_fields,
        )

    @router.patch(
        "/{nano_id}/status",
        response_model=StatusUpdateResponse,
        status_code=status.HTTP_200_OK,
        summary="Update Nano status",
        description="""
        Update the publishing status of a Nano with state machine validation.

        **Requirements:**
        - Authentication required (Bearer token)
        - User must be the creator of the Nano
        - Status transition must be valid according to state machine rules
        - For draft → published: metadata must be complete

        **Valid Status Transitions:**
        - draft → pending_review, published, archived, deleted
        - pending_review → draft, published, archived
        - published → archived (or draft within 24h of publication)
        - archived → deleted
        - deleted → (no transitions allowed)

        **Metadata Completeness Requirements for Publishing:**
        - title (required, non-empty)
        - description (required, non-empty)
        - duration_minutes (required, > 0)
        - language (required)

        **Business Rules:**
        - Only creators can change status
        - Published → draft transition only allowed within 24h of publication
        - Cannot delete published Nanos directly (must archive first)
        - Status changes trigger audit log entries
        - published_at timestamp set when transitioning to published
        - archived_at timestamp set when transitioning to archived

        **Error Cases:**
        - 400: Invalid status transition or incomplete metadata
        - 401: Not authenticated
        - 403: Not the creator
        - 404: Nano not found
        - 422: Invalid status value (request validation error)
        """,
        responses={
            200: {
                "description": "Status updated successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "nano_id": "123e4567-e89b-12d3-a456-426614174000",
                            "old_status": "draft",
                            "new_status": "published",
                            "message": "Status updated successfully",
                            "published_at": "2026-03-08T15:30:00Z",
                            "archived_at": None,
                        }
                    }
                },
            },
            400: {"description": "Invalid status transition or incomplete metadata"},
            401: {"description": "Not authenticated"},
            403: {"description": "Not authorized (not the creator)"},
            404: {"description": "Nano not found"},
            422: {"description": "Invalid status value (request validation error)"},
        },
    )
    async def update_status(
        nano_id: UUID,
        status_update: StatusUpdateRequest,
        current_user: Annotated[TokenData, Depends(get_current_user)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> StatusUpdateResponse:
        """Update Nano status with state machine validation."""
        nano, old_status, new_status = await update_nano_status(
            nano_id, status_update, current_user, db
        )

        return StatusUpdateResponse(
            nano_id=nano.id,
            old_status=old_status,
            new_status=new_status,
            message=f"Status updated from '{old_status}' to '{new_status}'",
            published_at=nano.published_at,
            archived_at=nano.archived_at,
        )

    @router.post(
        "/{nano_id}/takedown",
        response_model=AdminTakedownResponse,
        status_code=status.HTTP_200_OK,
        summary="Admin takedown for public Nano content",
        description="""
        Execute an admin-only takedown for a Nano.

        **Requirements:**
        - Authentication required
        - Caller must have `admin` role
        - `reason` is required and stored for audit trail purposes

        **Behavior:**
        - Published Nanos are moved to `archived` to remove them from public views
        - Non-public Nanos remain unchanged and return deterministic `already_removed=true`
        - Every request writes a structured audit event

        **Error Cases:**
        - 401: Not authenticated
        - 403: Caller is not an admin
        - 404: Nano not found
        """,
        responses={
            200: {"description": "Takedown processed successfully"},
            401: {"description": "Not authenticated"},
            403: {"description": "Admin role required"},
            404: {"description": "Nano not found"},
        },
    )
    async def takedown_nano(
        nano_id: UUID,
        takedown_request: AdminTakedownRequest,
        current_user: Annotated[TokenData, Depends(require_role(ROLE_ADMIN))],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> AdminTakedownResponse:
        """Perform an admin takedown and return the action result."""
        return await admin_takedown_nano(
            nano_id=nano_id,
            takedown_request=takedown_request,
            current_user=current_user,
            db=db,
        )

    @router.delete(
        "/{nano_id}",
        response_model=NanoDeleteResponse,
        status_code=status.HTTP_200_OK,
        summary="Delete a Nano",
        description="""
        Delete (soft-delete) a Nano owned by the authenticated creator.

        **Requirements:**
        - Authentication required (Bearer token)
        - User must be the creator of the Nano
        - Nano must be in draft or archived status (published Nanos must be archived first)

        **Business Rules:**
        - Only draft/archived Nanos can be deleted
        - Published Nanos must be archived first via status transition
        - Deletion is soft-delete (status set to 'deleted')
        - Only the creator can delete their own Nanos

        **Error Cases:**
        - 400: Nano in invalid state for deletion (e.g., published)
        - 401: Not authenticated
        - 403: Not the creator of the Nano
        - 404: Nano not found
        """,
        responses={
            200: {
                "description": "Nano deleted successfully",
                "content": {
                    "application/json": {
                        "example": {
                            "nano_id": "123e4567-e89b-12d3-a456-426614174000",
                            "status": "deleted",
                            "message": "Nano deleted successfully",
                        }
                    }
                },
            },
            400: {"description": "Nano in invalid state for deletion"},
            401: {"description": "Not authenticated"},
            403: {"description": "Not authorized (not the creator)"},
            404: {"description": "Nano not found"},
        },
    )
    async def delete_nano_endpoint(
        nano_id: UUID,
        current_user_id: Annotated[UUID, Depends(get_current_user_id)],
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> NanoDeleteResponse:
        """Delete a Nano."""
        return await delete_nano(
            nano_id=nano_id,
            creator_id=current_user_id,
            db=db,
        )

    return router
