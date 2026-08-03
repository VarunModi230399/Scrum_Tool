"use client";

import { use, useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { useCreateProject, useProjects } from "@/features/projects/hooks";
import { ApiError } from "@/lib/api-client";

const statusVariant = {
  active: "default",
  archived: "secondary",
  on_hold: "outline",
} as const;

export default function WorkspacePage({
  params,
}: {
  params: Promise<{ workspaceId: string }>;
}) {
  const { workspaceId } = use(params);
  const { data: projects, isLoading } = useProjects(workspaceId);

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold tracking-tight">Projects</h1>
          <p className="text-sm text-muted-foreground">
            Everything your workspace is working on.
          </p>
        </div>
        <CreateProjectDialog workspaceId={workspaceId} />
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading projects…</p>}

      {!isLoading && projects && projects.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-sm text-muted-foreground">
            No projects yet. Create your first one to start adding work.
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {projects?.map((project) => (
          <Link key={project.id} href={`/w/${workspaceId}/p/${project.id}`}>
            <Card className="h-full transition-colors hover:bg-accent/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="font-mono text-[10px]">
                    {project.key}
                  </Badge>
                  <Badge variant={statusVariant[project.status]}>{project.status}</Badge>
                </div>
                <CardTitle className="pt-1">{project.name}</CardTitle>
                {project.description && (
                  <CardDescription className="line-clamp-2">
                    {project.description}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent className="flex items-center gap-2">
                <Progress value={project.progress_override ?? project.progress} className="h-1.5" />
                <span className="w-9 text-right text-xs text-muted-foreground">
                  {Math.round(project.progress_override ?? project.progress)}%
                </span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}

function CreateProjectDialog({ workspaceId }: { workspaceId: string }) {
  const [open, setOpen] = useState(false);
  const [key, setKey] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const createProject = useCreateProject(workspaceId);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createProject.mutateAsync({ key, name });
      setOpen(false);
      setKey("");
      setName("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create project.");
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button size="sm" />}>
        <Plus className="size-4" />
        New project
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>New project</DialogTitle>
            <DialogDescription>
              Projects group epics, stories, and tasks under a short key (like ENG or MKT).
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-4 py-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="project-key">Key</Label>
              <Input
                id="project-key"
                placeholder="ENG"
                maxLength={10}
                required
                value={key}
                onChange={(e) => setKey(e.target.value.toUpperCase())}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="project-name">Name</Label>
              <Input
                id="project-name"
                placeholder="Engineering"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
          <DialogFooter>
            <DialogClose render={<Button type="button" variant="outline" />}>Cancel</DialogClose>
            <Button type="submit" disabled={createProject.isPending}>
              {createProject.isPending ? "Creating…" : "Create project"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
