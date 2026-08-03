"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import * as authApi from "@/features/auth/api";
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "@/lib/auth-tokens";

export function useCurrentUser() {
  return useQuery({
    queryKey: ["me"],
    queryFn: authApi.me,
    enabled: !!getAccessToken(),
    select: (res) => res.data,
    retry: false,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (res) => {
      setTokens(res.data.access_token, res.data.refresh_token);
      queryClient.invalidateQueries();
    },
  });
}

export function useRegister() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: authApi.register,
    onSuccess: (res) => {
      setTokens(res.data.access_token, res.data.refresh_token);
      queryClient.invalidateQueries();
    },
  });
}

export function useLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();
  return () => {
    const refreshToken = getRefreshToken();
    clearTokens();
    queryClient.clear();
    router.push("/login");
    if (refreshToken) {
      authApi.logout(refreshToken).catch(() => {
        // best-effort server-side revocation; tokens are already cleared client-side
      });
    }
  };
}
