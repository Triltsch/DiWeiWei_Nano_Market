import { useEffect, useId, useRef, useState, type FormEvent } from "react";

import {
  NANO_FLAG_COMMENT_MAX_LENGTH,
  NANO_FLAG_REASONS,
  type NanoFlagReason,
} from "../../../shared/api/nanoFlags";
import { useTranslation, type TranslationKey } from "../../../shared/i18n";

const REASON_LABEL_KEYS: Record<NanoFlagReason, TranslationKey> = {
  spam: "nano_report_reason_spam",
  copyright: "nano_report_reason_copyright",
  offensive: "nano_report_reason_offensive",
  misinformation: "nano_report_reason_misinformation",
  other: "nano_report_reason_other",
};

interface ReportNanoModalProps {
  isOpen: boolean;
  isSubmitting: boolean;
  onClose: () => void;
  onSubmit: (payload: { reason: NanoFlagReason; comment: string }) => void;
}

export function ReportNanoModal({
  isOpen,
  isSubmitting,
  onClose,
  onSubmit,
}: ReportNanoModalProps): JSX.Element | null {
  const { t } = useTranslation();
  const titleId = useId();
  const reasonId = useId();
  const commentId = useId();
  const counterId = useId();
  const reasonRef = useRef<HTMLSelectElement>(null);
  const [reason, setReason] = useState<NanoFlagReason | "">("");
  const [comment, setComment] = useState("");

  useEffect(() => {
    if (!isOpen) {
      setReason("");
      setComment("");
      return;
    }

    reasonRef.current?.focus();
  }, [isOpen]);

  if (!isOpen) {
    return null;
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (!reason || isSubmitting) {
      return;
    }
    onSubmit({ reason, comment });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/50 p-4 sm:items-center">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg bg-white p-6 shadow-lg"
      >
        <form className="space-y-4" onSubmit={handleSubmit}>
          <h2 id={titleId} className="text-lg font-semibold text-neutral-900">
            {t("nano_report_modal_title")}
          </h2>

          <label className="block space-y-2" htmlFor={reasonId}>
            <span className="text-sm font-medium text-neutral-800">{t("nano_report_reason_label")}</span>
            <select
              id={reasonId}
              ref={reasonRef}
              className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
              value={reason}
              onChange={(event) => setReason(event.target.value as NanoFlagReason | "")}
              disabled={isSubmitting}
              required
            >
              <option value="">{t("nano_report_reason_placeholder")}</option>
              {NANO_FLAG_REASONS.map((flagReason) => (
                <option key={flagReason} value={flagReason}>
                  {t(REASON_LABEL_KEYS[flagReason])}
                </option>
              ))}
            </select>
          </label>

          <div className="space-y-2">
            <label className="block space-y-2" htmlFor={commentId}>
              <span className="text-sm font-medium text-neutral-800">{t("nano_report_comment_label")}</span>
              <textarea
                id={commentId}
                className="min-h-28 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
                value={comment}
                maxLength={NANO_FLAG_COMMENT_MAX_LENGTH}
                onChange={(event) => setComment(event.target.value)}
                disabled={isSubmitting}
                aria-describedby={counterId}
              />
            </label>
            <span id={counterId} className="block text-right text-xs text-neutral-500">
              {`${comment.length}/${NANO_FLAG_COMMENT_MAX_LENGTH}`}
            </span>
          </div>

          <div className="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end">
            <button
              type="button"
              className="rounded-lg bg-neutral-100 px-4 py-2 font-medium text-neutral-700 transition-colors hover:bg-neutral-200 disabled:opacity-50"
              onClick={onClose}
              disabled={isSubmitting}
            >
              {t("cancel")}
            </button>
            <button
              type="submit"
              className="rounded-lg bg-primary-600 px-4 py-2 font-medium text-white transition-colors hover:bg-primary-700 disabled:opacity-50"
              disabled={isSubmitting || reason === ""}
            >
              {isSubmitting ? t("nano_report_submitting") : t("nano_report_submit")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
