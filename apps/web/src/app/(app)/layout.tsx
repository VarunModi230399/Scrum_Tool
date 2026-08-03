"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AppHeader } from "@/components/shared/app-header";
import { useCurrentUser } from "@/features/auth/hooks";
import { getAccessToken } from "@/lib/auth-tokens";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { data: user, isError } = useCurrentUser();

  useEffect(() => {
    if (!getAccessToken() || isError) {
      router.replace("/login");
    }
  }, [isError, router]);

  if (!getAccessToken()) {
    return null;
  }

  return (
    <div className="flex min-h-screen flex-col">
      <AppHeader user={user} />
      <main className="flex-1">{children}</main>
    </div>
  );
}
