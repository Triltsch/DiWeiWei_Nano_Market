import axios from "axios";

import { httpClient } from "./httpClient";

export interface NanoDetailCategory {
  categoryId: string;
  categoryName: string;
}

export interface NanoDetailMetadata {
  description: string | null;
  durationMinutes: number | null;
  competencyLevel: string;
  language: string;
  format: string;
  status: string;
  version: string;
  categories: NanoDetailCategory[];
  license: string;
  thumbnailUrl: string | null;
  uploadedAt: string;
  publishedAt: string | null;
  updatedAt: string;
}

export interface NanoDetailCreator {
  id: string;
  username: string | null;
}

export interface NanoRatingSummary {
  averageRating: number;
  ratingCount: number;
  downloadCount: number;
}

export interface NanoDownloadAccess {
  requiresAuthentication: boolean;
  canDownload: boolean;
  downloadPath: string | null;
}

export interface NanoDetail {
  nanoId: string;
  title: string;
  metadata: NanoDetailMetadata;
  creator: NanoDetailCreator;
  ratingSummary: NanoRatingSummary;
  downloadInfo: NanoDownloadAccess;
}

export interface NanoDownloadInfo {
  nanoId: string;
  canDownload: boolean;
  downloadPath: string;
}

type NanoDetailApiErrorCode =
  | "not-found"
  | "unauthorized"
  | "forbidden"
  | "request-failed"
  | "unknown";

interface ErrorResponseBody {
  detail?: string;
}

interface RawNanoDetailCategory {
  category_id?: unknown;
  category_name?: unknown;
}

interface RawNanoDetailMetadata {
  description?: unknown;
  duration_minutes?: unknown;
  competency_level?: unknown;
  language?: unknown;
  format?: unknown;
  status?: unknown;
  version?: unknown;
  categories?: unknown;
  license?: unknown;
  thumbnail_url?: unknown;
  uploaded_at?: unknown;
  published_at?: unknown;
  updated_at?: unknown;
}

interface RawNanoDetailCreator {
  id?: unknown;
  username?: unknown;
}

interface RawNanoRatingSummary {
  average_rating?: unknown;
  rating_count?: unknown;
  download_count?: unknown;
}

interface RawNanoDownloadInfo {
  requires_authentication?: unknown;
  can_download?: unknown;
  download_path?: unknown;
}

interface RawNanoDetailData {
  nano_id?: unknown;
  title?: unknown;
  metadata?: unknown;
  creator?: unknown;
  rating_summary?: unknown;
  download_info?: unknown;
}

interface RawNanoDetailResponse {
  data?: unknown;
}

interface RawNanoDownloadInfoData {
  nano_id?: unknown;
  can_download?: unknown;
  download_path?: unknown;
}

interface RawNanoDownloadInfoResponse {
  data?: unknown;
}

function asString(value: unknown): string | null {
  if (typeof value === "string" && value.trim().length > 0) {
    return value;
  }
  return null;
}

function asNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim().length > 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function asBoolean(value: unknown): boolean {
  return value === true;
}

function mapNanoDetailCategory(raw: RawNanoDetailCategory, index: number): NanoDetailCategory {
  return {
    categoryId: asString(raw.category_id) ?? `category-${index}`,
    categoryName: asString(raw.category_name) ?? "",
  };
}

function mapNanoDetail(raw: RawNanoDetailData): NanoDetail {
  const metadata = (raw.metadata as RawNanoDetailMetadata | undefined) ?? {};
  const creator = (raw.creator as RawNanoDetailCreator | undefined) ?? {};
  const ratingSummary = (raw.rating_summary as RawNanoRatingSummary | undefined) ?? {};
  const downloadInfo = (raw.download_info as RawNanoDownloadInfo | undefined) ?? {};
  const categoriesRaw = Array.isArray(metadata.categories)
    ? (metadata.categories as RawNanoDetailCategory[])
    : [];

  return {
    nanoId: asString(raw.nano_id) ?? "",
    title: asString(raw.title) ?? "",
    metadata: {
      description: asString(metadata.description),
      durationMinutes: asNumber(metadata.duration_minutes),
      competencyLevel: asString(metadata.competency_level) ?? "",
      language: asString(metadata.language) ?? "",
      format: asString(metadata.format) ?? "",
      status: asString(metadata.status) ?? "",
      version: asString(metadata.version) ?? "",
      categories: categoriesRaw.map(mapNanoDetailCategory),
      license: asString(metadata.license) ?? "",
      thumbnailUrl: asString(metadata.thumbnail_url),
      uploadedAt: asString(metadata.uploaded_at) ?? "",
      publishedAt: asString(metadata.published_at),
      updatedAt: asString(metadata.updated_at) ?? "",
    },
    creator: {
      id: asString(creator.id) ?? "",
      username: asString(creator.username),
    },
    ratingSummary: {
      averageRating: asNumber(ratingSummary.average_rating) ?? 0,
      ratingCount: asNumber(ratingSummary.rating_count) ?? 0,
      downloadCount: asNumber(ratingSummary.download_count) ?? 0,
    },
    downloadInfo: {
      requiresAuthentication: asBoolean(downloadInfo.requires_authentication),
      canDownload: asBoolean(downloadInfo.can_download),
      downloadPath: asString(downloadInfo.download_path),
    },
  };
}

function getErrorCode(error: unknown): NanoDetailApiErrorCode {
  if (axios.isAxiosError<ErrorResponseBody>(error)) {
    const status = error.response?.status;
    if (status === 404) {
      return "not-found";
    }
    if (status === 401) {
      return "unauthorized";
    }
    if (status === 403) {
      return "forbidden";
    }
    if (status) {
      return "request-failed";
    }
  }

  return "unknown";
}

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ErrorResponseBody>(error)) {
    const detail = error.response?.data?.detail;
    if (detail && detail.trim().length > 0) {
      return detail;
    }
    return "Request failed";
  }

  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  return "Request failed";
}

export class NanoDetailApiError extends Error {
  code: NanoDetailApiErrorCode;

  constructor(message: string, code: NanoDetailApiErrorCode) {
    super(message);
    this.name = "NanoDetailApiError";
    this.code = code;
  }
}

export async function getNanoDetail(nanoId: string): Promise<NanoDetail> {
  try {
    const response = await httpClient.get<RawNanoDetailResponse>(`/api/v1/nanos/${nanoId}/detail`);
    const rawData = (response.data.data as RawNanoDetailData | undefined) ?? {};
    return mapNanoDetail(rawData);
  } catch (error) {
    throw new NanoDetailApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function getNanoDownloadInfo(nanoId: string): Promise<NanoDownloadInfo> {
  try {
    const response = await httpClient.get<RawNanoDownloadInfoResponse>(
      `/api/v1/nanos/${nanoId}/download-info`
    );
    const rawData = (response.data.data as RawNanoDownloadInfoData | undefined) ?? {};
    const downloadPath = asString(rawData.download_path) ?? "";

    return {
      nanoId: asString(rawData.nano_id) ?? nanoId,
      canDownload: asBoolean(rawData.can_download),
      downloadPath,
    };
  } catch (error) {
    throw new NanoDetailApiError(getErrorMessage(error), getErrorCode(error));
  }
}
