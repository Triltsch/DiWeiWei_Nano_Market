"""
Pydantic schemas for search operations.

This module defines request and response models for the search API endpoint.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SearchNano(BaseModel):
    """
    Searched Nano result item.

    Represents a single Nano in search results with essential metadata
    for display and discovery.

    Attributes:
        id: Unique identifier of the Nano
        title: Nano title (nullable for robustness)
        description: Short description or summary
        creator: Creator/author name (nullable for robustness)
        duration_minutes: Estimated duration in minutes
        competency_level: Learning level (1=Basic, 2=Intermediate, 3=Advanced)
        category: Primary category name
        format: Content format (video, text, quiz, interactive, mixed)
        average_rating: Average rating (0.00-5.00)
        rating_count: Total number of ratings
        published_at: When the Nano was published
        thumbnail_url: URL to thumbnail image
    """

    id: UUID = Field(description="Unique identifier of the Nano")
    title: Optional[str] = Field(None, description="Nano title")
    description: Optional[str] = Field(None, description="Short description")
    creator: Optional[str] = Field(None, description="Creator/author name")
    duration_minutes: Optional[int] = Field(None, description="Estimated duration in minutes")
    competency_level: int = Field(
        description="Learning level (1=Basic, 2=Intermediate, 3=Advanced)"
    )
    category: Optional[str] = Field(None, description="Primary category name")
    format: str = Field(description="Content format")
    average_rating: Decimal = Field(description="Average rating (0.00-5.00)")
    rating_count: int = Field(description="Total number of ratings")
    published_at: datetime = Field(description="When the Nano was published")
    thumbnail_url: Optional[str] = Field(None, description="URL to thumbnail image")


class SearchPaginationMeta(BaseModel):
    """
    Pagination metadata for search results.

    Attributes:
        current_page: Current page number (1-indexed)
        page_size: Number of results per page
        total_results: Total number of results matching the query
        total_pages: Total number of pages
        has_next_page: Whether there is a next page
        has_prev_page: Whether there is a previous page
    """

    current_page: int = Field(ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(ge=1, description="Number of results per page")
    total_results: int = Field(ge=0, description="Total number of results matching the query")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next_page: bool = Field(description="Whether there is a next page")
    has_prev_page: bool = Field(description="Whether there is a previous page")


class SearchResponse(BaseModel):
    """
    Complete search response with results and metadata.

    Follows the unified API response format: success/data/meta/timestamp.

    Attributes:
        success: Whether the search was successful
        data: List of Nano search results
        meta: Pagination metadata and filter information
        timestamp: ISO 8601 timestamp when the response was generated
    """

    success: bool = Field(description="Whether the search was successful")
    data: list[SearchNano] = Field(description="List of Nano search results")
    meta: dict = Field(description="Pagination metadata and filter information")
    timestamp: datetime = Field(description="ISO 8601 timestamp when the response was generated")
