import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  getCreatorNanoMetadata,
  updateCreatorNanoMetadata,
  type CreatorNanoMetadataResponse,
} from "../../shared/api/creator";
import type { UpdateNanoMetadataRequest } from "../../shared/api/upload";
import { useTranslation } from "../../shared/i18n";
import { GlobalNav } from "../../shared/ui/GlobalNav";

interface MetadataFormState {
  title: string;
  description: string;
  durationMinutes: string;
  competencyLevel: "beginner" | "intermediate" | "advanced";
  language: string;
  format: "video" | "text" | "quiz" | "interactive" | "mixed";
  license: "CC-BY" | "CC-BY-SA" | "CC0" | "proprietary";
}

function mapToForm(metadata: CreatorNanoMetadataResponse): MetadataFormState {
  return {
    title: metadata.title,
    description: metadata.description ?? "",
    durationMinutes: metadata.duration_minutes ? String(metadata.duration_minutes) : "",
    competencyLevel: metadata.competency_level,
    language: metadata.language,
    format: metadata.format,
    license: metadata.license,
  };
}

export function EditNanoPage(): JSX.Element {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const params = useParams<{ id: string }>();
  const nanoId = params.id ?? "";

  const [metadata, setMetadata] = useState<MetadataFormState | null>(null);
  const [nanoStatus, setNanoStatus] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSave = useMemo(() => {
    return Boolean(metadata?.title.trim());
  }, [metadata]);

  useEffect(() => {
    const loadNano = async (): Promise<void> => {
      if (!nanoId) {
        setError(t("creator_edit_load_error"));
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        const response = await getCreatorNanoMetadata(nanoId);
        setMetadata(mapToForm(response));
        setNanoStatus(response.status);
      } catch {
        setError(t("creator_edit_load_error"));
      } finally {
        setIsLoading(false);
      }
    };

    void loadNano();
  }, [nanoId, t]);

  const handleSave = async (): Promise<void> => {
    if (!metadata || !nanoId) {
      setError(t("creator_edit_load_error"));
      return;
    }

    if (!metadata.title.trim()) {
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

    try {
      setIsSaving(true);
      setError(null);
      await updateCreatorNanoMetadata(nanoId, payload);
      navigate("/dashboard");
    } catch {
      setError(t("creator_edit_save_error"));
    } finally {
      setIsSaving(false);
    }
  };

  const isDraft = nanoStatus === "draft";

  return (
    <>
      <GlobalNav />
      <main className="container-main space-y-6 pb-8">
        <section className="card-elevated space-y-3">
          <h1 className="text-primary-600">{t("creator_edit_title")}</h1>
          <p className="text-base text-neutral-600">{t("creator_edit_subtitle")}</p>
          {error && <p className="text-red-700 bg-red-50 rounded-md p-3">{error}</p>}
          {!isLoading && !isDraft && (
            <p className="text-amber-800 bg-amber-50 rounded-md p-3">{t("creator_edit_draft_only")}</p>
          )}
        </section>

        {isLoading || !metadata ? (
          <section className="card-elevated text-center py-10">
            <p className="text-neutral-600">{t("loading")}</p>
          </section>
        ) : (
          <section className="card-elevated space-y-4">
            <label className="block space-y-1">
              <span className="text-sm font-medium text-neutral-800">{t("upload_metadata_label_title")}</span>
              <input
                type="text"
                value={metadata.title}
                onChange={(event) => setMetadata((prev) => (prev ? { ...prev, title: event.target.value } : prev))}
                className="w-full rounded-md border border-neutral-300 px-3 py-2"
                disabled={!isDraft || isSaving}
              />
            </label>

            <label className="block space-y-1">
              <span className="text-sm font-medium text-neutral-800">{t("upload_metadata_label_description")}</span>
              <textarea
                value={metadata.description}
                onChange={(event) =>
                  setMetadata((prev) => (prev ? { ...prev, description: event.target.value } : prev))
                }
                className="w-full rounded-md border border-neutral-300 px-3 py-2 min-h-24"
                disabled={!isDraft || isSaving}
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
                    setMetadata((prev) =>
                      prev ? { ...prev, durationMinutes: event.target.value } : prev
                    )
                  }
                  className="w-full rounded-md border border-neutral-300 px-3 py-2"
                  disabled={!isDraft || isSaving}
                />
              </label>

              <label className="block space-y-1">
                <span className="text-sm font-medium text-neutral-800">{t("upload_metadata_label_language")}</span>
                <input
                  type="text"
                  maxLength={2}
                  value={metadata.language}
                  onChange={(event) =>
                    setMetadata((prev) =>
                      prev ? { ...prev, language: event.target.value.toLowerCase() } : prev
                    )
                  }
                  className="w-full rounded-md border border-neutral-300 px-3 py-2"
                  disabled={!isDraft || isSaving}
                />
              </label>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <label className="block space-y-1">
                <span className="text-sm font-medium text-neutral-800">{t("upload_metadata_label_level")}</span>
                <select
                  value={metadata.competencyLevel}
                  onChange={(event) =>
                    setMetadata((prev) =>
                      prev
                        ? {
                            ...prev,
                            competencyLevel: event.target.value as MetadataFormState["competencyLevel"],
                          }
                        : prev
                    )
                  }
                  className="w-full rounded-md border border-neutral-300 px-3 py-2"
                  disabled={!isDraft || isSaving}
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
                    setMetadata((prev) =>
                      prev
                        ? {
                            ...prev,
                            format: event.target.value as MetadataFormState["format"],
                          }
                        : prev
                    )
                  }
                  className="w-full rounded-md border border-neutral-300 px-3 py-2"
                  disabled={!isDraft || isSaving}
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
                    setMetadata((prev) =>
                      prev
                        ? {
                            ...prev,
                            license: event.target.value as MetadataFormState["license"],
                          }
                        : prev
                    )
                  }
                  className="w-full rounded-md border border-neutral-300 px-3 py-2"
                  disabled={!isDraft || isSaving}
                >
                  <option value="proprietary">proprietary</option>
                  <option value="CC-BY">CC-BY</option>
                  <option value="CC-BY-SA">CC-BY-SA</option>
                  <option value="CC0">CC0</option>
                </select>
              </label>
            </div>

            <div className="flex justify-end gap-2">
              <Link to="/dashboard" className="btn-outline">
                {t("creator_edit_cancel")}
              </Link>
              <button
                type="button"
                className="btn-primary"
                onClick={() => void handleSave()}
                disabled={!isDraft || isSaving || !canSave}
              >
                {isSaving ? t("creator_edit_saving") : t("creator_edit_save")}
              </button>
            </div>
          </section>
        )}
      </main>
    </>
  );
}
