// Public entry page that routes visitors toward authentication.

import { ArrowRight, LogIn } from "lucide-react";
import { Link } from "react-router-dom";

/** Present OpsDesk's current public call to action and roadmap preview. */
export function LandingPage() {
  return (
    <main className="min-h-screen bg-surface text-ink">
      <section className="mx-auto flex min-h-screen max-w-6xl flex-col justify-center px-4 py-12">
        <div className="grid items-center gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-brand">
              OpsDesk
            </p>
            <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-tight sm:text-5xl">
              Operational work management for teams that need clear ownership.
            </h1>
            <p className="mt-5 max-w-2xl text-lg text-muted">
              Sign in to manage your profile today. Organizations, projects, and
              tasks are prepared in the product roadmap and will connect into
              this shell as they land.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                to="/login"
                className="inline-flex items-center justify-center gap-2 rounded-md bg-brand px-5 py-3 font-semibold text-white hover:bg-brand/90"
              >
                <LogIn aria-hidden="true" className="h-5 w-5" />
                Log in
              </Link>
              <Link
                to="/signup"
                className="inline-flex items-center justify-center gap-2 rounded-md border border-line bg-white px-5 py-3 font-semibold hover:bg-surface"
              >
                Create account
                <ArrowRight aria-hidden="true" className="h-5 w-5" />
              </Link>
            </div>
          </div>

          <div className="rounded-md border border-line bg-white p-6 shadow-panel">
            <div className="grid gap-4">
              {["Identity", "Workspace", "Delivery"].map((item) => (
                <div key={item} className="rounded-md border border-line p-4">
                  <p className="font-semibold">{item}</p>
                  <p className="mt-1 text-sm text-muted">
                    {item === "Identity"
                      ? "Secure cookie-based auth and profile management."
                      : "Reserved app structure for upcoming product modules."}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
