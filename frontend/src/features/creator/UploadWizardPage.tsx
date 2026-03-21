import { useMemo, useRef, useState, type ChangeEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  updateNanoMetadata,
  uploadNanoZip,
  type UpdateNanoMetadataRequest,
} from "../../shared/api/upload";
import { submitNanoForReview } from "../../shared/api/creator";
import { useTranslation, type TranslationKey } from "../../shared/i18n";
import { GlobalNav } from "../../shared/ui/GlobalNav";

type WizardStep = 1 | 2 | 3;

interface MetadataFormState {
  title: string;
  description: string;
  durationMinutes: string;
  competencyLevel: "beginner" | "intermediate" | "advanced";
  language: string;
  format: "video" | "text" | "quiz" | "interactive" | "mixed";
  license: "CC-BY" | "CC-BY-SA" | "CC0" | "proprietary";
}

const INITIAL_METADATA: MetadataFormState = {
  title: "",
  description: "",
  durationMinutes: "",
  competencyLevel: "beginner",
  language: "de",
  format: "mixed",
  license: "proprietary",
};

const UPLOAD_ERROR_KEYS: TranslationKey[] = [
  "upload_error_upload_failed",
  "upload_error_metadata_failed",
  "upload_error_publish_failed",
  "upload_error_network",
  "upload_error_service_unavailable",
  "upload_error_file_too_large",
];

function isUploadErrorKey(value: string): value is TranslationKey {
  return UPLOAD_ERROR_KEYS.includes(value as TranslationKey);
}

export function UploadWizardPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [step, setStep] = useState<WizardStep>(1);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [nanoId, setNanoId] = useState<string | null>(null);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [metadata, setMetadata] = useState<MetadataFormState>(INITIAL_METADATA);

  const getTranslatedApiError = (error: unknown): string => {
    if (error instanceof Error && isUploadErrorKey(error.message)) {
      return t(error.message);
    }

    return t("error_unknown");
  };

  const canSubmitMetadata = useMemo(() => {
    return metadata.title.trim().length > 0;
  }, [metadata.title]);

  const stepClass = (current: WizardStep): string => {
    if (step === current) {
      return "bg-primary-600 text-white";
    }
    if (step > current) {
      // Use project token rather than default Tailwind green (which is overridden)
      return "bg-success-100 text-success-700";
    }
    return "bg-neutral-100 text-neutral-700";
  };

  const handleSelectFile = (event: ChangeEvent<HTMLInputElement>): void => {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    setError(null);
  };

  const handleOpenFilePicker = (): void => {
    fileInputRef.current?.click();
  };

  const handleUpload = async (): Promise<void> => {
    if (!selectedFile) {
      setError(t("upload_error_no_file"));
      return;
    }

    setIsBusy(true);
    setError(null);

    try {
      const response = await uploadNanoZip(selectedFile);
      setNanoId(response.nano_id);
      setUploadMessage(response.message);
      setStep(2);
    } catch (uploadError) {
      setError(getTranslatedApiError(uploadError));
    } finally {
      setIsBusy(false);
    }
  };

  const handleMetadataSubmit = async (): Promise<void> => {
    if (!nanoId) {
      setError(t("upload_error_missing_nano"));
      return;
    }

    if (!canSubmitMetadata) {
      setError(t("upload_error_title_required"));
      return;
    }

    const payload: UpdateNanoMetadataRequest = {
      title: metadata.title.trim(),
      description: metadata.description.trim() || undefined,
      duration_minutes: metadata.durationMinutes ? Number(metadata.durationMinutes) : undefined,
      competency_level: metadata.competencyLevel,
      language: metadata.language,
      format: metadata.format,
      license: metadata.license,
    };

    setIsBusy(true);
    setError(null);

    try {
      await updateNanoMetadata(nanoId, payload);
      setStep(3);
    } catch (metadataError) {
      setError(getTranslatedApiError(metadataError));
    } finally {
      setIsBusy(false);
    }
  };

  const handleSubmitForReview = async (): Promise<void> => {
    if (!nanoId) {
      setError(t("upload_error_missing_nano"));
      return;
    }

    setIsBusy(true);
    setError(null);

    try {
      await submitNanoForReview(nanoId);
      navigate("/dashboard");
    } catch (publishError) {
      setError(getTranslatedApiError(publishError));
    } finally {
      setIsBusy(false);
    }
  };

  return (
    <>
      <GlobalNav />
      <main className="container-main space-y-6 pb-8">
        <section className="card-elevated space-y-4">
          <h1 className="text-primary-600">{t("upload_wizard_title")}</h1>
          <p className="text-base text-neutral-600">{t("upload_wizard_description")}</p>

          <div className="flex flex-wrap gap-2" aria-label={t("upload_steps_aria")}>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${stepClass(1)}`}>
              {t("upload_step_zip")}
            </span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${stepClass(2)}`}>
              {t("upload_step_metadata")}
            </span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${stepClass(3)}`}>
              {t("upload_step_submit")}
            </span>
          </div>

          {error && <p className="text-error-700 bg-error-50 rounded-md p-3">{error}</p>}
          {uploadMessage && <p className="text-success-700 bg-success-50 rounded-md p-3">{uploadMessage}</p>}
        </section>

        {step === 1 && (
          <section className="card-elevated space-y-4">
            <label className="block space-y-2">
              <span className="font-medium text-neutral-800">{t("upload_file_label")}</span>
              <input
                ref={fileInputRef}
                type="file"
                accept=".zip,application/zip"
                onChange={handleSelectFile}
                className="sr-only"
              />
            </label>

            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <button type="button" className="btn-outline" onClick={handleOpenFilePicker}>
                  {t("upload_select_file")}
                </button>
                <span className="text-sm text-neutral-600">
                  {selectedFile ? selectedFile.name : t("upload_no_file_selected")}
                </span>
              </div>
              <button type="button" className="btn-primary" onClick={() => void handleUpload()} disabled={isBusy}>
                {isBusy ? t("upload_uploading") : t("upload_start")}
              </button>
            </div>
          </section>
        )}

        {step === 2 && (
          <section className="card-elevated space-y-4">
            <h2 className="text-lg font-semibold text-neutral-900">{t("upload_metadata_title")}</h2>

            <label className="block space-y-1">
              <span className="text-sm font-medium text-neutral-800">{t("upload_metadata_label_title")}</span>
              <input
                type="text"
                value={metadata.title}
                onChange={(event) => setMetadata((prev) => ({ ...prev, title: event.target.value }))}
                className="w-full rounded-md border border-neutral-300 px-3 py-2"
              />
            </label>

            <label className="block space-y-1">
              <span className="text-sm font-medium text-neutral-800">{t("upload_metadata_label_description")}</span>
              <textarea
                value={metadata.description}
                onChange={(event) =>
                  setMetadata((prev) => ({ ...prev, description: event.target.value }))
                }
                className="w-full rounded-md border border-neutral-300 px-3 py-2 min-h-24"
              />
            </label>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <label className="block space-y-1">
                <span className="text-sm font-medium text-neutral-800">{t("upload_metadata_label_duration")}</span>
                <input
                  type="number"
                  min={1}
                  value={metadata.durationMinutes}
                  onChange={(event) =>
                    setMetadata((prev) => ({ ...prev, durationMinutes: event.target.value }))
                  }
                  className="w-full rounded-md border border-neutral-300 px-3 py-2"
                />
              </label>

              <label className="block space-y-1">
                <span className="text-sm font-medium text-neutral-800">{t("upload_metadata_label_language")}</span>
                <input
                  type="text"
                  maxLength={2}
                  value={metadata.language}
                  onChange={(event) =>
                    setMetadata((prev) => ({ ...prev, language: event.target.value.toLowerCase() }))
                  }
                  className="w-full rounded-md border border-neutral-300 px-3 py-2"
                />
              </label>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <label className="block space-y-1">
                <span className="text-sm font-medium text-neutral-800">{t("upload_metadata_label_level")}</span>
                <select
                  value={metadata.competencyLevel}
                  onChange={(event) =>
                    setMetadata((prev) => ({
                      ...prev,
                      competencyLevel: event.target.value as MetadataFormState["competencyLevel"],
                    }))
                  }
                  className="w-full rounded-md border border-neutral-300 px-3 py-2"
                >
                  <option value="beginner">{t("search_level_beginner")}</option>
                  <option value="intermediate">{t("search_level_intermediate")}</option>
                  <option value="advanced">{t("search_level_advanced")}</option>
                </select>
              </label>

              <label className="block space-y-1">
                <span className="text-sm font-medium text-neutral-800">{t("upload_metadata_label_format")}</span>
                <select
                  value={metadata.format}
                  onChange={(event) =>
                    setMetadata((prev) => ({
                      ...prev,
                      format: event.target.value as MetadataFormState["format"],
                    }))
                  }
                  className="w-full rounded-md border border-neutral-300 px-3 py-2"
                >
                  <option value="mixed">mixed</option>
                  <option value="video">video</option>
                  <option value="text">text</option>
                  <option value="quiz">quiz</option>
                  <option value="interactive">interactive</option>
                </select>
              </label>

              <label className="block space-y-1">
                <span className="text-sm font-medium text-neutral-800">{t("upload_metadata_label_license")}</span>
                <select
                  value={metadata.license}
                  onChange={(event) =>
                    setMetadata((prev) => ({
                      ...prev,
                      license: event.target.value as MetadataFormState["license"],
                    }))
                  }
                  className="w-full rounded-md border border-neutral-300 px-3 py-2"
                >
                  <option value="proprietary">proprietary</option>
                  <option value="CC-BY">CC-BY</option>
                  <option value="CC-BY-SA">CC-BY-SA</option>
                  <option value="CC0">CC0</option>
                </select>
              </label>
            </div>

            <div className="flex justify-end">
              <button
                type="button"
                className="btn-primary"
                onClick={() => void handleMetadataSubmit()}
                disabled={isBusy || !canSubmitMetadata}
              >
                {isBusy ? t("upload_saving_metadata") : t("upload_save_metadata")}
              </button>
            </div>
          </section>
        )}

        {step === 3 && (
          <section className="card-elevated space-y-4">
            <h2 className="text-lg font-semibold text-neutral-900">{t("upload_submit_title")}</h2>
            <p className="text-neutral-600">{t("upload_submit_description")}</p>

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                className="btn-primary"
                onClick={() => void handleSubmitForReview()}
                disabled={isBusy}
              >
                {isBusy ? t("upload_submitting") : t("upload_submit_now")}
              </button>
              <Link to="/dashboard" className="btn-outline">
                {t("upload_back_dashboard")}
              </Link>
            </div>
          </section>
        )}
      </main>
    </>
  );
}
