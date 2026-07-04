export type Conversation = {
  id: string;
  title: string | null;
  subject_address: string | null;
  user_email: string | null;
  radius_miles: number | null;
  status: string;
  created_at: string;
  updated_at: string;
};

export type StoredMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type ChatStatus = "ready" | "submitted" | "streaming" | "error";
