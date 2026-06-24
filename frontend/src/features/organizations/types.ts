// TypeScript contracts for organization and membership API responses.

export type OrganizationRole = "owner" | "admin" | "member";

/** Paginated response shape shared by organization list endpoints. */
export type PaginatedResponse<TItem> = {
  items: TItem[];
  total: number;
  limit: number;
  offset: number;
};

/** Organization fields returned with the current user's role. */
export type Organization = {
  id: string;
  name: string;
  slug: string;
  role: OrganizationRole;
  created_at: string;
  updated_at: string;
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
