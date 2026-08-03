"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useMyWorkspaces } from "@/features/workspaces/hooks";

export default function HomePage() {
  const router = useRouter();
  const { data: workspaces, isSuccess } = useMyWorkspaces();

  useEffect(() => {
    if (isSuccess && workspaces.length > 0) {
      router.replace(`/w/${workspaces[0].id}`);
    }
  }, [isSuccess, workspaces, router]);

  return (
    <div className="flex flex-1 items-center justify-center py-24 text-sm text-muted-foreground">
      Loading your workspace…
    </div>
  );
}
