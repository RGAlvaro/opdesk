// Placeholder dashboard that anchors the authenticated workspace shell.

import { Building2, FolderKanban, ListChecks } from "lucide-react";
import { Link } from "react-router-dom";

const upcoming = [
  {
    title: "Organizations",
    description: "Create workspaces and manage role-aware membership.",
    icon: Building2,
    href: "/app/organizations",
  },
  {
    title: "Projects",
    description: "Open an organization to create and manage projects.",
    icon: FolderKanban,
    href: "/app/organizations",
  },
  {
    title: "Tasks",
    description: "Open a project to filter, assign, and update task work.",
    icon: ListChecks,
    href: "/app/organizations",
  },
];

/** Show current shell status and reserved space for upcoming modules. */
export function DashboardPage() {
  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Workspace overview</h1>
        <p className="mt-2 max-w-2xl text-muted">
          Monitor operational work as organization, project, and task modules
          become available.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {upcoming.map((item) => {
          const Icon = item.icon;
          return (
            <article
              key={item.title}
              className="rounded-md border border-line bg-white p-4"
            >
              <Icon aria-hidden="true" className="h-5 w-5 text-brand" />
              <h2 className="mt-3 font-semibold">{item.title}</h2>
              <p className="mt-2 text-sm text-muted">{item.description}</p>
              {item.href ? (
                <Link
                  to={item.href}
                  className="mt-3 inline-flex text-sm font-medium text-brand hover:underline"
                >
                  {item.title === "Organizations"
                    ? "Open organizations"
                    : `Open ${item.title.toLowerCase()}`}
                </Link>
              ) : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}
