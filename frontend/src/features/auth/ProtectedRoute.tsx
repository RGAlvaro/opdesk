import { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { ApiError } from "../../shared/api";
import { useSession } from "./session";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const location = useLocation();
  const session = useSession();

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
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (session.isError) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-surface px-4 text-ink">
        <div
          role="alert"
          className="rounded-md border border-line bg-white px-5 py-4 shadow-panel"
        >
          Unable to load your session.
        </div>
      </main>
    );
  }

  return children;
}
