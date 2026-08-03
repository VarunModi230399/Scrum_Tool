import { apiFetch } from "@/lib/api-client";
import type {
  Attachment,
  Comment,
  ItemResponse,
  ListResponse,
  Priority,
  Risk,
  WorkItem,
  WorkItemStatus,
  WorkItemType,
} from "@/lib/types";

export function listWorkItems(projectId: string) {
  return apiFetch<ListResponse<WorkItem>>(`/projects/${projectId}/work-items`);
}

export interface CreateWorkItemBody {
  type: WorkItemType;
  title: string;
  parent_id?: string | null;
  description?: string | null;
  priority?: Priority;
  story_points?: number | null;
}

export function createWorkItem(projectId: string, body: CreateWorkItemBody) {
  return apiFetch<ItemResponse<WorkItem>>(`/projects/${projectId}/work-items`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getWorkItem(workItemId: string) {
  return apiFetch<ItemResponse<WorkItem>>(`/work-items/${workItemId}`);
}

export interface UpdateWorkItemBody {
  title?: string;
  description?: string | null;
  status?: WorkItemStatus;
  priority?: Priority;
  risk?: Risk | null;
  story_points?: number | null;
}

export function updateWorkItem(workItemId: string, body: UpdateWorkItemBody) {
  return apiFetch<ItemResponse<WorkItem>>(`/work-items/${workItemId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function deleteWorkItem(workItemId: string) {
  return apiFetch<void>(`/work-items/${workItemId}`, { method: "DELETE" });
}

export function listComments(workItemId: string) {
  return apiFetch<ListResponse<Comment>>(`/work-items/${workItemId}/comments`);
}

export function addComment(workItemId: string, body: string) {
  return apiFetch<ItemResponse<Comment>>(`/work-items/${workItemId}/comments`, {
    method: "POST",
    body: JSON.stringify({ body }),
  });
}

export function listAttachments(workItemId: string) {
  return apiFetch<ListResponse<Attachment>>(`/work-items/${workItemId}/attachments`);
}

export function uploadAttachment(workItemId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<ItemResponse<Attachment>>(`/work-items/${workItemId}/attachments`, {
    method: "POST",
    body: formData,
  });
}
