import type { PropsWithChildren } from "react";

export function AppShell({ children }: PropsWithChildren): JSX.Element {
  return (
    <main
      style={{
        margin: "0 auto",
        maxWidth: "960px",
        minHeight: "100vh",
        padding: "2rem"
      }}
    >
      {children}
    </main>
  );
}
