// TypeScript contracts for organization and membership API responses.

export type OrganizationRole = "owner" | "admin" | "member";

/** Paginated response shape shared by organization list endpoints. */
export type PaginatedResponse<TItem> = {
  items: TItem[];
  total: number;
  limit: number;
  offset: number;
};

/** Standard list pagination parameters accepted by backend endpoints. */
export type PaginationParams = {
  limit: number;
  offset: number;
};

/** Organization fields returned with the current user's role. */
export type Organization = {
  id: string;
  name: string;
  slug: string;
  role: OrganizationRole;
  employee_count: number | null;
  industry: string | null;
  website: string | null;
  contact_email: string | null;
  phone: string | null;
  address_line1: string | null;
  address_line2: string | null;
  city: string | null;
  region: string | null;
  postal_code: string | null;
  country: string | null;
  tax_id: string | null;
  logo_url: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
};

/** Payload accepted by organization create and update mutations. */
export type OrganizationPayload = {
  name?: string;
  employee_count?: number | null;
  industry?: string | null;
  website?: string | null;
  contact_email?: string | null;
  phone?: string | null;
  address_line1?: string | null;
  address_line2?: string | null;
  city?: string | null;
  region?: string | null;
  postal_code?: string | null;
  country?: string | null;
  tax_id?: string | null;
  logo_url?: string | null;
  description?: string | null;
};

/** Safe user fields embedded inside membership responses. */
export type MembershipUser = {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
};

/** Membership row returned to organization administrators. */
export type OrganizationMembership = {
  id: string;
  user_id: string;
  organization_id: string;
  role: OrganizationRole;
  user: MembershipUser;
  created_at: string;
  updated_at: string;
};

export type OrganizationListResponse = PaginatedResponse<Organization>;
export type MembershipListResponse = PaginatedResponse<OrganizationMembership>;

export type InvitationStatus =
  | "pending"
  | "accepted"
  | "declined"
  | "cancelled"
  | "expired";

export type InvitationScope = "organization" | "project";

/** Invitation row returned for recipient and organization-admin views. */
export type Invitation = {
  id: string;
  organization_id: string;
  organization_name: string | null;
  target_email: string;
  target_user_id: string;
  role: Exclude<OrganizationRole, "owner"> | null;
  scope_type: InvitationScope;
  project_id: string | null;
  project_name: string | null;
  status: InvitationStatus;
  accepted_at: string | null;
  declined_at: string | null;
  cancelled_at: string | null;
  expires_at: string;
  created_at: string;
  updated_at: string;
};

export type InvitationListResponse = PaginatedResponse<Invitation>;
