// Placeholder dashboard that anchors the authenticated workspace shell.

import { Building2, FolderKanban, ListChecks } from "lucide-react";

const upcoming = [
  {
    title: "Organizations",
    description:
      "Workspace membership and role-aware navigation will connect here.",
    icon: Building2,
  },
  {
    title: "Projects",
    description:
      "Project lists and details will appear after organization APIs are available.",
    icon: FolderKanban,
  },
  {
    title: "Tasks",
    description: "Task tracking will appear when the module is available.",
    icon: ListChecks,
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
            </article>
          );
        })}
      </div>
    </section>
  );
}
