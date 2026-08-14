// Authenticated application shell with navigation, user chrome, and nested pages.

import {
  Building2,
  FolderKanban,
  ListChecks,
  LogOut,
  Mail,
  UserRound,
} from "lucide-react";
import {
  Link,
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
} from "react-router-dom";
import { ReactNode } from "react";

import { useLogout, useSession } from "../features/auth/session";
import { useProject } from "../features/projects/api";
import { useTask } from "../features/tasks/api";

type PrimarySection = "organizations" | "projects" | "tasks" | "invitations";

const primaryNavBaseClass =
  "flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm font-medium";

/** Identify the active top-level workspace section from the current URL. */
function activePrimarySection(pathname: string): PrimarySection | undefined {
  if (/^\/app\/projects\/[^/]+\/tasks(\/|$)/.test(pathname)) {
    return "tasks";
  }
  if (/^\/app\/tasks\/[^/]+(\/|$)/.test(pathname)) {
    return "tasks";
  }
  if (/^\/app\/organizations\/[^/]+\/projects(\/|$)/.test(pathname)) {
    return "projects";
  }
  if (/^\/app\/projects\/[^/]+(\/|$)/.test(pathname)) {
    return "projects";
  }
  if (/^\/app\/organizations(\/|$)/.test(pathname)) {
    return "organizations";
  }
  if (/^\/app\/invitations(\/|$)/.test(pathname)) {
    return "invitations";
  }
  return undefined;
}

/** Read a named route identifier from known app-shell route patterns. */
function routeId(pathname: string, pattern: RegExp) {
  return pattern.exec(pathname)?.[1];
}

/** Render one contextual app-shell navigation entry with disabled support. */
function PrimaryNavItem({
  icon,
  label,
  section,
  to,
  activeSection,
}: {
  icon: ReactNode;
  label: string;
  section: PrimarySection;
  to: string | undefined;
  activeSection: PrimarySection | undefined;
}) {
  const isActive = activeSection === section;
  const className = `${primaryNavBaseClass} ${
    isActive ? "bg-brand text-white" : "text-ink hover:bg-surface"
  }`;

  if (!to) {
    return (
      <button
        type="button"
        className={`${primaryNavBaseClass} cursor-not-allowed text-muted opacity-65`}
        aria-disabled="true"
        disabled
      >
        {icon}
        {label}
      </button>
    );
  }

  return (
    <Link
      to={to}
      className={className}
      aria-current={isActive ? "page" : undefined}
    >
      {icon}
      {label}
    </Link>
  );
}

/** Render the protected layout and route outlet for signed-in users. */
export function AppShell() {
  const { data: user } = useSession();
  const logout = useLogout();
  const navigate = useNavigate();
  const location = useLocation();
  const activeOrganizationId = routeId(
    location.pathname,
    /^\/app\/organizations\/([^/]+)/,
  );
  const routeProjectId = routeId(
    location.pathname,
    /^\/app\/projects\/([^/]+)/,
  );
  const routeTaskId = routeId(location.pathname, /^\/app\/tasks\/([^/]+)/);
  const project = useProject(routeProjectId);
  const task = useTask(routeTaskId);
  const activeSection = activePrimarySection(location.pathname);
  const activeProjectId = routeProjectId ?? task.data?.project_id;
  const projectOrganizationId =
    activeOrganizationId ??
    project.data?.organization_id ??
    task.data?.organization_id;
  const projectsHref = projectOrganizationId
    ? `/app/organizations/${projectOrganizationId}/projects`
    : undefined;
  const tasksHref = activeProjectId
    ? `/app/projects/${activeProjectId}/tasks`
    : undefined;

  /** End the session and return the browser to the public entry page. */
  async function handleLogout() {
    try {
      await logout.mutateAsync();
    } finally {
      navigate("/", { replace: true });
    }
  }

  return (
    <div className="min-h-screen bg-surface text-ink">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <NavLink to="/app" className="text-xl font-semibold">
              OpsDesk
            </NavLink>
            <p className="text-sm text-muted">Operational work management</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm">
              <UserRound aria-hidden="true" className="h-4 w-4 text-brand" />
              <span className="font-medium">{user?.full_name}</span>
              <span className="text-muted">{user?.email}</span>
            </div>
            <button
              type="button"
              className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-medium hover:bg-surface disabled:cursor-not-allowed disabled:opacity-60"
              disabled={logout.isPending}
              onClick={handleLogout}
            >
              <LogOut aria-hidden="true" className="h-4 w-4" />
              {logout.isPending ? "Signing out" : "Sign out"}
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl gap-6 px-4 py-6 lg:grid-cols-[220px_1fr]">
        <aside className="rounded-md border border-line bg-white p-3">
          <nav aria-label="Primary navigation" className="space-y-1">
            <NavLink
              to="/app"
              end
              className={({ isActive }) =>
                `block rounded-md px-3 py-2 text-sm font-medium ${
                  isActive ? "bg-brand text-white" : "text-ink hover:bg-surface"
                }`
              }
            >
              Overview
            </NavLink>
            <NavLink
              to="/app/profile"
              className={({ isActive }) =>
                `block rounded-md px-3 py-2 text-sm font-medium ${
                  isActive ? "bg-brand text-white" : "text-ink hover:bg-surface"
                }`
              }
            >
              Profile
            </NavLink>
            <div className="border-t border-line pt-2">
              <PrimaryNavItem
                icon={<Building2 aria-hidden="true" className="h-4 w-4" />}
                label="Organizations"
                section="organizations"
                to="/app/organizations"
                activeSection={activeSection}
              />
              <PrimaryNavItem
                icon={<Mail aria-hidden="true" className="h-4 w-4" />}
                label="Invitations"
                section="invitations"
                to="/app/invitations"
                activeSection={activeSection}
              />
              <PrimaryNavItem
                icon={<FolderKanban aria-hidden="true" className="h-4 w-4" />}
                label="Projects"
                section="projects"
                to={projectsHref}
                activeSection={activeSection}
              />
              <PrimaryNavItem
                icon={<ListChecks aria-hidden="true" className="h-4 w-4" />}
                label="Tasks"
                section="tasks"
                to={tasksHref}
                activeSection={activeSection}
              />
            </div>
          </nav>
        </aside>

        <main>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
