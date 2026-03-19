import type { TranslationKey } from "../../shared/i18n";
import type { PasswordStrengthLabel } from "./types";

interface PasswordStrengthResult {
  label: PasswordStrengthLabel;
  score: number;
}

/**
 * Keep the frontend password rules aligned with the backend validator in
 * app/modules/auth/validators.py.
 */
export const PASSWORD_SPECIAL_CHARACTER_PATTERN = /[!@#$%^&*(),.?":{}|<>]/;

export const PASSWORD_REQUIREMENT_KEYS: readonly TranslationKey[] = [
  "register_requirement_min_length",
  "register_requirement_uppercase",
  "register_requirement_digit",
  "register_requirement_special",
] as const;

export function getPasswordStrength(password: string): PasswordStrengthResult {
  if (!password) {
    return { label: "weak", score: 0 };
  }

  let score = 0;

  if (password.length >= 8) score += 30;
  if (/[A-Z]/.test(password)) score += 20;
  if (/[0-9]/.test(password)) score += 20;
  if (PASSWORD_SPECIAL_CHARACTER_PATTERN.test(password)) score += 20;
  if (password.length >= 12) score += 10;

  if (score >= 80) {
    return { label: "strong", score };
  }

  if (score >= 50) {
    return { label: "medium", score };
  }

  return { label: "weak", score };
}

export function meetsPasswordPolicy(password: string): boolean {
  return (
    password.length >= 8 &&
    /[A-Z]/.test(password) &&
    /[0-9]/.test(password) &&
    PASSWORD_SPECIAL_CHARACTER_PATTERN.test(password)
  );
}
