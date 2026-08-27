import type { TranslationKey } from "./i18n";
import type {
  FlagContentDetail,
  ModerationCaseItem,
  ModerationContentDetail,
  ModerationContentType,
} from "./api/admin";

const FLAG_REASON_KEYS: Record<string, TranslationKey> = {
  spam: "nano_report_reason_spam",
  copyright: "nano_report_reason_copyright",
  offensive: "nano_report_reason_offensive",
  misinformation: "nano_report_reason_misinformation",
  other: "nano_report_reason_other",
};

type Translate = (key: TranslationKey) => string;

export function isFlagContentDetail(detail: ModerationContentDetail): detail is FlagContentDetail {
  return "flaggedByUsername" in detail && "reason" in detail && "nanoId" in detail;
}

export function getContentTypeLabel(value: ModerationContentType, t: Translate): string {
  if (value === "nano_rating") {
    return t("admin_moderation_content_type_rating");
  }
  if (value === "nano_comment") {
    return t("admin_moderation_content_type_comment");
  }
  if (value === "flag") {
    return t("admin_moderation_content_type_flag");
  }
  return t("admin_moderation_content_type_nano");
}

export function getModerationNanoId(item: ModerationCaseItem): string | null {
  if (item.contentType === "nano") {
    return item.contentId;
  }
  if (item.contentDetail && "nanoId" in item.contentDetail) {
    return item.contentDetail.nanoId;
  }
  return null;
}

export function getModerationSummary(item: ModerationCaseItem, t: Translate): string {
  if (!item.contentDetail) {
    return t("admin_moderation_missing_content");
  }

  if (item.contentType === "nano") {
    return item.contentDetail.title;
  }

  if (item.contentType === "nano_rating") {
    return item.contentDetail.score + "/5";
  }

  if (item.contentType === "flag" && isFlagContentDetail(item.contentDetail)) {
    return item.contentDetail.nanoTitle ?? item.contentDetail.nanoId;
  }

  if (item.contentType === "nano_comment") {
    return item.contentDetail.content;
  }

  return t("admin_moderation_missing_content");
}

export function getModerationMeta(item: ModerationCaseItem, t: Translate): string {
  if (!item.contentDetail) {
    return t("admin_moderation_missing_content");
  }

  if (item.contentType === "nano") {
    return item.contentDetail.creatorUsername ?? t("search_creator_fallback");
  }

  if (item.contentType === "flag" && isFlagContentDetail(item.contentDetail)) {
    return item.contentDetail.flaggedByUsername ?? t("search_creator_fallback");
  }

  if ("authorUsername" in item.contentDetail) {
    return item.contentDetail.authorUsername ?? t("search_creator_fallback");
  }

  return t("search_creator_fallback");
}

export function getFlagReasonLabel(reason: string, t: Translate): string {
  const key = FLAG_REASON_KEYS[reason.toLowerCase()];
  return key ? t(key) : reason.toUpperCase();
}

export function getModerationActorPrefix(item: ModerationCaseItem, t: Translate): string {
  if (item.contentType === "flag") {
    return t("admin_moderation_reporter_prefix");
  }
  return t("admin_moderation_author_prefix");
}

export function getFlagCaseFields(
  item: ModerationCaseItem,
  t: Translate,
): {
  nanoId: string;
  nanoTitle: string | null;
  reporter: string;
  reasonLabel: string;
  comment: string | null;
} | null {
  if (item.contentType !== "flag" || !item.contentDetail || !isFlagContentDetail(item.contentDetail)) {
    return null;
  }

  return {
    nanoId: item.contentDetail.nanoId,
    nanoTitle: item.contentDetail.nanoTitle,
    reporter: item.contentDetail.flaggedByUsername ?? t("search_creator_fallback"),
    reasonLabel: getFlagReasonLabel(item.contentDetail.reason, t),
    comment: item.contentDetail.comment,
  };
}
