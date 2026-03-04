/**
 * Design Tokens - DiWeiWei Nano-Marktplatz Frontend
 *
 * Centralized design-token constants used in components and frontend logic.
 *
 * This module is aligned with the Tailwind theme's semantic palette and font
 * families while also exposing additional runtime token groupings for app code.
 *
 * Usage:
 * ```tsx
 * import { colors, typography, spacing } from "../shared/tokens"
 * 
 * const buttonColor = colors.primary[500]
 * const headingSize = typography.sizes.h2
 * ```
 */

/**
 * Color Design Tokens
 * Maps to Tailwind color palette defined in tailwind.config.ts
 */
export const colors = {
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
} as const;

/**
 * Typography Design Tokens
 * Font sizes, weights, and families
 */
export const typography = {
  fontFamily: {
    sans: "Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
    mono: "Fira Code, Courier New, monospace",
  },
  sizes: {
    h1: { size: "2rem", weight: 700, lineHeight: 1.2 },
    h2: { size: "1.75rem", weight: 700, lineHeight: 1.3 },
    h3: { size: "1.5rem", weight: 600, lineHeight: 1.4 },
    h4: { size: "1.25rem", weight: 600, lineHeight: 1.4 },
    h5: { size: "1.125rem", weight: 600, lineHeight: 1.5 },
    h6: { size: "1rem", weight: 600, lineHeight: 1.5 },
    bodyLg: { size: "1.125rem", weight: 400, lineHeight: 1.6 },
    bodyBase: { size: "1rem", weight: 400, lineHeight: 1.6 },
    bodySm: { size: "0.875rem", weight: 400, lineHeight: 1.5 },
    bodyXs: { size: "0.75rem", weight: 400, lineHeight: 1.5 },
    label: { size: "0.875rem", weight: 500, lineHeight: 1.5 },
    caption: { size: "0.75rem", weight: 500, lineHeight: 1.5 },
  },
  weights: {
    thin: 100,
    extralight: 200,
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
    black: 900,
  },
} as const;

/**
 * Spacing Design Tokens
 * Uses 4px base unit (Tailwind default)
 */
export const spacing = {
  xs: "0.25rem", // 4px
  sm: "0.5rem", // 8px
  md: "1rem", // 16px
  lg: "1.5rem", // 24px
  xl: "2rem", // 32px
  "2xl": "3rem", // 48px
  "3xl": "4rem", // 64px
} as const;

/**
 * Border Radius Design Tokens
 */
export const borderRadius = {
  none: "0",
  sm: "0.25rem",
  base: "0.375rem",
  md: "0.5rem",
  lg: "0.75rem",
  xl: "1rem",
  full: "9999px",
} as const;

/**
 * Shadow Design Tokens
 * Provides elevation through shadow depth
 */
export const shadows = {
  none: "none",
  xs: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
  sm: "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
  base: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
  md: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
  lg: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
  xl: "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
} as const;

/**
 * Transition Design Tokens
 * Standard animation durations and easing functions
 */
export const transitions = {
  duration: {
    fast: "150ms",
    base: "200ms",
    slow: "300ms",
    slower: "500ms",
  },
  easing: {
    ease: "cubic-bezier(0.25, 0.46, 0.45, 0.94)",
    easeIn: "cubic-bezier(0.42, 0, 1, 1)",
    easeOut: "cubic-bezier(0, 0, 0.58, 1)",
    easeInOut: "cubic-bezier(0.42, 0, 0.58, 1)",
  },
} as const;

/**
 * Breakpoints for Responsive Design
 * Mobile-first approach
 */
export const breakpoints = {
  xs: "320px",
  sm: "640px",
  md: "768px",
  lg: "1024px",
  xl: "1280px",
  "2xl": "1536px",
} as const;

/**
 * Z-Index Scale
 * Manages stacking context for modals, dropdowns, notifications
 */
export const zIndex = {
  auto: "auto",
  base: 0,
  dropdown: 1000,
  sticky: 1020,
  fixed: 1030,
  modalBackdrop: 1040,
  modal: 1050,
  popover: 1060,
  tooltip: 1070,
} as const;

/**
 * Opacity Scale
 * Standard opacity values for consistent transparency
 */
export const opacity = {
  0: 0,
  5: 0.05,
  10: 0.1,
  20: 0.2,
  25: 0.25,
  30: 0.3,
  40: 0.4,
  50: 0.5,
  60: 0.6,
  70: 0.7,
  75: 0.75,
  80: 0.8,
  90: 0.9,
  95: 0.95,
  100: 1,
} as const;

/**
 * Complete Design System Export
 * Re-exports all token categories for convenience
 */
export const designTokens = {
  colors,
  typography,
  spacing,
  borderRadius,
  shadows,
  transitions,
  breakpoints,
  zIndex,
  opacity,
} as const;

export default designTokens;
