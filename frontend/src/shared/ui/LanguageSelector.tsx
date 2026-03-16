import { type ChangeEvent, useCallback, useId } from "react";

import { useLanguage, useTranslation, type SupportedLanguage } from "../i18n";

/**
/**
 * LanguageSelector Component
 *
 * Provides language selection dropdown for multi-language support.
 * Supports German (de) and English (en), with the selected language
 * persisted via i18n context (localStorage key: diwei_ui_language).
 *
 * Each instance generates a unique ID via React's `useId` hook so that
 * multiple LanguageSelector instances (e.g. desktop + mobile nav) do
 * not produce duplicate DOM IDs.
 *
 * Accessibility:
 * - Uses semantic select element for screen readers
 * - Includes proper ARIA labels
 * - Keyboard navigable
 */
export function LanguageSelector(): JSX.Element {
  const { language, setLanguage } = useLanguage();
  const { t } = useTranslation();
  const selectorId = useId();

  const handleLanguageChange = useCallback((e: ChangeEvent<HTMLSelectElement>) => {
    setLanguage(e.target.value as SupportedLanguage);
  }, [setLanguage]);

  return (
    <div className="flex items-center gap-2">
      <label htmlFor={selectorId} className="text-sm font-medium text-neutral-700">
        {t("language_label")}
      </label>
      <select
        id={selectorId}
        value={language}
        onChange={handleLanguageChange}
        className="px-2 py-1 rounded-md border border-neutral-300 text-sm font-medium text-neutral-700 hover:border-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors"
        aria-label={t("language_select_aria")}
      >
        <option value="de">{t("language_option_de")}</option>
        <option value="en">{t("language_option_en")}</option>
      </select>
    </div>
  );
}
