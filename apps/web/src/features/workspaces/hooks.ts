"use client";

import { useQuery } from "@tanstack/react-query";
import * as workspacesApi from "@/features/workspaces/api";
import { getAccessToken } from "@/lib/auth-tokens";

export function useMyWorkspaces() {
  return useQuery({
    queryKey: ["my-workspaces"],
    queryFn: workspacesApi.listMyWorkspaces,
    enabled: !!getAccessToken(),
    select: (res) => res.data,
  });
}
