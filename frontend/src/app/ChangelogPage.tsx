// Public release notes page backed by the repository changelog.

import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

import changelogMarkdown from "../../../CHANGELOG.md?raw";
import { parseChangelog } from "./changelog";

const changelogEntries = parseChangelog(changelogMarkdown);

/** Render production release notes without requiring an authenticated session. */
export function ChangelogPage() {
  return (
    <main className="min-h-screen bg-surface text-ink">
      <section className="mx-auto max-w-4xl px-4 py-10 sm:py-14">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm font-semibold text-brand hover:text-brand/80"
        >
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          OpsDesk
        </Link>
        <div className="mt-8">
          <p className="text-sm font-semibold uppercase tracking-wide text-brand">
            Release notes
          </p>
          <h1 className="mt-3 text-3xl font-semibold sm:text-4xl">Changelog</h1>
          <p className="mt-4 max-w-2xl text-muted">
            Production release notes for user-visible additions, changes, and
            fixes.
          </p>
        </div>

        <div className="mt-10 space-y-8">
          {changelogEntries.map((entry) => (
            <article
              key={entry.heading}
              className="rounded-md border border-line bg-white p-5 shadow-panel sm:p-6"
            >
              <h2 className="text-xl font-semibold">{entry.heading}</h2>
              <div className="mt-5 space-y-5">
                {entry.sections.map((section) => (
                  <section key={section.name}>
                    <h3 className="text-sm font-semibold uppercase tracking-wide text-muted">
                      {section.name}
                    </h3>
                    <ul className="mt-2 list-disc space-y-2 pl-5 text-sm leading-6 text-ink sm:text-base">
                      {section.items.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </section>
                ))}
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
