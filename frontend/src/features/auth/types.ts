export type User = {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
};

export type LoginResponse = {
  user: User;
};

export type StatusResponse = {
  status: string;
};
