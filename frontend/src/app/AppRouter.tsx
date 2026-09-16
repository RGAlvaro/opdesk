// Central route table for public auth pages and the protected app shell.

import { Navigate, Route, Routes } from "react-router-dom";

import { LoginPage } from "../features/auth/LoginPage";
import { SignupPage } from "../features/auth/SignupPage";
import { ProtectedRoute } from "../features/auth/ProtectedRoute";
import { PublicOnlyRoute } from "../features/auth/PublicOnlyRoute";
import { useSession } from "../features/auth/session";
import {
  ClientTicketDetailPage,
  ClientTicketListPage,
  InternalTicketDetailPage,
  InternalTicketListPage,
  TicketAssignmentRequestsPage,
} from "../features/client-tickets/ClientTicketPages";
import { OrganizationChatPage } from "../features/chat/ChatPage";
import {
  OrganizationDetailPage,
  OrganizationListPage,
  OrganizationMembersPage,
  OrganizationNewPage,
  OrganizationSettingsPage,
} from "../features/organizations/OrganizationPages";
import { MyInvitationsPage } from "../features/organizations/InvitationsPage";
import { NotificationsPage } from "../features/notifications/NotificationsPage";
import { OperationalAuditPage } from "../features/operational-audit/OperationalAuditPage";
import {
  ProjectDetailPage,
  ProjectListPage,
  ProjectNewPage,
  ProjectSettingsPage,
} from "../features/projects/ProjectPages";
import { ProfilePage } from "../features/profile/ProfilePage";
import {
  TaskDetailPage,
  TaskListPage,
  TaskNewPage,
} from "../features/tasks/TaskPages";
import { AppShell } from "./AppShell";
import { ChangelogPage } from "./ChangelogPage";
import { DashboardPage } from "./DashboardPage";
import { LandingPage } from "./LandingPage";
import { CopyrightPage, CookiesPage, TermsPage } from "./LegalPages";

/** Map URLs to route guards, public pages, and authenticated app content. */
function AppIndexPage() {
  const { data: user } = useSession();
  if (user?.account_type === "client") {
    return <Navigate to="/app/client" replace />;
  }
  return <DashboardPage />;
}

/** Map URLs to route guards, public pages, and authenticated app content. */
export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/terms" element={<TermsPage />} />
      <Route path="/copyright" element={<CopyrightPage />} />
      <Route path="/cookies" element={<CookiesPage />} />
      <Route
        path="/login"
        element={
          <PublicOnlyRoute>
            <LoginPage />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/signup"
        element={
          <PublicOnlyRoute>
            <SignupPage />
          </PublicOnlyRoute>
        }
      />
      <Route path="/changelog" element={<ChangelogPage />} />
      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<AppIndexPage />} />
        <Route path="client" element={<ClientTicketListPage />} />
        <Route
          path="client/tickets/:ticketId"
          element={<ClientTicketDetailPage />}
        />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="invitations" element={<MyInvitationsPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route
          path="admin/operational-audit"
          element={<OperationalAuditPage />}
        />
        <Route
          path="ticket-assignment-requests"
          element={<TicketAssignmentRequestsPage />}
        />
        <Route path="organizations" element={<OrganizationListPage />} />
        <Route path="organizations/new" element={<OrganizationNewPage />} />
        <Route
          path="organizations/:organizationId"
          element={<OrganizationDetailPage />}
        />
        <Route
          path="organizations/:organizationId/settings"
          element={<OrganizationSettingsPage />}
        />
        <Route
          path="organizations/:organizationId/members"
          element={<OrganizationMembersPage />}
        />
        <Route
          path="organizations/:organizationId/chat"
          element={<OrganizationChatPage />}
        />
        <Route
          path="organizations/:organizationId/projects"
          element={<ProjectListPage />}
        />
        <Route
          path="organizations/:organizationId/projects/new"
          element={<ProjectNewPage />}
        />
        <Route path="projects/:projectId" element={<ProjectDetailPage />} />
        <Route
          path="projects/:projectId/settings"
          element={<ProjectSettingsPage />}
        />
        <Route path="projects/:projectId/tasks" element={<TaskListPage />} />
        <Route path="projects/:projectId/tasks/new" element={<TaskNewPage />} />
        <Route
          path="projects/:projectId/tickets"
          element={<InternalTicketListPage />}
        />
        <Route path="tasks/:taskId" element={<TaskDetailPage />} />
        <Route
          path="tickets/:ticketId"
          element={<InternalTicketDetailPage />}
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
