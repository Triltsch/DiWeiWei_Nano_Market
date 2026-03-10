/**
 * Password Strength Tests
 *
 * Tests for password strength classification and policy validation.
 * Verifies that password strength is correctly assessed based on character type diversity
 * and that policy requirements (uppercase, lowercase, digits, special characters) are validated.
 */

import { describe, expect, it } from "vitest";

import { getPasswordStrength, meetsPasswordPolicy } from "./passwordStrength";

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
    expect(meetsPasswordPolicy("weakpass")).toBe(false);
  });
});
