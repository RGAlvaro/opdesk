// Route guard for public pages that authenticated users should skip.

import { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { ApiError } from "../../shared/api";
import { useSession } from "./session";

/** Redirect signed-in users away from public auth and landing routes. */
export function PublicOnlyRoute({ children }: { children: ReactNode }) {
  const session = useSession();

  if (session.isSuccess) {
    return <Navigate to="/app" replace />;
  }

  if (session.isPending) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-surface px-4 text-ink">
        <div className="rounded-md border border-line bg-white px-5 py-4 shadow-panel">
          Loading session
        </div>
      </main>
    );
  }

  if (session.error instanceof ApiError && session.error.status === 401) {
    return children;
  }

  return children;
}
