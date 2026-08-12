// Public portfolio home that presents OpsDesk and future app work.

import {
  ArrowRight,
  CheckCircle2,
  Clock,
  ExternalLink,
  LogIn,
} from "lucide-react";
import { Link } from "react-router-dom";

import portfolioHubImage from "../assets/portfolio-hub.png";

type PortfolioApp = {
  name: string;
  status: "Available" | "Coming soon";
  description: string;
  points: string[];
  primaryAction?: { label: string; to: string };
  secondaryAction?: { label: string; to: string };
};

const apps: PortfolioApp[] = [
  {
    name: "OpsDesk",
    status: "Available",
    description:
      "A production-minded B2B operations app for organizations, projects, tasks, labels, metadata, and release discipline.",
    primaryAction: { label: "Open OpsDesk", to: "/login" },
    secondaryAction: { label: "Create account", to: "/signup" },
    points: ["FastAPI backend", "React TypeScript UI", "Docker release path"],
  },
  {
    name: "Small-team ERP",
    status: "Coming soon",
    description:
      "A future easy-to-use ERP concept for small teams that need simple operations, clients, tickets, and back-office workflows.",
    points: ["Future app", "No live product yet", "Planned portfolio slot"],
  },
] as const;

/** Present the public portfolio hub without requiring backend session state. */
export function LandingPage() {
  return (
    <main className="min-h-screen bg-surface text-ink">
      <section className="mx-auto max-w-6xl px-4 py-6 sm:py-8">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <Link to="/" className="text-sm font-semibold text-ink">
            RGAlvaro
          </Link>
          <nav
            aria-label="Public navigation"
            className="flex items-center gap-4 text-sm font-semibold"
          >
            <Link to="/changelog" className="text-muted hover:text-brand">
              Changelog
            </Link>
            <Link to="/login" className="text-muted hover:text-brand">
              Log in
            </Link>
          </nav>
        </header>

        <div className="grid min-h-[calc(100vh-5rem)] items-center gap-10 py-10 lg:grid-cols-[1fr_0.92fr]">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-wide text-brand">
              Portfolio app hub
            </p>
            <h1 className="mt-4 text-4xl font-semibold leading-tight sm:text-5xl">
              Production-minded SaaS projects, built for inspection.
            </h1>
            <p className="mt-5 text-lg leading-8 text-muted">
              I am a software engineer building focused B2B products with
              FastAPI, React, PostgreSQL, Docker, CI, and spec-driven delivery.
              This public hub links the live OpsDesk app and future portfolio
              work without presenting unfinished products as available.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                to="/login"
                className="inline-flex items-center justify-center gap-2 rounded-md bg-brand px-5 py-3 font-semibold text-white hover:bg-brand/90"
              >
                <LogIn aria-hidden="true" className="h-5 w-5" />
                Open OpsDesk
              </Link>
              <Link
                to="/changelog"
                className="inline-flex items-center justify-center gap-2 rounded-md border border-line bg-white px-5 py-3 font-semibold hover:bg-surface"
              >
                Release notes
                <ArrowRight aria-hidden="true" className="h-5 w-5" />
              </Link>
            </div>
          </div>

          <div className="overflow-hidden rounded-md border border-line bg-white shadow-panel">
            <img
              src={portfolioHubImage}
              alt="Abstract SaaS dashboard displayed on a laptop"
              className="aspect-[16/10] w-full object-cover"
            />
          </div>
        </div>
      </section>

      <section className="border-t border-line bg-white">
        <div className="mx-auto grid max-w-6xl gap-5 px-4 py-10 md:grid-cols-2">
          {apps.map((app) => (
            <article
              key={app.name}
              className="rounded-md border border-line bg-white p-5"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-xl font-semibold">{app.name}</h2>
                <span
                  className={
                    app.status === "Available"
                      ? "inline-flex items-center gap-1 rounded-md bg-brand/10 px-2.5 py-1 text-sm font-semibold text-brand"
                      : "inline-flex items-center gap-1 rounded-md bg-surface px-2.5 py-1 text-sm font-semibold text-muted"
                  }
                >
                  {app.status === "Available" ? (
                    <CheckCircle2 aria-hidden="true" className="h-4 w-4" />
                  ) : (
                    <Clock aria-hidden="true" className="h-4 w-4" />
                  )}
                  {app.status}
                </span>
              </div>
              <p className="mt-3 leading-7 text-muted">{app.description}</p>
              <ul className="mt-4 grid gap-2 text-sm text-ink">
                {app.points.map((point) => (
                  <li key={point} className="flex items-center gap-2">
                    <span
                      aria-hidden="true"
                      className="h-1.5 w-1.5 rounded-full bg-brand"
                    />
                    {point}
                  </li>
                ))}
              </ul>
              {app.primaryAction ? (
                <div className="mt-5 flex flex-col gap-3 sm:flex-row">
                  <Link
                    to={app.primaryAction.to}
                    className="inline-flex items-center justify-center gap-2 rounded-md bg-brand px-4 py-2.5 font-semibold text-white hover:bg-brand/90"
                  >
                    {app.primaryAction.label}
                    <ExternalLink aria-hidden="true" className="h-4 w-4" />
                  </Link>
                  {app.secondaryAction ? (
                    <Link
                      to={app.secondaryAction.to}
                      className="inline-flex items-center justify-center rounded-md border border-line px-4 py-2.5 font-semibold hover:bg-surface"
                    >
                      {app.secondaryAction.label}
                    </Link>
                  ) : null}
                </div>
              ) : null}
            </article>
          ))}
        </div>
      </section>

      <footer className="border-t border-line bg-surface">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-6 text-sm text-muted sm:flex-row sm:items-center sm:justify-between">
          <p>OpsDesk is the currently available portfolio app.</p>
          <div className="flex gap-4 font-semibold">
            <Link to="/changelog" className="hover:text-brand">
              Changelog
            </Link>
            <Link to="/signup" className="hover:text-brand">
              Create account
            </Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
