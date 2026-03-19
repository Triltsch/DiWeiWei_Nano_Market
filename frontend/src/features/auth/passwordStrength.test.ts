/**
 * Password Strength Tests
 *
 * Tests for password strength classification and policy validation.
 * Verifies that password strength is correctly assessed based on character type diversity
 * and that policy requirements (uppercase, lowercase, digits, special characters) are validated.
 */

import { describe, expect, it } from "vitest";

import {
  getPasswordStrength,
  meetsPasswordPolicy,
  PASSWORD_REQUIREMENT_KEYS,
} from "./passwordStrength";

describe("passwordStrength", () => {
  /**
   * Verifies that short passwords with limited character diversity are classified as weak.
   * A password of only 3 lowercase characters should receive the "weak" classification.
   */
  it("classifies weak passwords", () => {
    expect(getPasswordStrength("abc").label).toBe("weak");
  });

  /**
   * Verifies that passwords with mixed case are classified as medium strength.
   * A password with uppercase and lowercase letters should receive the "medium" classification.
   */
  it("classifies medium passwords", () => {
    expect(getPasswordStrength("Abcdefgh").label).toBe("medium");
  });

  /**
   * Verifies that passwords with diverse character types are classified as strong.
   * A password with uppercase, lowercase, digits, and special characters should
   * receive the "strong" classification.
   */
  it("classifies strong passwords", () => {
    expect(getPasswordStrength("StrongPass1!").label).toBe("strong");
  });

  /**
   * Verifies that the password policy validator correctly assesses whether a password
   * meets the application's requirements (length, uppercase, lowercase, digits, special chars).
   * Strong passwords should pass validation while weak passwords should not.
   */
  it("validates policy requirements", () => {
    expect(meetsPasswordPolicy("StrongPass1!")).toBe(true);
    expect(meetsPasswordPolicy("sjdsfgJHKJB//%%8&&")).toBe(true);
    expect(meetsPasswordPolicy("StrongPass1/")).toBe(false);
    expect(meetsPasswordPolicy("weakpass")).toBe(false);
  });

  /**
   * Verifies that the exported password requirement keys remain stable so the
   * registration page can translate each bullet consistently.
   */
  it("exports translation keys for password requirements", () => {
    expect(PASSWORD_REQUIREMENT_KEYS).toEqual([
      "register_requirement_min_length",
      "register_requirement_uppercase",
      "register_requirement_digit",
      "register_requirement_special",
    ]);
  });
});
