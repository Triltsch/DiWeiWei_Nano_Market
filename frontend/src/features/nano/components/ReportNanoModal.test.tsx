/**
 * Report modal: reason focus, live character counter, static reason options.
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi, type ComponentProps } from "vitest";

import { LanguageProvider } from "../../../shared/i18n";
import { ReportNanoModal } from "./ReportNanoModal";

function renderModal(
  props?: Partial<ComponentProps<typeof ReportNanoModal>>
): ReturnType<typeof render> {
  const onClose = vi.fn();
  const onSubmit = vi.fn();
  return render(
    <LanguageProvider>
      <ReportNanoModal
        isOpen
        isSubmitting={false}
        onClose={onClose}
        onSubmit={onSubmit}
        {...props}
      />
    </LanguageProvider>
  );
}

describe("ReportNanoModal", () => {
  it("focuses the reason dropdown when opened and lists static reasons", () => {
    renderModal();

    expect(screen.getByRole("dialog", { name: "Unangemessenen Inhalt melden" })).toBeTruthy();
    const reasonSelect = screen.getByLabelText("Grund");
    expect(reasonSelect).toBe(document.activeElement);
    expect(screen.getByRole("option", { name: "SPAM" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "COPYRIGHT" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "OFFENSIVE" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "MISINFORMATION" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "OTHER" })).toBeTruthy();
  });

  it("updates the comment character counter as the user types", () => {
    renderModal();

    const commentField = screen.getByRole("textbox");
    expect(screen.getByText("0/500")).toBeTruthy();

    fireEvent.change(commentField, { target: { value: "a".repeat(45) } });

    expect(screen.getByText("45/500")).toBeTruthy();
  });

  it("shows a submitting label and keeps the dialog open while submitting", () => {
    renderModal({ isSubmitting: true });

    expect(screen.getByRole("button", { name: "Wird gesendet..." })).toBeTruthy();
    expect(screen.getByRole("dialog")).toBeTruthy();
  });
});
