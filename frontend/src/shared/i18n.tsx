import { createContext, useCallback, useContext, useMemo, useState, type PropsWithChildren } from "react";

export type SupportedLanguage = "de" | "en";

const LANGUAGE_STORAGE_KEY = "diwei_ui_language";

const de = {
  logo_src: "/logo.png",
  logo_alt: "DiWeiWei Nano Market Logo",
  nav_fallback_account: "Konto",
  nav_aria_global: "Globale Navigation",
  nav_home_aria: "DiWeiWei Nano Market Home",
  nav_search: "Suche",
  nav_dashboard: "Übersicht",
  nav_profile: "Profil",
  nav_login: "Anmelden",
  nav_register: "Registrieren",
  nav_logout: "Abmelden",
  nav_menu_open: "Menü öffnen",
  nav_menu_close: "Menü schließen",
  nav_mobile_region: "Mobile Navigation",
  language_label: "Sprache:",
  language_select_aria: "Sprache auswählen",
  language_option_de: "Deutsch (de)",
  language_option_en: "Englisch (en)",

  search_title: "Nano-Lerneinheiten suchen",
  search_description:
    "Entdecken Sie veröffentlichte Nano-Lerneinheiten mit Suchbegriff und Filtern.",
  search_keyword_label: "Suchbegriff",
  search_keyword_placeholder: "Nach Titel oder Ersteller suchen",
  search_filters_aria: "Suchfilter",
  search_filters_title: "Filter",
  search_category_label: "Kategorie",
  search_category_placeholder: "z. B. Frontend",
  search_level_label: "Niveau",
  search_level_all: "Alle Niveaus",
  search_level_beginner: "Anfänger",
  search_level_intermediate: "Fortgeschritten",
  search_level_advanced: "Experte",
  search_duration_label: "Dauer",
  search_duration_all: "Beliebige Dauer",
  search_language_label: "Sprache",
  search_language_all: "Alle Sprachen",
  search_results_aria: "Suchergebnisse",
  search_loading_aria: "Ladeskelett",
  search_empty: "Keine Nano-Lerneinheiten gefunden. Bitte versuchen Sie andere Suchbegriffe.",
  search_creator_label: "Ersteller:",
  search_avg_rating_label: "Durchschnittsbewertung:",
  search_duration_result_label: "Dauer:",
  search_not_available: "k. A.",
  search_duration_0_15: "0–15 min",
  search_duration_15_30: "15–30 min",
  search_duration_30_plus: "30+ min",
  search_error: "Suche fehlgeschlagen. Bitte versuchen Sie es erneut.",
  search_title_fallback: "Ohne Titel",
  search_creator_fallback: "Unbekannt",
  search_load_more: "Mehr laden",
  search_loading_more: "Lädt...",

  login_title: "Anmeldung",
  login_subtitle: "Willkommen zurück. Bitte melden Sie sich an.",
  login_email_label: "E-Mail",
  login_password_label: "Passwort",
  login_email_required: "E-Mail ist erforderlich",
  login_email_invalid: "Bitte eine gültige E-Mail-Adresse eingeben",
  login_password_required: "Passwort ist erforderlich",
  auth_show_password: "Anzeigen",
  auth_hide_password: "Ausblenden",
  login_remember_email: "E-Mail merken",
  login_submitting: "Melde an...",
  login_submit: "Anmelden",
  login_error_default: "Anmeldung fehlgeschlagen.",
  login_forgot_password: "Passwort vergessen? (Demnächst verfügbar)",
  login_no_account: "Noch kein Konto?",
  login_create_account_link: "Konto erstellen",

  register_title: "Registrierung",
  register_subtitle: "Erstellen Sie Ihr Konto für den DiWeiWei Nano Market.",
  register_email_label: "E-Mail",
  register_username_label: "Benutzername",
  register_password_label: "Passwort",
  register_confirm_password_label: "Passwort bestätigen",
  register_email_required: "E-Mail ist erforderlich",
  register_email_invalid: "Bitte eine gültige E-Mail-Adresse eingeben",
  register_username_required: "Benutzername ist erforderlich",
  register_username_min: "Benutzername muss mindestens 3 Zeichen haben",
  register_username_max: "Benutzername darf höchstens 20 Zeichen haben",
  register_username_pattern: "Nur Buchstaben, Zahlen und Unterstriche sind erlaubt",
  register_password_required: "Passwort ist erforderlich",
  register_password_policy: "Passwort erfüllt die Richtlinie nicht",
  register_confirm_required: "Bitte Passwort bestätigen",
  register_confirm_mismatch: "Passwörter stimmen nicht überein",
  register_strength_weak: "schwach",
  register_strength_medium: "mittel",
  register_strength_strong: "stark",
  register_password_strength: "Stärke:",
  register_requirements_title: "Passwortanforderungen",
  register_requirement_min_length: "Mindestens 8 Zeichen",
  register_requirement_uppercase: "Mindestens 1 Großbuchstabe",
  register_requirement_digit: "Mindestens 1 Ziffer",
  register_requirement_special: "Mindestens 1 Sonderzeichen",
  register_accept_terms_prefix: "Ich akzeptiere die",
  register_accept_terms_link: "Nutzungsbedingungen",
  register_accept_privacy_prefix: "Ich akzeptiere die",
  register_accept_privacy_link: "Datenschutzerklärung",
  register_accept_terms_required: "Sie müssen die Nutzungsbedingungen akzeptieren",
  register_accept_privacy_required: "Sie müssen die Datenschutzerklärung akzeptieren",
  register_submit: "Konto erstellen",
  register_submitting: "Konto wird erstellt...",
  register_error_default: "Registrierung fehlgeschlagen.",
  register_error_connection: "Verbindungsfehler. Bitte versuchen Sie es erneut.",
  register_error_request_failed: "Anfrage fehlgeschlagen. Bitte versuchen Sie es erneut.",
  register_error_email_exists: "Diese E-Mail-Adresse ist bereits registriert.",
  register_error_username_exists: "Dieser Benutzername ist bereits vergeben.",
  register_error_terms: "Sie müssen die Nutzungsbedingungen akzeptieren, um sich zu registrieren.",
  register_error_privacy: "Sie müssen die Datenschutzerklärung akzeptieren, um sich zu registrieren.",
  register_error_password_length: "Das Passwort muss mindestens 8 Zeichen lang sein.",
  register_error_password_uppercase: "Das Passwort muss mindestens einen Großbuchstaben enthalten.",
  register_error_password_digit: "Das Passwort muss mindestens eine Ziffer enthalten.",
  register_error_password_special: "Das Passwort muss mindestens ein Sonderzeichen enthalten.",
  register_error_service_unavailable: "Der Dienst ist momentan nicht verfügbar. Bitte versuchen Sie es später erneut.",
  register_has_account: "Bereits ein Konto?",
  register_go_login: "Zur Anmeldung",

  verify_title: "E-Mail verifizieren",
  verify_subtitle: "Bitte prüfen Sie Ihre E-Mails auf den Verifizierungslink.",
  verify_registered_email: "Registrierte E-Mail:",
  verify_email_not_provided: "(nicht angegeben)",
  verify_success_redirect: "E-Mail verifiziert! Weiterleitung zur Anmeldung...",
  verify_error_invalid: "Link ist abgelaufen oder ungültig. Bitte neue E-Mail anfordern.",
  verify_resend_success: "Verifizierungs-E-Mail wurde erneut gesendet.",
  verify_resend_failed: "Erneutes Senden der Verifizierungs-E-Mail fehlgeschlagen.",
  verify_resend_button: "Verifizierungs-E-Mail erneut senden",
  verify_resend_button_cooldown: "Verifizierungs-E-Mail erneut senden ({seconds}s)",
  verify_register_again:
    "Bitte erneut registrieren, um eine E-Mail-Adresse für den erneuten Versand anzugeben.",
  verify_already_verified: "Bereits verifiziert?",
  verify_go_login: "Zur Anmeldung",

  nano_details_title: "Nano-Details",
  nano_details_description: "Platzhalter für Detailroute. Aktuelle Nano-ID: {id}",
  dashboard_title: "Übersicht",
  dashboard_description: "Geschützte Übersichts-Route (Platzhalter).",
  profile_title: "Profil",
  profile_description: "Geschützte Profil-Route (Platzhalter).",
  admin_title: "Admin",
  admin_description: "Geschützte Admin-Route (Platzhalter).",
  not_found_title: "Seite nicht gefunden",
  not_found_description:
    "Die angeforderte Route existiert nicht. Verwenden Sie die Navigation, um zu bekannten Seiten zurückzukehren.",
  not_found_back_home: "Zur Startseite",

  home_title: "DiWeiWei Nano Market",
  home_hero_description:
    "Der Marktplatz für Nano-Lerneinheiten. Hochwertige Schulungsinhalte austauschen, entdecken und weiterentwickeln – alles in einem Ökosystem für lebenslanges Lernen.",
  home_cta_register: "Jetzt Registrieren",
  home_cta_discover: "Lerneinheiten Entdecken",
  home_features_title: "Warum DiWeiWei?",
  home_feature_quality_title: "Hochwertige Inhalte",
  home_feature_quality_description:
    "Kurierte Nano-Lerneinheiten von Experten für schnelles, gezieltes Lernen.",
  home_feature_share_title: "Einfach Teilbar",
  home_feature_share_description:
    "Inhalte schnell hochladen, verwalten und mit der Community teilen.",
  home_feature_fast_title: "Schneller Zugriff",
  home_feature_fast_description:
    "Mobil-optimiert und blitzschnell. Lernen Sie jederzeit und überall.",
  home_creator_title: "Sie sind Inhalts-Creator oder Trainer?",
  home_creator_description:
    "Teilen Sie Ihre Expertise als Nano-Lerneinheiten und erreichen Sie ein globales Publikum.",
  home_creator_cta: "Als Creator Beitreten",
  home_footer_terms: "Nutzungsbedingungen",
  home_footer_privacy: "Datenschutz",
  home_footer_copy: "© 2026 DiWeiWei Nano Market. Alle Rechte vorbehalten. | Sprint 3 Launch",
} as const;

export type TranslationKey = keyof typeof de;

const en: Record<TranslationKey, string> = {
  logo_src: "/logo_en.png",
  logo_alt: "DiWeiWei Nano Market Logo",
  nav_fallback_account: "Account",
  nav_aria_global: "Global navigation",
  nav_home_aria: "DiWeiWei Nano Market Home",
  nav_search: "Search",
  nav_dashboard: "Dashboard",
  nav_profile: "Profile",
  nav_login: "Login",
  nav_register: "Register",
  nav_logout: "Logout",
  nav_menu_open: "Open menu",
  nav_menu_close: "Close menu",
  nav_mobile_region: "Mobile navigation",
  language_label: "Language:",
  language_select_aria: "Select language",
  language_option_de: "German (de)",
  language_option_en: "English (en)",

  search_title: "Search Nano Learning Units",
  search_description: "Discover published nano learning units using keyword search and filters.",
  search_keyword_label: "Keyword",
  search_keyword_placeholder: "Search by title or creator",
  search_filters_aria: "Search filters",
  search_filters_title: "Filters",
  search_category_label: "Category",
  search_category_placeholder: "e.g. frontend",
  search_level_label: "Level",
  search_level_all: "All levels",
  search_level_beginner: "Beginner",
  search_level_intermediate: "Intermediate",
  search_level_advanced: "Advanced",
  search_duration_label: "Duration",
  search_duration_all: "Any duration",
  search_language_label: "Language",
  search_language_all: "All languages",
  search_results_aria: "Search results",
  search_loading_aria: "Loading skeleton",
  search_empty: "No nanos found. Please try different keywords.",
  search_creator_label: "Creator:",
  search_avg_rating_label: "Avg rating:",
  search_duration_result_label: "Duration:",
  search_not_available: "n/a",
  search_duration_0_15: "0–15 min",
  search_duration_15_30: "15–30 min",
  search_duration_30_plus: "30+ min",
  search_error: "Search failed. Please try again.",
  search_title_fallback: "Untitled",
  search_creator_fallback: "Unknown",
  search_load_more: "Load more",
  search_loading_more: "Loading...",

  login_title: "Login",
  login_subtitle: "Welcome back. Please sign in to continue.",
  login_email_label: "Email",
  login_password_label: "Password",
  login_email_required: "Email is required",
  login_email_invalid: "Please enter a valid email address",
  login_password_required: "Password is required",
  auth_show_password: "Show",
  auth_hide_password: "Hide",
  login_remember_email: "Remember my email",
  login_submitting: "Signing in...",
  login_submit: "Sign in",
  login_error_default: "Login failed.",
  login_forgot_password: "Forgot password? (Coming soon)",
  login_no_account: "Don't have an account?",
  login_create_account_link: "Create one",

  register_title: "Register",
  register_subtitle: "Create your account to start using DiWeiWei Nano Market.",
  register_email_label: "Email",
  register_username_label: "Username",
  register_password_label: "Password",
  register_confirm_password_label: "Confirm password",
  register_email_required: "Email is required",
  register_email_invalid: "Please enter a valid email address",
  register_username_required: "Username is required",
  register_username_min: "Username must be at least 3 characters",
  register_username_max: "Username must be at most 20 characters",
  register_username_pattern: "Only letters, numbers, and underscore are allowed",
  register_password_required: "Password is required",
  register_password_policy: "Password does not meet the required policy",
  register_confirm_required: "Please confirm your password",
  register_confirm_mismatch: "Passwords do not match",
  register_strength_weak: "weak",
  register_strength_medium: "medium",
  register_strength_strong: "strong",
  register_password_strength: "Strength:",
  register_requirements_title: "Password requirements",
  register_requirement_min_length: "Minimum 8 characters",
  register_requirement_uppercase: "At least 1 uppercase letter",
  register_requirement_digit: "At least 1 digit",
  register_requirement_special: "At least 1 special character",
  register_accept_terms_prefix: "I accept the",
  register_accept_terms_link: "Terms of Service",
  register_accept_privacy_prefix: "I accept the",
  register_accept_privacy_link: "Privacy Policy",
  register_accept_terms_required: "You must accept the Terms of Service",
  register_accept_privacy_required: "You must accept the Privacy Policy",
  register_submit: "Create account",
  register_submitting: "Creating account...",
  register_error_default: "Registration failed.",
  register_error_connection: "Connection error. Please try again.",
  register_error_request_failed: "Request failed. Please try again.",
  register_error_email_exists: "This email address is already registered.",
  register_error_username_exists: "This username is already taken.",
  register_error_terms: "You must accept the Terms of Service to register.",
  register_error_privacy: "You must accept the Privacy Policy to register.",
  register_error_password_length: "Password must be at least 8 characters.",
  register_error_password_uppercase: "Password must contain at least one uppercase letter.",
  register_error_password_digit: "Password must contain at least one digit.",
  register_error_password_special: "Password must contain at least one special character.",
  register_error_service_unavailable: "Service is temporarily unavailable. Please try again later.",
  register_has_account: "Already have an account?",
  register_go_login: "Go to login",

  verify_title: "Verify email",
  verify_subtitle: "Check your email for a verification link.",
  verify_registered_email: "Registered email:",
  verify_email_not_provided: "(not provided)",
  verify_success_redirect: "Email verified! Redirecting to login...",
  verify_error_invalid: "Link expired or invalid. Request a new email.",
  verify_resend_success: "Verification email resent.",
  verify_resend_failed: "Failed to resend verification email.",
  verify_resend_button: "Resend verification email",
  verify_resend_button_cooldown: "Resend verification email ({seconds}s)",
  verify_register_again: "Register again to provide an email for resending verification links.",
  verify_already_verified: "Already verified?",
  verify_go_login: "Go to login",

  nano_details_title: "Nano Details",
  nano_details_description: "Placeholder detail route. Current nano id: {id}",
  dashboard_title: "Dashboard",
  dashboard_description: "Protected dashboard placeholder route.",
  profile_title: "Profile",
  profile_description: "Protected profile placeholder route.",
  admin_title: "Admin",
  admin_description: "Protected admin placeholder route.",
  not_found_title: "Page Not Found",
  not_found_description:
    "The requested route does not exist. Use navigation to return to known routes.",
  not_found_back_home: "Back to Home",

  home_title: "DiWeiWei Nano Market",
  home_hero_description:
    "The marketplace for nano learning units. Exchange, discover, and evolve high-quality training content in one ecosystem for lifelong learning.",
  home_cta_register: "Register Now",
  home_cta_discover: "Discover Learning Units",
  home_features_title: "Why DiWeiWei?",
  home_feature_quality_title: "High-Quality Content",
  home_feature_quality_description:
    "Curated nano learning units from experts for fast, focused learning.",
  home_feature_share_title: "Easy to Share",
  home_feature_share_description:
    "Upload, manage, and share content with the community quickly.",
  home_feature_fast_title: "Fast Access",
  home_feature_fast_description:
    "Mobile-optimized and lightning fast. Learn anytime, anywhere.",
  home_creator_title: "Are you a content creator or trainer?",
  home_creator_description:
    "Share your expertise as nano learning units and reach a global audience.",
  home_creator_cta: "Join as Creator",
  home_footer_terms: "Terms of Service",
  home_footer_privacy: "Privacy Policy",
  home_footer_copy: "© 2026 DiWeiWei Nano Market. All rights reserved. | Sprint 3 Launch",
};

const translations: Record<SupportedLanguage, Record<TranslationKey, string>> = {
  de,
  en,
};

function isSupportedLanguage(value: string | null): value is SupportedLanguage {
  return value === "de" || value === "en";
}

interface LanguageContextValue {
  language: SupportedLanguage;
  setLanguage: (language: SupportedLanguage) => void;
}

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

export function LanguageProvider({ children }: PropsWithChildren): JSX.Element {
  const [language, setLanguageState] = useState<SupportedLanguage>(() => {
    if (typeof window === "undefined") {
      return "de";
    }

    const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    return isSupportedLanguage(stored) ? stored : "de";
  });

  const setLanguage = useCallback((nextLanguage: SupportedLanguage) => {
    setLanguageState(nextLanguage);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(LANGUAGE_STORAGE_KEY, nextLanguage);
    }
  }, []);

  const value = useMemo<LanguageContextValue>(
    () => ({ language, setLanguage }),
    [language, setLanguage]
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage(): LanguageContextValue {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within LanguageProvider");
  }
  return context;
}

export function useTranslation(): {
  language: SupportedLanguage;
  t: (key: TranslationKey) => string;
} {
  const { language } = useLanguage();

  const t = useCallback(
    (key: TranslationKey): string => {
      return translations[language][key] ?? translations.de[key];
    },
    [language]
  );

  return { language, t };
}
