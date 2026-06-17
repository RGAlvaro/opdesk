// Shared visual frame for login and signup pages.

import { ReactNode } from "react";
import { Link } from "react-router-dom";

/** Render consistent public auth page structure around form content. */
export function AuthLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <main className="min-h-screen bg-surface px-4 py-10 text-ink">
      <div className="mx-auto max-w-md">
        <Link to="/" className="text-sm font-semibold text-brand">
          OpsDesk
        </Link>
        <section className="mt-6 rounded-md border border-line bg-white p-6 shadow-panel">
          <h1 className="text-2xl font-semibold">{title}</h1>
          <p className="mt-2 text-sm text-muted">{subtitle}</p>
          <div className="mt-6">{children}</div>
        </section>
      </div>
    </main>
  );
}
