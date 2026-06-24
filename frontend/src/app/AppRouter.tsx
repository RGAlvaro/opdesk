// Central route table for public auth pages and the protected app shell.

import { Navigate, Route, Routes } from "react-router-dom";

import { LoginPage } from "../features/auth/LoginPage";
import { SignupPage } from "../features/auth/SignupPage";
import { ProtectedRoute } from "../features/auth/ProtectedRoute";
import { PublicOnlyRoute } from "../features/auth/PublicOnlyRoute";
import {
  OrganizationDetailPage,
  OrganizationListPage,
  OrganizationMembersPage,
  OrganizationNewPage,
  OrganizationSettingsPage,
} from "../features/organizations/OrganizationPages";
import { ProfilePage } from "../features/profile/ProfilePage";
import { AppShell } from "./AppShell";
import { DashboardPage } from "./DashboardPage";
import { LandingPage } from "./LandingPage";

/** Map URLs to route guards, public pages, and authenticated app content. */
export function AppRouter() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <PublicOnlyRoute>
            <LandingPage />
          </PublicOnlyRoute>
        }
      />
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
      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="profile" element={<ProfilePage />} />
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
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
