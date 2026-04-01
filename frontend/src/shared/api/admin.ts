import axios from "axios";

import { httpClient } from "./httpClient";
import type { AuthRole } from "./types";

export type AdminUserStatus = "active" | "inactive" | "suspended" | "deleted";
export type ModerationContentType = "nano" | "nano_rating" | "nano_comment";
export type ModerationCaseStatus = "pending" | "approved" | "rejected" | "deferred" | "escalated";
export type ModerationDecision = "approve" | "reject" | "defer" | "escalate";

type AdminApiErrorCode = "unauthorized" | "forbidden" | "validation" | "not-found" | "generic";

interface RawAdminUser {
  id: string;
  email: string;
  username: string;
  first_name: string | null;
  last_name: string | null;
  bio: string | null;
  preferred_language: string;
  status: AdminUserStatus;
  role: AuthRole;
  email_verified: boolean;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
  last_login: string | null;
  profile_avatar: string | null;
  company: string | null;
  job_title: string | null;
  phone: string | null;
}

interface RawAdminUsersResponse {
  users: RawAdminUser[];
  total: number;
  limit: number;
  offset: number;
}

interface RawAuditLogItem {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  metadata: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

interface RawAuditLogsResponse {
  logs: RawAuditLogItem[];
  total: number;
  limit: number;
  offset: number;
}

interface RawNanoContentDetail {
  title: string;
  creator_username: string | null;
  status: string;
  description: string | null;
  uploaded_at: string | null;
}

interface RawRatingContentDetail {
  nano_id: string;
  score: number;
  author_username: string | null;
  moderation_status: string;
  created_at: string | null;
}

interface RawCommentContentDetail {
  nano_id: string;
  content: string;
  author_username: string | null;
  moderation_status: string;
  created_at: string | null;
}

type RawModerationContentDetail =
  | RawNanoContentDetail
  | RawRatingContentDetail
  | RawCommentContentDetail;

interface RawModerationCaseItem {
  case_id: string;
  content_type: ModerationContentType;
  content_id: string;
  reporter_id: string | null;
  status: ModerationCaseStatus;
  reason: string | null;
  decided_by_user_id: string | null;
  decided_at: string | null;
  deferred_until: string | null;
  escalation_note: string | null;
  created_at: string;
  updated_at: string;
  content_detail: RawModerationContentDetail | null;
}

interface RawModerationQueueResponse {
  items: RawModerationCaseItem[];
  pagination: {
    current_page: number;
    page_size: number;
    total_results: number;
    total_pages: number;
    has_next_page: boolean;
    has_prev_page: boolean;
  };
}

interface RawAdminTakedownResponse {
  nano_id: string;
  old_status: string;
  new_status: string;
  already_removed: boolean;
  takedown_reason: string;
  taken_down_at: string;
  message: string;
}

export class AdminApiError extends Error {
  code: AdminApiErrorCode;

  constructor(message: string, code: AdminApiErrorCode) {
    super(message);
    this.name = "AdminApiError";
    this.code = code;
  }
}

export interface AdminUser {
  id: string;
  email: string;
  username: string;
  firstName: string | null;
  lastName: string | null;
  bio: string | null;
  preferredLanguage: string;
  status: AdminUserStatus;
  role: AuthRole;
  emailVerified: boolean;
  verifiedAt: string | null;
  createdAt: string;
  updatedAt: string;
  lastLogin: string | null;
  profileAvatar: string | null;
  company: string | null;
  jobTitle: string | null;
  phone: string | null;
}

export interface AdminUsersResponse {
  users: AdminUser[];
  total: number;
  limit: number;
  offset: number;
}

export interface AuditLogItem {
  id: string;
  userId: string | null;
  action: string;
  resourceType: string | null;
  resourceId: string | null;
  metadata: Record<string, unknown> | null;
  ipAddress: string | null;
  userAgent: string | null;
  createdAt: string;
}

export interface AuditLogsResponse {
  logs: AuditLogItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface NanoContentDetail {
  title: string;
  creatorUsername: string | null;
  status: string;
  description: string | null;
  uploadedAt: string | null;
}

export interface RatingContentDetail {
  nanoId: string;
  score: number;
  authorUsername: string | null;
  moderationStatus: string;
  createdAt: string | null;
}

export interface CommentContentDetail {
  nanoId: string;
  content: string;
  authorUsername: string | null;
  moderationStatus: string;
  createdAt: string | null;
}

export type ModerationContentDetail = NanoContentDetail | RatingContentDetail | CommentContentDetail;

export interface ModerationCaseItem {
  caseId: string;
  contentType: ModerationContentType;
  contentId: string;
  reporterId: string | null;
  status: ModerationCaseStatus;
  reason: string | null;
  decidedByUserId: string | null;
  decidedAt: string | null;
  deferredUntil: string | null;
  escalationNote: string | null;
  createdAt: string;
  updatedAt: string;
  contentDetail: ModerationContentDetail | null;
}

export interface ModerationQueueResponse {
  items: ModerationCaseItem[];
  pagination: {
    currentPage: number;
    pageSize: number;
    totalResults: number;
    totalPages: number;
    hasNextPage: boolean;
    hasPrevPage: boolean;
  };
}

export interface AdminTakedownResponse {
  nanoId: string;
  oldStatus: string;
  newStatus: string;
  alreadyRemoved: boolean;
  takedownReason: string;
  takenDownAt: string;
  message: string;
}

export interface GetAdminUsersParams {
  search?: string;
  role?: AuthRole | "all";
  status?: AdminUserStatus | "all";
  limit?: number;
  offset?: number;
}

export interface GetAuditLogsParams {
  action?: string;
  resourceType?: string;
  limit?: number;
  offset?: number;
}

export interface GetAdminModerationQueueParams {
  contentType?: ModerationContentType | "all";
  status?: ModerationCaseStatus | "all";
  page?: number;
  limit?: number;
}

export interface ReviewModerationCaseRequest {
  decision: ModerationDecision;
  reason?: string;
  deferredUntil?: string;
}

function mapAdminUser(user: RawAdminUser): AdminUser {
  return {
    id: user.id,
    email: user.email,
    username: user.username,
    firstName: user.first_name,
    lastName: user.last_name,
    bio: user.bio,
    preferredLanguage: user.preferred_language,
    status: user.status,
    role: user.role,
    emailVerified: user.email_verified,
    verifiedAt: user.verified_at,
    createdAt: user.created_at,
    updatedAt: user.updated_at,
    lastLogin: user.last_login,
    profileAvatar: user.profile_avatar,
    company: user.company,
    jobTitle: user.job_title,
    phone: user.phone,
  };
}

function mapAuditLog(log: RawAuditLogItem): AuditLogItem {
  return {
    id: log.id,
    userId: log.user_id,
    action: log.action,
    resourceType: log.resource_type,
    resourceId: log.resource_id,
    metadata: log.metadata,
    ipAddress: log.ip_address,
    userAgent: log.user_agent,
    createdAt: log.created_at,
  };
}

function mapModerationContentDetail(
  contentType: ModerationContentType,
  detail: RawModerationContentDetail | null,
): ModerationContentDetail | null {
  if (!detail) {
    return null;
  }

  if (contentType === "nano") {
    const nanoDetail = detail as RawNanoContentDetail;
    return {
      title: nanoDetail.title,
      creatorUsername: nanoDetail.creator_username,
      status: nanoDetail.status,
      description: nanoDetail.description,
      uploadedAt: nanoDetail.uploaded_at,
    };
  }

  if (contentType === "nano_rating") {
    const ratingDetail = detail as RawRatingContentDetail;
    return {
      nanoId: ratingDetail.nano_id,
      score: ratingDetail.score,
      authorUsername: ratingDetail.author_username,
      moderationStatus: ratingDetail.moderation_status,
      createdAt: ratingDetail.created_at,
    };
  }

  const commentDetail = detail as RawCommentContentDetail;
  return {
    nanoId: commentDetail.nano_id,
    content: commentDetail.content,
    authorUsername: commentDetail.author_username,
    moderationStatus: commentDetail.moderation_status,
    createdAt: commentDetail.created_at,
  };
}

function mapModerationCaseItem(item: RawModerationCaseItem): ModerationCaseItem {
  return {
    caseId: item.case_id,
    contentType: item.content_type,
    contentId: item.content_id,
    reporterId: item.reporter_id,
    status: item.status,
    reason: item.reason,
    decidedByUserId: item.decided_by_user_id,
    decidedAt: item.decided_at,
    deferredUntil: item.deferred_until,
    escalationNote: item.escalation_note,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
    contentDetail: mapModerationContentDetail(item.content_type, item.content_detail),
  };
}

function toAdminApiError(error: unknown): AdminApiError {
  if (!axios.isAxiosError(error)) {
    return new AdminApiError("Unknown error", "generic");
  }

  const detail = typeof error.response?.data?.detail === "string" ? error.response.data.detail : null;

  if (error.response?.status === 401) {
    return new AdminApiError(detail ?? "Unauthorized", "unauthorized");
  }
  if (error.response?.status === 403) {
    return new AdminApiError(detail ?? "Forbidden", "forbidden");
  }
  if (error.response?.status === 404) {
    return new AdminApiError(detail ?? "Not found", "not-found");
  }
  if (error.response?.status === 400 || error.response?.status === 422) {
    return new AdminApiError(detail ?? "Validation failed", "validation");
  }

  return new AdminApiError(detail ?? error.message ?? "Request failed", "generic");
}

export async function getAdminUsers(params: GetAdminUsersParams = {}): Promise<AdminUsersResponse> {
  try {
    const response = await httpClient.get<RawAdminUsersResponse>("/api/v1/admin/users", {
      params: {
        search: params.search?.trim() || undefined,
        role: params.role && params.role !== "all" ? params.role : undefined,
        status: params.status && params.status !== "all" ? params.status : undefined,
        limit: params.limit ?? 10,
        offset: params.offset ?? 0,
      },
    });

    return {
      users: response.data.users.map(mapAdminUser),
      total: response.data.total,
      limit: response.data.limit,
      offset: response.data.offset,
    };
  } catch (error) {
    throw toAdminApiError(error);
  }
}

export async function updateAdminUserRole(userId: string, role: AuthRole): Promise<AdminUser> {
  try {
    const response = await httpClient.patch<RawAdminUser>(`/api/v1/admin/users/${userId}/role`, {
      role,
    });
    return mapAdminUser(response.data);
  } catch (error) {
    throw toAdminApiError(error);
  }
}

export async function deleteAdminUser(userId: string): Promise<AdminUser> {
  try {
    const response = await httpClient.delete<RawAdminUser>(`/api/v1/admin/users/${userId}`);
    return mapAdminUser(response.data);
  } catch (error) {
    throw toAdminApiError(error);
  }
}

export async function getAdminAuditLogs(
  params: GetAuditLogsParams = {},
): Promise<AuditLogsResponse> {
  try {
    const response = await httpClient.get<RawAuditLogsResponse>("/api/v1/admin/audit-logs", {
      params: {
        action: params.action?.trim() || undefined,
        resource_type: params.resourceType?.trim() || undefined,
        limit: params.limit ?? 10,
        offset: params.offset ?? 0,
      },
    });

    return {
      logs: response.data.logs.map(mapAuditLog),
      total: response.data.total,
      limit: response.data.limit,
      offset: response.data.offset,
    };
  } catch (error) {
    throw toAdminApiError(error);
  }
}

export async function getAdminModerationQueue(
  params: GetAdminModerationQueueParams = {},
): Promise<ModerationQueueResponse> {
  try {
    const response = await httpClient.get<RawModerationQueueResponse>("/api/v1/moderation/queue", {
      params: {
        content_type:
          params.contentType && params.contentType !== "all" ? params.contentType : undefined,
        status: params.status ?? "pending",
        page: params.page ?? 1,
        limit: params.limit ?? 10,
      },
    });

    return {
      items: response.data.items.map(mapModerationCaseItem),
      pagination: {
        currentPage: response.data.pagination.current_page,
        pageSize: response.data.pagination.page_size,
        totalResults: response.data.pagination.total_results,
        totalPages: response.data.pagination.total_pages,
        hasNextPage: response.data.pagination.has_next_page,
        hasPrevPage: response.data.pagination.has_prev_page,
      },
    };
  } catch (error) {
    throw toAdminApiError(error);
  }
}

export async function reviewModerationCase(
  caseId: string,
  payload: ReviewModerationCaseRequest,
): Promise<ModerationCaseItem> {
  try {
    const response = await httpClient.post<RawModerationCaseItem>(
      `/api/v1/moderation/cases/${caseId}/review`,
      {
        decision: payload.decision,
        reason: payload.reason?.trim() || undefined,
        deferred_until: payload.deferredUntil ?? undefined,
      },
    );
    return mapModerationCaseItem(response.data);
  } catch (error) {
    throw toAdminApiError(error);
  }
}

export async function adminTakedownNano(
  nanoId: string,
  reason: string,
  note?: string,
): Promise<AdminTakedownResponse> {
  try {
    const response = await httpClient.post<RawAdminTakedownResponse>(
      `/api/v1/nanos/${nanoId}/takedown`,
      {
        reason,
        note: note?.trim() || undefined,
      },
    );

    return {
      nanoId: response.data.nano_id,
      oldStatus: response.data.old_status,
      newStatus: response.data.new_status,
      alreadyRemoved: response.data.already_removed,
      takedownReason: response.data.takedown_reason,
      takenDownAt: response.data.taken_down_at,
      message: response.data.message,
    };
  } catch (error) {
    throw toAdminApiError(error);
  }
}