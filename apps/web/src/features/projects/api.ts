import { apiFetch } from "@/lib/api-client";
import type { ItemResponse, ListResponse, Project } from "@/lib/types";

export function listProjects(workspaceId: string) {
  return apiFetch<ListResponse<Project>>(`/workspaces/${workspaceId}/projects`);
}

export function createProject(
  workspaceId: string,
  body: { key: string; name: string; description?: string },
) {
  return apiFetch<ItemResponse<Project>>(`/workspaces/${workspaceId}/projects`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getProject(projectId: string) {
  return apiFetch<ItemResponse<Project>>(`/projects/${projectId}`);
}
