// TypeScript contracts for SPEC-304 organization chat screens.

export type ChatConversationType =
  | "direct"
  | "organization_channel"
  | "project_channel";

export type ChatMember = {
  user_id: string;
  full_name: string;
  email: string;
  role: "owner" | "admin" | "member";
  shares_project: boolean;
};

export type ChatMemberListResponse = {
  items: ChatMember[];
};

export type ChatMessage = {
  id: string;
  conversation_id: string;
  organization_id: string;
  sender_id: string;
  body: string;
  created_at: string;
};

export type ChatConversation = {
  id: string;
  organization_id: string;
  conversation_type: ChatConversationType;
  project_id: string | null;
  direct_user_id: string | null;
  unread_count: number;
  last_message: ChatMessage | null;
  created_at: string;
  updated_at: string;
};

export type ChatConversationListResponse = {
  items: ChatConversation[];
};

export type ChatMessageListResponse = {
  items: ChatMessage[];
  total: number;
  limit: number;
  offset: number;
};
