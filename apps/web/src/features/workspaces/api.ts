import { apiFetch } from "@/lib/api-client";
import type { ListResponse, MyWorkspace } from "@/lib/types";

export function listMyWorkspaces() {
  return apiFetch<ListResponse<MyWorkspace>>("/me/workspaces");
}
