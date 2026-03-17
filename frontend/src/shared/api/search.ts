import { httpClient } from "./httpClient";

export interface SearchFilters {
  category?: string;
  level?: string;
  duration?: string;
  language?: string;
}

export interface SearchRequest {
  query: string;
  filters: SearchFilters;
  limit: number;
  page?: number;
  offset?: number;
}

export interface SearchNano {
  id: string;
  /** Null when the API returns no title; the UI renders a localised fallback. */
  title: string | null;
  /** Null when the API returns no creator; the UI renders a localised fallback. */
  creator: string | null;
  averageRating: number | null;
  durationMinutes: number | null;
}

export interface SearchResponse {
  items: SearchNano[];
  total: number | null;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNextPage: boolean;
  hasPrevPage: boolean;
}

interface RawSearchPagination {
  current_page?: unknown;
  page_size?: unknown;
  total_results?: unknown;
  total_pages?: unknown;
  has_next_page?: unknown;
  has_prev_page?: unknown;
}

interface RawSearchMeta {
  pagination?: unknown;
}

interface RawSearchNano {
  id?: unknown;
  nano_id?: unknown;
  title?: unknown;
  name?: unknown;
  creator?: unknown;
  creator_name?: unknown;
  avg_rating?: unknown;
  average_rating?: unknown;
  rating?: unknown;
  duration?: unknown;
  duration_minutes?: unknown;
}

interface RawSearchResponse {
  success?: unknown;
  data?: unknown;
  meta?: unknown;
  results?: unknown;
  items?: unknown;
  hits?: unknown;
  total?: unknown;
  estimatedTotalHits?: unknown;
  nbHits?: unknown;
}

function asBoolean(value: unknown): boolean | null {
  if (typeof value === "boolean") {
    return value;
  }

  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (normalized === "true") {
      return true;
    }
    if (normalized === "false") {
      return false;
    }
  }

  return null;
}

function normalizeLevel(level: string | undefined): string | undefined {
  if (!level) {
    return undefined;
  }

  const normalized = level.trim().toLowerCase();
  switch (normalized) {
    case "beginner":
      return "1";
    case "intermediate":
      return "2";
    case "advanced":
      return "3";
    default:
      return normalized.length > 0 ? normalized : undefined;
  }
}

function asString(value: unknown): string | null {
  if (typeof value === "string" && value.trim().length > 0) {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return null;
}

function asNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string" && value.trim().length > 0) {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return null;
}

function mapSearchNano(rawItem: RawSearchNano, index: number): SearchNano {
  const fallbackId = `nano-${index}`;

  return {
    id: asString(rawItem.id) ?? asString(rawItem.nano_id) ?? fallbackId,
    // Return null for missing title/creator – the UI renders localised fallbacks via t().
    title: asString(rawItem.title) ?? asString(rawItem.name) ?? null,
    creator: asString(rawItem.creator_name) ?? asString(rawItem.creator) ?? null,
    averageRating:
      asNumber(rawItem.average_rating) ?? asNumber(rawItem.avg_rating) ?? asNumber(rawItem.rating),
    durationMinutes: asNumber(rawItem.duration_minutes) ?? asNumber(rawItem.duration),
  };
}

function mapSearchResponse(rawData: RawSearchResponse): SearchResponse {
  const rawMeta = (rawData.meta as RawSearchMeta | undefined) ?? undefined;
  const rawPagination = (rawMeta?.pagination as RawSearchPagination | undefined) ?? undefined;
  const rawItems =
    (Array.isArray(rawData.data) && rawData.data) ||
    (Array.isArray(rawData.results) && rawData.results) ||
    (Array.isArray(rawData.items) && rawData.items) ||
    (Array.isArray(rawData.hits) && rawData.hits) ||
    [];

  const items = rawItems.map((entry, index) => mapSearchNano(entry as RawSearchNano, index));
  const total =
    asNumber(rawPagination?.total_results) ??
    asNumber(rawData.total) ??
    asNumber(rawData.estimatedTotalHits) ??
    asNumber(rawData.nbHits);
  const page = asNumber(rawPagination?.current_page) ?? 1;
  const pageSize = asNumber(rawPagination?.page_size) ?? items.length;
  const totalPages = asNumber(rawPagination?.total_pages) ?? 0;
  const hasNextPage = asBoolean(rawPagination?.has_next_page) ?? false;
  const hasPrevPage = asBoolean(rawPagination?.has_prev_page) ?? false;

  return {
    items,
    total,
    page,
    pageSize,
    totalPages,
    hasNextPage,
    hasPrevPage,
  };
}

/**
 * Calls GET /api/v1/search on the backend discovery endpoint.
 */
export async function searchNanos(request: SearchRequest): Promise<SearchResponse> {
  const effectivePage =
    request.page ??
    (typeof request.offset === "number" && request.limit > 0
      ? Math.floor(request.offset / request.limit) + 1
      : 1);

  const params = {
    q: request.query || undefined,
    category: request.filters.category || undefined,
    level: normalizeLevel(request.filters.level),
    duration: request.filters.duration || undefined,
    language: request.filters.language || undefined,
    page: effectivePage,
    limit: request.limit,
  };

  const response = await httpClient.get<RawSearchResponse>("/api/v1/search", { params });
  return mapSearchResponse(response.data);
}
