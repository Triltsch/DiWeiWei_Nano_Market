import { useEffect, useId, useState } from "react";

import {
  AccountSettingsApiError,
  changeMyPassword,
  exportMyData,
  getMyProfile,
  requestMyAccountDeletion,
  updateMyProfile,
  type UserProfile,
  type UserDataExport,
} from "../../shared/api";
import { useLanguage, useTranslation } from "../../shared/i18n";
import { getPasswordStrength, meetsPasswordPolicy } from "../auth/passwordStrength";

interface ProfileFormState {
  firstName: string;
  lastName: string;
  bio: string;
  company: string;
  jobTitle: string;
  phone: string;
  preferredLanguage: "de" | "en";
}

interface PasswordFormState {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const EMPTY_PASSWORD_FORM: PasswordFormState = {
  currentPassword: "",
  newPassword: "",
  confirmPassword: "",
};

function isSupportedLanguage(value: string): value is "de" | "en" {
  return value === "de" || value === "en";
}

function toInputValue(value: string | null): string {
  return value ?? "";
}

function buildProfileFormState(profile: UserProfile): ProfileFormState {
  return {
    firstName: toInputValue(profile.firstName),
    lastName: toInputValue(profile.lastName),
    bio: toInputValue(profile.bio),
    company: toInputValue(profile.company),
    jobTitle: toInputValue(profile.jobTitle),
    phone: toInputValue(profile.phone),
    preferredLanguage: isSupportedLanguage(profile.preferredLanguage)
      ? profile.preferredLanguage
      : "de",
  };
}

function normalizeOptionalString(value: string): string | null {
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function formatDateTime(value: string | null, locale: string): string {
  if (!value) {
    return "";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

function getStatusLabel(
  status: UserProfile["status"],
  t: ReturnType<typeof useTranslation>["t"],
): string {
  if (status === "inactive") {
    return t("profile_status_inactive");
  }

  if (status === "suspended") {
    return t("profile_status_suspended");
  }

  return t("profile_status_active");
}

function getPasswordStrengthLabel(
  label: ReturnType<typeof getPasswordStrength>["label"],
  t: ReturnType<typeof useTranslation>["t"],
): string {
  if (label === "strong") {
    return t("account_password_strength_strong");
  }

  if (label === "medium") {
    return t("account_password_strength_medium");
  }

  return t("account_password_strength_weak");
}

function downloadUserDataExport(data: UserDataExport): void {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const objectUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  const stamp = (data.exportDate || new Date().toISOString()).replace(/[:.]/g, "-");

  link.href = objectUrl;
  link.download = `diweiwei-user-export-${stamp}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(objectUrl);
}

export function AccountSettingsPage(): JSX.Element {
  const { t, language } = useTranslation();
  const { setLanguage } = useLanguage();
  const locale = language === "de" ? "de-DE" : "en-US";
  const deletionReasonId = useId();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [profileForm, setProfileForm] = useState<ProfileFormState | null>(null);
  const [passwordForm, setPasswordForm] = useState<PasswordFormState>(EMPTY_PASSWORD_FORM);
  const [isLoading, setIsLoading] = useState(true);
  const [loadErrorCode, setLoadErrorCode] = useState<"forbidden" | "generic" | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileMessage, setProfileMessage] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [deletionError, setDeletionError] = useState<string | null>(null);
  const [deletionMessage, setDeletionMessage] = useState<string | null>(null);
  const [deletionReason, setDeletionReason] = useState("");
  const [deleteConfirmed, setDeleteConfirmed] = useState(false);
  const [isProfileSaving, setIsProfileSaving] = useState(false);
  const [isPasswordSaving, setIsPasswordSaving] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [isDeletionSubmitting, setIsDeletionSubmitting] = useState(false);

  useEffect(() => {
    let isActive = true;

    const loadProfile = async (): Promise<void> => {
      setIsLoading(true);
      setLoadErrorCode(null);

      try {
        const response = await getMyProfile();
        if (!isActive) {
          return;
        }

        setProfile(response);
        setProfileForm(buildProfileFormState(response));
        if (isSupportedLanguage(response.preferredLanguage)) {
          setLanguage(response.preferredLanguage);
        }
      } catch (error) {
        if (!isActive) {
          return;
        }

        if (error instanceof AccountSettingsApiError && error.code === "forbidden") {
          setLoadErrorCode("forbidden");
        } else {
          setLoadErrorCode("generic");
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    };

    void loadProfile();

    return () => {
      isActive = false;
    };
  }, [setLanguage]);

  const passwordStrength = getPasswordStrength(passwordForm.newPassword);
  const canRequestDeletion = profile?.deletionRequestedAt == null;

  const handleProfileFieldChange = <K extends keyof ProfileFormState>(
    field: K,
    value: ProfileFormState[K],
  ): void => {
    if (field === "preferredLanguage") {
      setLanguage(value as ProfileFormState["preferredLanguage"]);
    }

    setProfileForm((current) => (current ? { ...current, [field]: value } : current));
  };

  const handlePasswordFieldChange = <K extends keyof PasswordFormState>(
    field: K,
    value: PasswordFormState[K],
  ): void => {
    setPasswordForm((current) => ({ ...current, [field]: value }));
  };

  const handleProfileSubmit = async (): Promise<void> => {
    if (!profile || !profileForm) {
      return;
    }

    setProfileError(null);
    setProfileMessage(null);
    setIsProfileSaving(true);

    try {
      const updatedProfile = await updateMyProfile({
        firstName: normalizeOptionalString(profileForm.firstName),
        lastName: normalizeOptionalString(profileForm.lastName),
        bio: normalizeOptionalString(profileForm.bio),
        company: normalizeOptionalString(profileForm.company),
        jobTitle: normalizeOptionalString(profileForm.jobTitle),
        phone: normalizeOptionalString(profileForm.phone),
        preferredLanguage: profileForm.preferredLanguage,
      });

      setProfile(updatedProfile);
      setProfileForm(buildProfileFormState(updatedProfile));
      if (isSupportedLanguage(updatedProfile.preferredLanguage)) {
        setLanguage(updatedProfile.preferredLanguage);
      }
      setProfileMessage(t("profile_save_success"));
    } catch (error) {
      if (error instanceof AccountSettingsApiError) {
        if (error.code === "validation") {
          setProfileError(t("profile_save_validation_error"));
        } else if (error.code === "forbidden") {
          setProfileError(t("auth_error_forbidden"));
        } else {
          setProfileError(t("profile_save_error"));
        }
      } else {
        setProfileError(t("profile_save_error"));
      }
    } finally {
      setIsProfileSaving(false);
    }
  };

  const handlePasswordSubmit = async (): Promise<void> => {
    setPasswordError(null);
    setPasswordMessage(null);

    if (!passwordForm.currentPassword || !passwordForm.newPassword || !passwordForm.confirmPassword) {
      setPasswordError(t("account_password_required_error"));
      return;
    }

    if (!meetsPasswordPolicy(passwordForm.newPassword)) {
      setPasswordError(t("account_password_policy_error"));
      return;
    }

    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setPasswordError(t("account_password_mismatch_error"));
      return;
    }

    if (passwordForm.currentPassword === passwordForm.newPassword) {
      setPasswordError(t("account_password_same_error"));
      return;
    }

    setIsPasswordSaving(true);

    try {
      const message = await changeMyPassword({
        currentPassword: passwordForm.currentPassword,
        newPassword: passwordForm.newPassword,
      });
      setPasswordMessage(message || t("account_password_success"));
      setPasswordForm(EMPTY_PASSWORD_FORM);
    } catch (error) {
      if (error instanceof AccountSettingsApiError) {
        if (error.code === "current-password-incorrect") {
          setPasswordError(t("account_password_current_error"));
        } else if (error.code === "validation") {
          setPasswordError(t("account_password_policy_error"));
        } else if (error.code === "forbidden") {
          setPasswordError(t("auth_error_forbidden"));
        } else {
          setPasswordError(t("account_password_submit_error"));
        }
      } else {
        setPasswordError(t("account_password_submit_error"));
      }
    } finally {
      setIsPasswordSaving(false);
    }
  };

  const handleExport = async (): Promise<void> => {
    setExportError(null);
    setExportMessage(null);
    setIsExporting(true);

    try {
      const response = await exportMyData();
      downloadUserDataExport(response);
      setExportMessage(t("gdpr_export_success"));
    } catch (error) {
      if (error instanceof AccountSettingsApiError && error.code === "forbidden") {
        setExportError(t("auth_error_forbidden"));
      } else {
        setExportError(t("gdpr_export_error"));
      }
    } finally {
      setIsExporting(false);
    }
  };

  const handleDeletionRequest = async (): Promise<void> => {
    setDeletionError(null);
    setDeletionMessage(null);

    if (!deleteConfirmed) {
      setDeletionError(t("gdpr_delete_confirm_error"));
      return;
    }

    setIsDeletionSubmitting(true);

    try {
      const response = await requestMyAccountDeletion({
        confirm: true,
        reason: deletionReason.trim() || undefined,
      });

      setDeletionMessage(response.message);
      setProfile((current) =>
        current
          ? {
              ...current,
              status: "inactive",
              deletionRequestedAt: new Date().toISOString(),
              deletionScheduledAt: response.deletionScheduledAt,
            }
          : current,
      );
      setDeleteConfirmed(false);
      setDeletionReason("");
    } catch (error) {
      if (error instanceof AccountSettingsApiError) {
        if (error.code === "deletion-already-requested") {
          setDeletionError(t("gdpr_delete_already_requested"));
        } else if (error.code === "forbidden") {
          setDeletionError(t("auth_error_forbidden"));
        } else if (error.code === "validation") {
          setDeletionError(t("gdpr_delete_confirm_error"));
        } else {
          setDeletionError(t("gdpr_delete_error"));
        }
      } else {
        setDeletionError(t("gdpr_delete_error"));
      }
    } finally {
      setIsDeletionSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <section className="card-elevated py-10 text-center">
        <p className="text-neutral-600" role="status" aria-live="polite">
          {t("profile_loading")}
        </p>
      </section>
    );
  }

  if (loadErrorCode || !profile || !profileForm) {
    return (
      <section className="card-elevated space-y-3" role="alert">
        <h1 className="text-primary-600">{t("profile_title")}</h1>
        <p className="text-neutral-700">
          {loadErrorCode === "forbidden" ? t("auth_error_forbidden") : t("profile_load_error")}
        </p>
      </section>
    );
  }

  return (
    <div className="space-y-6">
      <section className="card-elevated space-y-4 overflow-hidden bg-gradient-to-br from-primary-50 via-white to-secondary-50">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="space-y-2">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary-600">
              {t("profile_badge")}
            </p>
            <h1 className="text-primary-700">{t("profile_title")}</h1>
            <p className="max-w-2xl text-neutral-700">{t("profile_intro")}</p>
          </div>
          <div className="rounded-xl border border-primary-100 bg-white/80 px-4 py-3 text-sm text-neutral-700 shadow-sm">
            <p className="font-semibold text-neutral-900">{profile.username}</p>
            <p>{profile.email}</p>
            <p>
              {t("profile_role_prefix")} {profile.role}
            </p>
          </div>
        </div>

        <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-xl border border-neutral-200 bg-white px-4 py-3 shadow-sm">
            <dt className="text-xs font-semibold uppercase tracking-wide text-neutral-500">
              {t("profile_status_label")}
            </dt>
            <dd className="mt-1 font-medium text-neutral-900">{getStatusLabel(profile.status, t)}</dd>
          </div>
          <div className="rounded-xl border border-neutral-200 bg-white px-4 py-3 shadow-sm">
            <dt className="text-xs font-semibold uppercase tracking-wide text-neutral-500">
              {t("profile_language_label")}
            </dt>
            <dd className="mt-1 font-medium text-neutral-900">{profileForm.preferredLanguage.toUpperCase()}</dd>
          </div>
          <div className="rounded-xl border border-neutral-200 bg-white px-4 py-3 shadow-sm">
            <dt className="text-xs font-semibold uppercase tracking-wide text-neutral-500">
              {t("profile_created_label")}
            </dt>
            <dd className="mt-1 font-medium text-neutral-900">{formatDateTime(profile.createdAt, locale)}</dd>
          </div>
          <div className="rounded-xl border border-neutral-200 bg-white px-4 py-3 shadow-sm">
            <dt className="text-xs font-semibold uppercase tracking-wide text-neutral-500">
              {t("profile_last_login_label")}
            </dt>
            <dd className="mt-1 font-medium text-neutral-900">
              {profile.lastLogin ? formatDateTime(profile.lastLogin, locale) : t("profile_last_login_empty")}
            </dd>
          </div>
        </dl>
      </section>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <section className="card-elevated space-y-5">
          <div className="space-y-1">
            <h2 className="text-2xl text-neutral-900">{t("profile_section_title")}</h2>
            <p className="text-neutral-600">{t("profile_section_description")}</p>
          </div>

          {profileMessage ? (
            <p className="rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
              {profileMessage}
            </p>
          ) : null}
          {profileError ? (
            <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
              {profileError}
            </p>
          ) : null}

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <label className="block space-y-1">
              <span className="text-sm font-medium text-neutral-800">{t("profile_username_label")}</span>
              <input
                type="text"
                value={profile.username}
                readOnly
                className="w-full rounded-md border border-neutral-300 bg-neutral-100 px-3 py-2 text-neutral-600"
              />
            </label>
            <label className="block space-y-1">
              <span className="text-sm font-medium text-neutral-800">{t("profile_email_label")}</span>
              <input
                type="email"
                value={profile.email}
                readOnly
                className="w-full rounded-md border border-neutral-300 bg-neutral-100 px-3 py-2 text-neutral-600"
              />
            </label>
            <label className="block space-y-1">
              <span className="text-sm font-medium text-neutral-800">{t("profile_first_name_label")}</span>
              <input
                type="text"
                value={profileForm.firstName}
                onChange={(event) => handleProfileFieldChange("firstName", event.target.value)}
                className="w-full rounded-md border border-neutral-300 px-3 py-2"
                maxLength={100}
              />
            </label>
            <label className="block space-y-1">
              <span className="text-sm font-medium text-neutral-800">{t("profile_last_name_label")}</span>
              <input
                type="text"
                value={profileForm.lastName}
                onChange={(event) => handleProfileFieldChange("lastName", event.target.value)}
                className="w-full rounded-md border border-neutral-300 px-3 py-2"
                maxLength={100}
              />
            </label>
            <label className="block space-y-1">
              <span className="text-sm font-medium text-neutral-800">{t("profile_company_label")}</span>
              <input
                type="text"
                value={profileForm.company}
                onChange={(event) => handleProfileFieldChange("company", event.target.value)}
                className="w-full rounded-md border border-neutral-300 px-3 py-2"
                maxLength={255}
              />
            </label>
            <label className="block space-y-1">
              <span className="text-sm font-medium text-neutral-800">{t("profile_job_title_label")}</span>
              <input
                type="text"
                value={profileForm.jobTitle}
                onChange={(event) => handleProfileFieldChange("jobTitle", event.target.value)}
                className="w-full rounded-md border border-neutral-300 px-3 py-2"
                maxLength={100}
              />
            </label>
            <label className="block space-y-1">
              <span className="text-sm font-medium text-neutral-800">{t("profile_phone_label")}</span>
              <input
                type="tel"
                value={profileForm.phone}
                onChange={(event) => handleProfileFieldChange("phone", event.target.value)}
                className="w-full rounded-md border border-neutral-300 px-3 py-2"
                maxLength={20}
              />
            </label>
            <label className="block space-y-1">
              <span className="text-sm font-medium text-neutral-800">{t("profile_language_label")}</span>
              <select
                value={profileForm.preferredLanguage}
                onChange={(event) =>
                  handleProfileFieldChange(
                    "preferredLanguage",
                    event.target.value as ProfileFormState["preferredLanguage"],
                  )
                }
                className="w-full rounded-md border border-neutral-300 px-3 py-2"
              >
                <option value="de">{t("language_option_de")}</option>
                <option value="en">{t("language_option_en")}</option>
              </select>
            </label>
          </div>

          <label className="block space-y-1">
            <span className="text-sm font-medium text-neutral-800">{t("profile_bio_label")}</span>
            <textarea
              value={profileForm.bio}
              onChange={(event) => handleProfileFieldChange("bio", event.target.value)}
              className="min-h-32 w-full rounded-md border border-neutral-300 px-3 py-2"
              maxLength={500}
            />
          </label>

          <div className="flex justify-end">
            <button
              type="button"
              className="btn-primary"
              onClick={() => void handleProfileSubmit()}
              disabled={isProfileSaving}
            >
              {isProfileSaving ? t("profile_save_pending") : t("profile_save_cta")}
            </button>
          </div>
        </section>

        <div className="space-y-6">
          <section className="card-elevated space-y-4">
            <div className="space-y-1">
              <h2 className="text-2xl text-neutral-900">{t("account_password_title")}</h2>
              <p className="text-neutral-600">{t("account_password_description")}</p>
            </div>

            {passwordMessage ? (
              <p className="rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
                {passwordMessage}
              </p>
            ) : null}
            {passwordError ? (
              <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
                {passwordError}
              </p>
            ) : null}

            <label className="block space-y-1">
              <span className="text-sm font-medium text-neutral-800">{t("account_password_current_label")}</span>
              <input
                type="password"
                value={passwordForm.currentPassword}
                onChange={(event) => handlePasswordFieldChange("currentPassword", event.target.value)}
                className="w-full rounded-md border border-neutral-300 px-3 py-2"
              />
            </label>
            <label className="block space-y-1">
              <span className="text-sm font-medium text-neutral-800">{t("account_password_new_label")}</span>
              <input
                type="password"
                value={passwordForm.newPassword}
                onChange={(event) => handlePasswordFieldChange("newPassword", event.target.value)}
                className="w-full rounded-md border border-neutral-300 px-3 py-2"
              />
            </label>

            <div className="space-y-2 rounded-lg border border-neutral-200 bg-neutral-50 px-4 py-3">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-medium text-neutral-800">{t("account_password_strength_label")}</span>
                <span className="text-sm font-semibold text-neutral-700">
                  {getPasswordStrengthLabel(passwordStrength.label, t)}
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-neutral-200">
                <div
                  className={`h-full rounded-full transition-all ${
                    passwordStrength.label === "strong"
                      ? "bg-green-500"
                      : passwordStrength.label === "medium"
                        ? "bg-amber-500"
                        : "bg-red-500"
                  }`}
                  style={{ width: `${passwordStrength.score}%` }}
                />
              </div>
              <ul className="space-y-1 text-sm text-neutral-600">
                <li>{t("register_requirement_min_length")}</li>
                <li>{t("register_requirement_uppercase")}</li>
                <li>{t("register_requirement_digit")}</li>
                <li>{t("register_requirement_special")}</li>
              </ul>
            </div>

            <label className="block space-y-1">
              <span className="text-sm font-medium text-neutral-800">{t("account_password_confirm_label")}</span>
              <input
                type="password"
                value={passwordForm.confirmPassword}
                onChange={(event) => handlePasswordFieldChange("confirmPassword", event.target.value)}
                className="w-full rounded-md border border-neutral-300 px-3 py-2"
              />
            </label>

            <div className="flex justify-end">
              <button
                type="button"
                className="btn-primary"
                onClick={() => void handlePasswordSubmit()}
                disabled={isPasswordSaving}
              >
                {isPasswordSaving ? t("account_password_pending") : t("account_password_cta")}
              </button>
            </div>
          </section>

          <section className="card-elevated space-y-4">
            <div className="space-y-1">
              <h2 className="text-2xl text-neutral-900">{t("gdpr_export_title")}</h2>
              <p className="text-neutral-600">{t("gdpr_export_description")}</p>
            </div>
            {exportMessage ? (
              <p className="rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
                {exportMessage}
              </p>
            ) : null}
            {exportError ? (
              <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
                {exportError}
              </p>
            ) : null}
            <button
              type="button"
              className="btn-outline w-full"
              onClick={() => void handleExport()}
              disabled={isExporting}
            >
              {isExporting ? t("gdpr_export_pending") : t("gdpr_export_cta")}
            </button>
          </section>

          <section className="card-elevated space-y-4 border-red-100 bg-red-50/40">
            <div className="space-y-1">
              <h2 className="text-2xl text-red-700">{t("gdpr_delete_title")}</h2>
              <p className="text-neutral-700">{t("gdpr_delete_description")}</p>
            </div>
            {profile.deletionScheduledAt ? (
              <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                {t("gdpr_delete_scheduled_prefix")} {formatDateTime(profile.deletionScheduledAt, locale)}
              </p>
            ) : null}
            {deletionMessage ? (
              <p className="rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
                {deletionMessage}
              </p>
            ) : null}
            {deletionError ? (
              <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
                {deletionError}
              </p>
            ) : null}

            <label className="block space-y-1" htmlFor={deletionReasonId}>
              <span className="text-sm font-medium text-neutral-800">{t("gdpr_delete_reason_label")}</span>
              <textarea
                id={deletionReasonId}
                value={deletionReason}
                onChange={(event) => setDeletionReason(event.target.value)}
                className="min-h-24 w-full rounded-md border border-neutral-300 px-3 py-2"
                maxLength={500}
                disabled={!canRequestDeletion}
              />
            </label>

            <label className="flex items-start gap-3 rounded-lg border border-red-100 bg-white px-3 py-3 text-sm text-neutral-700">
              <input
                type="checkbox"
                checked={deleteConfirmed}
                onChange={(event) => setDeleteConfirmed(event.target.checked)}
                className="mt-1"
                disabled={!canRequestDeletion}
              />
              <span>{t("gdpr_delete_confirm_label")}</span>
            </label>

            <button
              type="button"
              className="w-full rounded-lg bg-red-600 px-4 py-2 font-medium text-white transition-colors hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-red-300"
              onClick={() => void handleDeletionRequest()}
              disabled={!canRequestDeletion || isDeletionSubmitting}
            >
              {isDeletionSubmitting ? t("gdpr_delete_pending") : t("gdpr_delete_cta")}
            </button>
          </section>
        </div>
      </div>
    </div>
  );
}