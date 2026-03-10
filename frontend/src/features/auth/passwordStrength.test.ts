import { describe, expect, it } from "vitest";

import { getPasswordStrength, meetsPasswordPolicy } from "./passwordStrength";

describe("passwordStrength", () => {
  it("classifies weak passwords", () => {
    expect(getPasswordStrength("abc").label).toBe("weak");
  });

  it("classifies medium passwords", () => {
    expect(getPasswordStrength("Abcdefgh").label).toBe("medium");
  });

  it("classifies strong passwords", () => {
    expect(getPasswordStrength("StrongPass1!").label).toBe("strong");
  });

  it("validates policy requirements", () => {
    expect(meetsPasswordPolicy("StrongPass1!")).toBe(true);
    expect(meetsPasswordPolicy("weakpass")).toBe(false);
  });
});
