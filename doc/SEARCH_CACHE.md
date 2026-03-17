# Search Cache Strategy (Story 7.4 / Issue #62)

## Scope
Redis cache for `GET /api/v1/search` responses to reduce repeated Meilisearch round-trips.

## Cache Key Strategy
- Prefix: `search:v1`
- Deterministic canonical key built from all query parameters:
  - `q`, `category`, `level`, `duration`, `language`, `page`, `limit`
- Canonicalization uses sorted query parameter encoding to ensure identical requests always map to the same key.

See [doc/SEARCH_OPERATIONS.md](./SEARCH_OPERATIONS.md) for the full frontend/backend search contract, pagination semantics, and Sprint-4 QA gate details.

## TTL
- `SEARCH_CACHE_TTL_SECONDS` default: `1800` (30 minutes)

## Invalidation Strategy
- Broad invalidation by key prefix (`search:v1:*`) on Nano data changes:
  - Metadata updates (`update_nano_metadata`)
  - Status transitions (`update_nano_status`)
- This guarantees consistency between search results and latest persisted Nano state.

## Degraded Mode
- Redis read/write/invalidate failures are handled defensively.
- Search falls back to live Meilisearch queries; API remains available.

## Observability Hooks
- Structured log events are emitted for:
  - `search_cache_hit`
  - `search_cache_miss`
  - `search_cache_store`
  - `search_cache_invalidate`
  - Redis-unavailable paths on get/set/invalidate
