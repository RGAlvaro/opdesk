// Shared TypeScript contracts for auth and profile API responses.

/** Public user profile fields returned by the backend. */
export type User = {
  id: string;
  email: string;
  full_name: string;
  job_title: string | null;
  phone: string | null;
  timezone: string | null;
  locale: string | null;
  avatar_url: string | null;
  bio: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
};

/** Login endpoint response after cookies have been set by the browser. */
export type LoginResponse = {
  user: User;
};

/** Small success envelope used by auth endpoints without payload data. */
export type StatusResponse = {
  status: string;
};
