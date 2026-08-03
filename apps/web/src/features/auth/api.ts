import { apiFetch } from "@/lib/api-client";
import type { AuthResponse, ItemResponse, User } from "@/lib/types";

export function register(body: { email: string; password: string; full_name: string }) {
  return apiFetch<ItemResponse<AuthResponse>>("/auth/register", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function login(body: { email: string; password: string }) {
  return apiFetch<ItemResponse<AuthResponse>>("/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function me() {
  return apiFetch<ItemResponse<User>>("/auth/me");
}

export function logout(refreshToken: string) {
  return apiFetch<void>("/auth/logout", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}
