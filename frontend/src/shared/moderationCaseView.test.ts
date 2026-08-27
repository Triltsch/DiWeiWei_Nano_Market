import { describe, expect, it } from "vitest";

import type { ModerationCaseItem } from "./api/admin";
import {
  getContentTypeLabel,
  getFlagCaseFields,
  getModerationActorPrefix,
  getModerationMeta,
  getModerationNanoId,
  getModerationSummary,
} from "./moderationCaseView";

const t = (key: string): string => key;

const flagItem: ModerationCaseItem = {
  caseId: "case-flag",
  contentType: "flag",
  contentId: "flag-1",
  reporterId: "user-1",
  status: "pending",
  reason: null,
  decidedByUserId: null,
  decidedAt: null,
  deferredUntil: null,
  escalationNote: null,
  createdAt: "2026-08-27T14:02:00Z",
  updatedAt: "2026-08-27T14:02:00Z",
  contentDetail: {
    nanoId: "nano-42",
    nanoTitle: "React Basics",
    reason: "spam",
    comment: "Looks like ads.",
    flagStatus: "pending",
    flaggedByUsername: "flag_reporter",
    createdAt: "2026-08-27T14:02:00Z",
  },
};

describe("moderationCaseView flag cases", () => {
  it("labels flags as reports and shows reporter, nano and reason", () => {
    expect(getContentTypeLabel("flag", t)).toBe("admin_moderation_content_type_flag");
    expect(getModerationSummary(flagItem, t)).toBe("React Basics");
    expect(getModerationMeta(flagItem, t)).toBe("flag_reporter");
    expect(getModerationActorPrefix(flagItem, t)).toBe("admin_moderation_reporter_prefix");
    expect(getModerationNanoId(flagItem)).toBe("nano-42");
    expect(getFlagCaseFields(flagItem, t)).toEqual({
      nanoId: "nano-42",
      nanoTitle: "React Basics",
      reporter: "flag_reporter",
      reasonLabel: "nano_report_reason_spam",
      comment: "Looks like ads.",
    });
  });
});
