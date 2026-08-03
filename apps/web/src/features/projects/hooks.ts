"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as projectsApi from "@/features/projects/api";

export function useProjects(workspaceId: string) {
  return useQuery({
    queryKey: ["projects", workspaceId],
    queryFn: () => projectsApi.listProjects(workspaceId),
    select: (res) => res.data,
    enabled: !!workspaceId,
  });
}

export function useProject(projectId: string) {
  return useQuery({
    queryKey: ["project", projectId],
    queryFn: () => projectsApi.getProject(projectId),
    select: (res) => res.data,
    enabled: !!projectId,
  });
}

export function useCreateProject(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { key: string; name: string; description?: string }) =>
      projectsApi.createProject(workspaceId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", workspaceId] });
    },
  });
}
