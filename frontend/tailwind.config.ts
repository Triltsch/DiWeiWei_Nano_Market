import type { Config } from "tailwindcss";

/**
 * Tailwind CSS Configuration for DiWeiWei Nano-Marktplatz Frontend
 *
 * Defines shared design tokens for colors, typography, and spacing.
 * These tokens are used across all frontend components following the design system.
 */

const config: Config = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    colors: {
      // Core colors
      white: "#ffffff",
      black: "#000000",
      transparent: "transparent",
      current: "currentColor",
      inherit: "inherit",

      // Neutral grays - used for text, backgrounds, borders
      neutral: {
        0: "#ffffff",
        50: "#f9fafb",
        100: "#f3f4f6",
        200: "#e5e7eb",
        300: "#d1d5db",
        400: "#9ca3af",
        500: "#6b7280",
        600: "#4b5563",
        700: "#374151",
        800: "#1f2937",
        900: "#111827",
        950: "#030712",
      },

      // Primary accent - DiWeiWei brand blue
      primary: {
        50: "#eff6ff",
        100: "#dbeafe",
        200: "#bfdbfe",
        300: "#93c5fd",
        400: "#60a5fa",
        500: "#3b82f6",
        600: "#2563eb",
        700: "#1d4ed8",
        800: "#1e40af",
        900: "#1e3a8a",
        950: "#172554",
      },

      // Secondary accent - for alternative CTAs
      secondary: {
        50: "#f5f3ff",
        100: "#ede9fe",
        200: "#ddd6fe",
        300: "#c4b5fd",
        400: "#a78bfa",
        500: "#8b5cf6",
        600: "#7c3aed",
        700: "#6d28d9",
        800: "#5b21b6",
        900: "#4c1d95",
        950: "#2e1065",
      },

      // Success - for positive actions and status
      success: {
        50: "#f0fdf4",
        100: "#dcfce7",
        200: "#bbf7d0",
        300: "#86efac",
        400: "#4ade80",
        500: "#22c55e",
        600: "#16a34a",
        700: "#15803d",
        800: "#166534",
        900: "#145231",
        950: "#052e16",
      },

      // Warning - for cautionary states
      warning: {
        50: "#fffbeb",
        100: "#fef3c7",
        200: "#fde68a",
        300: "#fcd34d",
        400: "#fbbf24",
        500: "#f59e0b",
        600: "#d97706",
        700: "#b45309",
        800: "#92400e",
        900: "#78350f",
        950: "#451a03",
      },

      // Error - for alerts and destructive actions
      error: {
        50: "#fef2f2",
        100: "#fee2e2",
        200: "#fecaca",
        300: "#fca5a5",
        400: "#f87171",
        500: "#ef4444",
        600: "#dc2626",
        700: "#b91c1c",
        800: "#991b1b",
        900: "#7f1d1d",
        950: "#4c0519",
      },

      // Info - for informational messages
      info: {
        50: "#f0f9ff",
        100: "#e0f2fe",
        200: "#bae6fd",
        300: "#7dd3fc",
        400: "#38bdf8",
        500: "#0ea5e9",
        600: "#0284c7",
        700: "#0369a1",
        800: "#075985",
        900: "#0c4a6e",
        950: "#051e3e",
      },
    },
    fontFamily: {
      sans: ["Inter", "system-ui", "-apple-system", "Segoe UI", "Roboto", "sans-serif"],
      mono: ["Fira Code", "Courier New", "monospace"],
    },
    fontSize: {
      xs: ["0.75rem", { lineHeight: "1.5" }],
      sm: ["0.875rem", { lineHeight: "1.5" }],
      base: ["1rem", { lineHeight: "1.6" }],
      lg: ["1.125rem", { lineHeight: "1.6" }],
      xl: ["1.25rem", { lineHeight: "1.4" }],
      "2xl": ["1.5rem", { lineHeight: "1.4" }],
      "3xl": ["1.75rem", { lineHeight: "1.3" }],
      "4xl": ["2rem", { lineHeight: "1.2" }],
    },
    extend: {
      boxShadow: {
        xs: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        sm: "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
      },
      transitionDuration: {
        fast: "150ms",
        base: "200ms",
        slow: "300ms",
        slower: "500ms",
      },
    },
  },
  plugins: [],
};

export default config;
