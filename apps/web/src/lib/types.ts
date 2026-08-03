export interface PageMeta {
  page: number;
  page_size: number;
  total: number;
}

export interface ItemResponse<T> {
  data: T;
}

export interface ListResponse<T> {
  data: T[];
  meta: PageMeta;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url: string | null;
  timezone: string;
  created_at: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export type WorkspaceRole = "admin" | "product_owner" | "scrum_master" | "developer" | "viewer";

export interface MyWorkspace {
  id: string;
  organization_id: string;
  organization_name: string;
  name: string;
  slug: string;
  role: WorkspaceRole;
}

export type ProjectStatus = "active" | "archived" | "on_hold";

export interface Project {
  id: string;
  workspace_id: string;
  key: string;
  name: string;
  description: string | null;
  status: ProjectStatus;
  progress: number;
  progress_override: number | null;
  created_at: string;
  updated_at: string;
}

export type WorkItemType = "epic" | "feature" | "story" | "task" | "subtask" | "checklist_item";
export type WorkItemStatus = "todo" | "in_progress" | "in_review" | "blocked" | "done";
export type Priority = "low" | "medium" | "high" | "critical";
export type Risk = "low" | "medium" | "high";

export interface WorkItem {
  id: string;
  project_id: string;
  parent_id: string | null;
  type: WorkItemType;
  path: string;
  depth: number;
  title: string;
  description: string | null;
  acceptance_criteria: string | null;
  status: WorkItemStatus;
  priority: Priority;
  risk: Risk | null;
  story_points: number | null;
  estimated_hours: number | null;
  actual_hours: number | null;
  start_date: string | null;
  due_date: string | null;
  owner_id: string | null;
  reviewer_id: string | null;
  progress: number;
  progress_override: number | null;
  position: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface Comment {
  id: string;
  entity_type: string;
  entity_id: string;
  author_id: string;
  body: string;
  created_at: string;
  updated_at: string;
}

export interface Attachment {
  id: string;
  entity_type: string;
  entity_id: string;
  uploaded_by: string;
  file_name: string;
  file_url: string;
  file_size_bytes: number;
  mime_type: string;
  created_at: string;
}
