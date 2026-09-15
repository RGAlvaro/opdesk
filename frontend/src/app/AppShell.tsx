// Authenticated application shell with navigation, user chrome, and nested pages.

import {
  Activity,
  Bell,
  Building2,
  FolderKanban,
  ListChecks,
  LogOut,
  Mail,
  MessageCircle,
  Ticket,
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
import {
  useNotificationRealtime,
  useUnreadNotificationCount,
} from "../features/notifications/api";
import { useOrganizations } from "../features/organizations/api";
import { useProject } from "../features/projects/api";
import { useTask } from "../features/tasks/api";

type PrimarySection =
  | "organizations"
  | "projects"
  | "tasks"
  | "invitations"
  | "notifications"
  | "operational-audit"
  | "assignment-requests"
  | "chat"
  | "client";

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
    if (/^\/app\/organizations\/[^/]+\/chat(\/|$)/.test(pathname)) {
      return "chat";
    }
    return "organizations";
  }
  if (/^\/app\/invitations(\/|$)/.test(pathname)) {
    return "invitations";
  }
  if (/^\/app\/notifications(\/|$)/.test(pathname)) {
    return "notifications";
  }
  if (/^\/app\/admin\/operational-audit(\/|$)/.test(pathname)) {
    return "operational-audit";
  }
  if (/^\/app\/ticket-assignment-requests(\/|$)/.test(pathname)) {
    return "assignment-requests";
  }
  if (/^\/app\/client(\/|$)/.test(pathname)) {
    return "client";
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
  badge,
}: {
  icon: ReactNode;
  label: string;
  section: PrimarySection;
  to: string | undefined;
  activeSection: PrimarySection | undefined;
  badge?: number;
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
        <span className="min-w-0 flex-1">{label}</span>
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
      <span className="min-w-0 flex-1">{label}</span>
      {badge && badge > 0 ? (
        <span
          aria-label={`${badge} unread notifications`}
          className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
            isActive ? "bg-white text-brand" : "bg-brand text-white"
          }`}
        >
          {badge > 99 ? "99+" : badge}
        </span>
      ) : null}
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
  const unreadNotifications = useUnreadNotificationCount();
  useNotificationRealtime(Boolean(user));
  const activeSection = activePrimarySection(location.pathname);
  const isClient = user?.account_type === "client";
  const organizations = useOrganizations(
    Boolean(user) && !isClient && activeSection === "operational-audit",
  );
  const organizationItems = Array.isArray(organizations.data?.items)
    ? organizations.data.items
    : [];
  const canSeeOperationalAudit =
    !isClient &&
    organizationItems.some((organization) =>
      ["owner", "admin"].includes(organization.role),
    );
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
  const chatHref = projectOrganizationId
    ? `/app/organizations/${projectOrganizationId}/chat`
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
            {isClient ? (
              <>
                <PrimaryNavItem
                  icon={<Ticket aria-hidden="true" className="h-4 w-4" />}
                  label="My tickets"
                  section="client"
                  to="/app/client"
                  activeSection={activeSection}
                />
                <NavLink
                  to="/app/profile"
                  className={({ isActive }) =>
                    `block rounded-md px-3 py-2 text-sm font-medium ${
                      isActive
                        ? "bg-brand text-white"
                        : "text-ink hover:bg-surface"
                    }`
                  }
                >
                  Profile
                </NavLink>
              </>
            ) : (
              <>
                <NavLink
                  to="/app"
                  end
                  className={({ isActive }) =>
                    `block rounded-md px-3 py-2 text-sm font-medium ${
                      isActive
                        ? "bg-brand text-white"
                        : "text-ink hover:bg-surface"
                    }`
                  }
                >
                  Overview
                </NavLink>
                <NavLink
                  to="/app/profile"
                  className={({ isActive }) =>
                    `block rounded-md px-3 py-2 text-sm font-medium ${
                      isActive
                        ? "bg-brand text-white"
                        : "text-ink hover:bg-surface"
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
                    icon={<Bell aria-hidden="true" className="h-4 w-4" />}
                    label="Notifications"
                    section="notifications"
                    to="/app/notifications"
                    activeSection={activeSection}
                    badge={unreadNotifications.data?.unread_count}
                  />
                  {canSeeOperationalAudit ? (
                    <PrimaryNavItem
                      icon={<Activity aria-hidden="true" className="h-4 w-4" />}
                      label="Operational audit"
                      section="operational-audit"
                      to="/app/admin/operational-audit"
                      activeSection={activeSection}
                    />
                  ) : null}
                  <PrimaryNavItem
                    icon={<Mail aria-hidden="true" className="h-4 w-4" />}
                    label="Invitations"
                    section="invitations"
                    to="/app/invitations"
                    activeSection={activeSection}
                  />
                  <PrimaryNavItem
                    icon={
                      <MessageCircle aria-hidden="true" className="h-4 w-4" />
                    }
                    label="Chat"
                    section="chat"
                    to={chatHref}
                    activeSection={activeSection}
                  />
                  <PrimaryNavItem
                    icon={<Ticket aria-hidden="true" className="h-4 w-4" />}
                    label="Assignment requests"
                    section="assignment-requests"
                    to="/app/ticket-assignment-requests"
                    activeSection={activeSection}
                  />
                  <PrimaryNavItem
                    icon={
                      <FolderKanban aria-hidden="true" className="h-4 w-4" />
                    }
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
              </>
            )}
          </nav>
        </aside>

        <main>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
