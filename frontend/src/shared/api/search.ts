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
  offset: number;
}

export interface SearchNano {
  id: string;
  title: string;
  creator: string;
  averageRating: number | null;
  durationMinutes: number | null;
}

export interface SearchResponse {
  items: SearchNano[];
  total: number | null;
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
  results?: unknown;
  items?: unknown;
  hits?: unknown;
  total?: unknown;
  estimatedTotalHits?: unknown;
  nbHits?: unknown;
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
    title: asString(rawItem.title) ?? asString(rawItem.name) ?? "Untitled Nano",
    creator: asString(rawItem.creator_name) ?? asString(rawItem.creator) ?? "Unknown Creator",
    averageRating:
      asNumber(rawItem.average_rating) ?? asNumber(rawItem.avg_rating) ?? asNumber(rawItem.rating),
    durationMinutes: asNumber(rawItem.duration_minutes) ?? asNumber(rawItem.duration),
  };
}

function mapSearchResponse(rawData: RawSearchResponse): SearchResponse {
  const rawItems =
    (Array.isArray(rawData.results) && rawData.results) ||
    (Array.isArray(rawData.items) && rawData.items) ||
    (Array.isArray(rawData.hits) && rawData.hits) ||
    [];

  const items = rawItems.map((entry, index) => mapSearchNano(entry as RawSearchNano, index));
  const total =
    asNumber(rawData.total) ?? asNumber(rawData.estimatedTotalHits) ?? asNumber(rawData.nbHits);

  return {
    items,
    total,
  };
}

export async function searchNanos(request: SearchRequest): Promise<SearchResponse> {
  const params = {
    q: request.query || undefined,
    category: request.filters.category || undefined,
    level: request.filters.level || undefined,
    duration: request.filters.duration || undefined,
    language: request.filters.language || undefined,
    limit: request.limit,
    offset: request.offset,
  };

  const response = await httpClient.get<RawSearchResponse>("/api/v1/search", { params });
  return mapSearchResponse(response.data);
}
