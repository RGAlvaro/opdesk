// Authenticated application shell with navigation, user chrome, and nested pages.

import { LogOut, UserRound } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useLogout, useSession } from "../features/auth/session";

const disabledNavItems = ["Organizations", "Projects", "Tasks"];

/** Render the protected layout and route outlet for signed-in users. */
export function AppShell() {
  const { data: user } = useSession();
  const logout = useLogout();
  const navigate = useNavigate();

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
              {disabledNavItems.map((item) => (
                <span
                  key={item}
                  className="block rounded-md px-3 py-2 text-sm font-medium text-muted opacity-70"
                  aria-disabled="true"
                >
                  {item}
                </span>
              ))}
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
