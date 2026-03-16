"""Search module - Full-text search functionality using Meilisearch"""

from app.modules.search.router import get_search_router
from app.modules.search.schemas import SearchNano, SearchResponse

__all__ = ["get_search_router", "SearchNano", "SearchResponse"]
