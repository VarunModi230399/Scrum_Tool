"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as workItemsApi from "@/features/work-items/api";
import type { CreateWorkItemBody, UpdateWorkItemBody } from "@/features/work-items/api";

export function useWorkItems(projectId: string) {
  return useQuery({
    queryKey: ["work-items", projectId],
    queryFn: () => workItemsApi.listWorkItems(projectId),
    select: (res) => res.data,
    enabled: !!projectId,
  });
}

export function useWorkItem(workItemId: string | null) {
  return useQuery({
    queryKey: ["work-item", workItemId],
    queryFn: () => workItemsApi.getWorkItem(workItemId as string),
    select: (res) => res.data,
    enabled: !!workItemId,
  });
}

// Creating, updating, or deleting a work item can change the project's rolled-up
// progress (see ProgressRollupService server-side), so every mutation here also
// invalidates the project query — not just the work-items list.

export function useCreateWorkItem(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateWorkItemBody) => workItemsApi.createWorkItem(projectId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["work-items", projectId] });
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    },
  });
}

export function useUpdateWorkItem(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateWorkItemBody }) =>
      workItemsApi.updateWorkItem(id, body),
    onSuccess: (_res, variables) => {
      queryClient.invalidateQueries({ queryKey: ["work-items", projectId] });
      queryClient.invalidateQueries({ queryKey: ["work-item", variables.id] });
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    },
  });
}

export function useDeleteWorkItem(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workItemsApi.deleteWorkItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["work-items", projectId] });
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    },
  });
}

export function useComments(workItemId: string | null) {
  return useQuery({
    queryKey: ["comments", workItemId],
    queryFn: () => workItemsApi.listComments(workItemId as string),
    select: (res) => res.data,
    enabled: !!workItemId,
  });
}

export function useAddComment(workItemId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) => workItemsApi.addComment(workItemId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["comments", workItemId] });
    },
  });
}

export function useAttachments(workItemId: string | null) {
  return useQuery({
    queryKey: ["attachments", workItemId],
    queryFn: () => workItemsApi.listAttachments(workItemId as string),
    select: (res) => res.data,
    enabled: !!workItemId,
  });
}

export function useUploadAttachment(workItemId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => workItemsApi.uploadAttachment(workItemId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attachments", workItemId] });
    },
  });
}
