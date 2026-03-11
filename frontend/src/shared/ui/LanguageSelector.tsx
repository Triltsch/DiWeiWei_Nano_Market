import { useCallback, useState } from "react";

/**
 * LanguageSelector Component
 *
 * Provides language selection dropdown for multi-language support.
 * Currently supports German (de) as default with placeholder for future languages.
 *
 * Accessibility:
 * - Uses semantic select element for screen readers
 * - Includes proper ARIA labels
 * - Keyboard navigable
 */
export function LanguageSelector(): JSX.Element {
  const [language, setLanguage] = useState<string>("de");

  const handleLanguageChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setLanguage(e.target.value);
    // TODO: Implement language switching logic (i18n integration)
    // This is a placeholder for Story 8.X (future multi-language support)
  }, []);

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="language-selector" className="text-sm font-medium text-neutral-700">
        Sprache:
      </label>
      <select
        id="language-selector"
        value={language}
        onChange={handleLanguageChange}
        className="px-2 py-1 rounded-md border border-neutral-300 text-sm font-medium text-neutral-700 hover:border-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500 transition-colors"
        aria-label="Select language / Sprache wählen"
      >
        <option value="de">Deutsch (de)</option>
        {/* Placeholder for future languages */}
        {/* <option value="en">English (en)</option> */}
      </select>
    </div>
  );
}
