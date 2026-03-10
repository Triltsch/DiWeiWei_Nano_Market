import type { PasswordStrengthLabel } from "./types";

interface PasswordStrengthResult {
  label: PasswordStrengthLabel;
  score: number;
}

export const PASSWORD_REQUIREMENTS = [
  "Minimum 8 characters",
  "At least 1 uppercase letter",
  "At least 1 digit",
  "At least 1 special character",
] as const;

export function getPasswordStrength(password: string): PasswordStrengthResult {
  if (!password) {
    return { label: "weak", score: 0 };
  }

  let score = 0;

  if (password.length >= 8) score += 30;
  if (/[A-Z]/.test(password)) score += 20;
  if (/[0-9]/.test(password)) score += 20;
  if (/[^A-Za-z0-9]/.test(password)) score += 20;
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
    /[^A-Za-z0-9]/.test(password)
  );
}
