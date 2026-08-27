import { useEffect, useState } from "react";

import {
  createNanoFlag,
  getMyNanoFlag,
  NanoFlagApiError,
  type NanoFlagReason,
} from "../../../shared/api/nanoFlags";
import { useTranslation } from "../../../shared/i18n";
import { ReportNanoModal } from "./ReportNanoModal";

interface ReportNanoControlProps {
  nanoId: string;
  creatorId: string;
  isPublished: boolean;
  isAuthenticated: boolean;
  currentUserId: string | undefined;
  onRequireLogin: () => void;
}

type ToastTone = "success" | "error";

export function ReportNanoControl({
  nanoId,
  creatorId,
  isPublished,
  isAuthenticated,
  currentUserId,
  onRequireLogin,
}: ReportNanoControlProps): JSX.Element | null {
  const { t } = useTranslation();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [hasReported, setHasReported] = useState(false);
  const [toast, setToast] = useState<{ message: string; tone: ToastTone } | null>(null);

  const isOwnNano = Boolean(currentUserId) && currentUserId === creatorId;

  useEffect(() => {
    let isActive = true;

    const loadMyFlag = async (): Promise<void> => {
      if (!isPublished || !isAuthenticated || isOwnNano || !nanoId) {
        if (isActive) {
          setHasReported(false);
        }
        return;
      }

      try {
        const existing = await getMyNanoFlag(nanoId);
        if (!isActive) {
          return;
        }
        setHasReported(existing != null);
      } catch (error) {
        if (!isActive) {
          return;
        }
        if (error instanceof NanoFlagApiError && error.code === "unauthorized") {
          onRequireLogin();
        }
      }
    };

    void loadMyFlag();

    return () => {
      isActive = false;
    };
  }, [creatorId, isAuthenticated, isOwnNano, isPublished, nanoId, onRequireLogin]);

  if (!isPublished || isOwnNano) {
    return null;
  }

  const handleOpen = (): void => {
    if (!isAuthenticated) {
      onRequireLogin();
      return;
    }
    if (hasReported) {
      return;
    }
    setIsModalOpen(true);
  };

  const handleSubmit = async (payload: { reason: NanoFlagReason; comment: string }): Promise<void> => {
    setIsSubmitting(true);

    try {
      await createNanoFlag(nanoId, payload);
      setHasReported(true);
      setIsModalOpen(false);
      setToast({ message: t("nano_report_success"), tone: "success" });
    } catch (error) {
      if (error instanceof NanoFlagApiError) {
        if (error.code === "unauthorized") {
          onRequireLogin();
          return;
        }
        if (error.code === "conflict") {
          setHasReported(true);
          setIsModalOpen(false);
          setToast({ message: t("nano_report_success"), tone: "success" });
          return;
        }
      }

      setToast({ message: t("nano_report_error"), tone: "error" });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <article className="card-elevated space-y-3">
        <h2 className="text-lg font-semibold text-neutral-900">{t("nano_report_section_title")}</h2>
        <p className="text-sm text-neutral-700">{t("nano_report_section_description")}</p>
        <button
          type="button"
          className="btn-outline inline-flex disabled:cursor-not-allowed disabled:opacity-60"
          onClick={handleOpen}
          disabled={hasReported}
          title={hasReported ? t("nano_report_already_tooltip") : undefined}
        >
          {hasReported ? t("nano_report_already") : t("nano_report_button")}
        </button>
      </article>

      <ReportNanoModal
        isOpen={isModalOpen}
        isSubmitting={isSubmitting}
        onClose={() => setIsModalOpen(false)}
        onSubmit={(payload) => {
          void handleSubmit(payload);
        }}
      />

      {toast && (
        <div
          role="status"
          className={`fixed bottom-4 right-4 z-[60] max-w-sm rounded-lg px-4 py-3 text-sm shadow-lg ${
            toast.tone === "success"
              ? "bg-success-700 text-white"
              : "bg-error-600 text-white"
          }`}
        >
          {toast.message}
        </div>
      )}
    </div>
  );
}
