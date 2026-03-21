import axios from "axios";

import { httpClient } from "./httpClient";

type UploadApiErrorKey =
  | "upload_error_upload_failed"
  | "upload_error_metadata_failed"
  | "upload_error_publish_failed"
  | "upload_error_network"
  | "upload_error_service_unavailable"
  | "upload_error_file_too_large";

export interface UploadNanoResponse {
  nano_id: string;
  status: string;
  title: string;
  uploaded_at: string;
  message: string;
}

export interface UpdateNanoMetadataRequest {
  title?: string;
  description?: string;
  duration_minutes?: number;
  competency_level?: "beginner" | "intermediate" | "advanced";
  language?: string;
  format?: "video" | "text" | "quiz" | "interactive" | "mixed";
  license?: "CC-BY" | "CC-BY-SA" | "CC0" | "proprietary";
}

export interface UpdateNanoMetadataResponse {
  nano_id: string;
  status: string;
  message: string;
  updated_fields: string[];
}

export interface UpdateNanoStatusResponse {
  nano_id: string;
  old_status: string;
  new_status: string;
  message: string;
  published_at: string | null;
  archived_at: string | null;
}

interface ApiErrorPayload {
  detail?: string;
}

function toApiError(error: unknown, operationErrorKey: UploadApiErrorKey): Error {
  if (axios.isAxiosError<ApiErrorPayload>(error)) {
    if (!error.response) {
      return new Error("upload_error_network");
    }

    if (error.response.status === 413) {
      return new Error("upload_error_file_too_large");
    }

    if (error.response.status >= 500) {
      return new Error("upload_error_service_unavailable");
    }

    return new Error(operationErrorKey);
  }

  if (error instanceof Error) {
    return new Error(operationErrorKey);
  }

  return new Error(operationErrorKey);
}

export async function uploadNanoZip(file: File): Promise<UploadNanoResponse> {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await httpClient.post<UploadNanoResponse>("/api/v1/upload/nano", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  } catch (error) {
    throw toApiError(error, "upload_error_upload_failed");
  }
}

export async function updateNanoMetadata(
  nanoId: string,
  payload: UpdateNanoMetadataRequest
): Promise<UpdateNanoMetadataResponse> {
  try {
    const response = await httpClient.post<UpdateNanoMetadataResponse>(
      `/api/v1/nanos/${nanoId}/metadata`,
      payload
    );
    return response.data;
  } catch (error) {
    throw toApiError(error, "upload_error_metadata_failed");
  }
}

export async function publishNano(nanoId: string): Promise<UpdateNanoStatusResponse> {
  try {
    const response = await httpClient.patch<UpdateNanoStatusResponse>(
      `/api/v1/nanos/${nanoId}/status`,
      { status: "published" }
    );
    return response.data;
  } catch (error) {
    throw toApiError(error, "upload_error_publish_failed");
  }
}
