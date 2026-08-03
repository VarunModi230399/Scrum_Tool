"use client";

import { use, useState } from "react";
import { Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useProject } from "@/features/projects/hooks";
import {
  PRIORITY_BADGE_CLASS,
  STATUS_BADGE_CLASS,
  STATUS_COLUMNS,
  TYPE_LABEL,
} from "@/features/work-items/status-config";
import { useCreateWorkItem, useUpdateWorkItem, useWorkItems } from "@/features/work-items/hooks";
import { WorkItemSheet } from "@/features/work-items/work-item-sheet";
import { ApiError } from "@/lib/api-client";
import type { WorkItem, WorkItemStatus, WorkItemType } from "@/lib/types";

export default function ProjectPage({
  params,
}: {
  params: Promise<{ workspaceId: string; projectId: string }>;
}) {
  const { projectId } = use(params);
  const { data: project } = useProject(projectId);
  const { data: workItems, isLoading } = useWorkItems(projectId);
  const updateWorkItem = useUpdateWorkItem(projectId);
  const [openWorkItemId, setOpenWorkItemId] = useState<string | null>(null);

  const columns = STATUS_COLUMNS.map((column) => ({
    ...column,
    items: (workItems ?? []).filter((w) => w.status === column.value),
  }));

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col">
      <div className="flex items-center justify-between border-b px-6 py-4">
        <div>
          <div className="flex items-center gap-2">
            {project && (
              <Badge variant="outline" className="font-mono text-[10px]">
                {project.key}
              </Badge>
            )}
            <h1 className="text-lg font-semibold tracking-tight">{project?.name}</h1>
          </div>
          {project && (
            <div className="mt-1 flex items-center gap-2">
              <Progress
                value={project.progress_override ?? project.progress}
                className="h-1.5 w-32"
              />
              <span className="text-xs text-muted-foreground">
                {Math.round(project.progress_override ?? project.progress)}% complete
              </span>
            </div>
          )}
        </div>
        <CreateWorkItemDialog projectId={projectId} workItems={workItems ?? []} />
      </div>

      {isLoading && <p className="px-6 py-4 text-sm text-muted-foreground">Loading…</p>}

      <div className="flex flex-1 gap-4 overflow-x-auto p-6">
        {columns.map((column) => (
          <div key={column.value} className="flex w-72 shrink-0 flex-col gap-3">
            <div className="flex items-center justify-between px-1">
              <h2 className="text-sm font-medium">{column.label}</h2>
              <span className="text-xs text-muted-foreground">{column.items.length}</span>
            </div>
            <div className="flex flex-1 flex-col gap-2">
              {column.items.map((item) => (
                <WorkItemCard
                  key={item.id}
                  item={item}
                  onOpen={() => setOpenWorkItemId(item.id)}
                  onStatusChange={(status) =>
                    updateWorkItem.mutate({ id: item.id, body: { status } })
                  }
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      <WorkItemSheet
        workItemId={openWorkItemId}
        projectId={projectId}
        onClose={() => setOpenWorkItemId(null)}
      />
    </div>
  );
}

function WorkItemCard({
  item,
  onOpen,
  onStatusChange,
}: {
  item: WorkItem;
  onOpen: () => void;
  onStatusChange: (status: WorkItemStatus) => void;
}) {
  return (
    <Card size="sm" className="cursor-pointer gap-2 transition-colors hover:bg-accent/50">
      <CardContent onClick={onOpen}>
        <div className="mb-1.5 flex items-center gap-1.5">
          <Badge variant="outline" className="text-[10px]">
            {TYPE_LABEL[item.type]}
          </Badge>
          <Badge className={`text-[10px] ${PRIORITY_BADGE_CLASS[item.priority]}`}>
            {item.priority}
          </Badge>
        </div>
        <p className="text-sm leading-snug font-medium">{item.title}</p>
        {item.story_points != null && (
          <p className="mt-1 text-xs text-muted-foreground">{item.story_points} pts</p>
        )}
      </CardContent>
      <CardContent className="pt-0">
        <Select value={item.status} onValueChange={(v) => onStatusChange(v as WorkItemStatus)}>
          <SelectTrigger
            size="sm"
            className={`w-full ${STATUS_BADGE_CLASS[item.status]}`}
            onClick={(e) => e.stopPropagation()}
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUS_COLUMNS.map((s) => (
              <SelectItem key={s.value} value={s.value}>
                {s.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </CardContent>
    </Card>
  );
}

const WORK_ITEM_TYPES: WorkItemType[] = [
  "epic",
  "feature",
  "story",
  "task",
  "subtask",
  "checklist_item",
];

function CreateWorkItemDialog({
  projectId,
  workItems,
}: {
  projectId: string;
  workItems: WorkItem[];
}) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [type, setType] = useState<WorkItemType>("task");
  const [parentId, setParentId] = useState<string>("none");
  const [error, setError] = useState<string | null>(null);
  const createWorkItem = useCreateWorkItem(projectId);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createWorkItem.mutateAsync({
        title,
        type,
        parent_id: parentId === "none" ? null : parentId,
      });
      setOpen(false);
      setTitle("");
      setType("task");
      setParentId("none");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create work item.");
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button size="sm" />}>
        <Plus className="size-4" />
        New work item
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>New work item</DialogTitle>
            <DialogDescription>Add an epic, story, task, or checklist item.</DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-4 py-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="work-item-title">Title</Label>
              <Input
                id="work-item-title"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label>Type</Label>
              <Select value={type} onValueChange={(v) => setType(v as WorkItemType)}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {WORK_ITEM_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>
                      {TYPE_LABEL[t]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {workItems.length > 0 && (
              <div className="flex flex-col gap-2">
                <Label>Parent (optional)</Label>
                <Select value={parentId} onValueChange={(v) => setParentId(v ?? "none")}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    {workItems.map((w) => (
                      <SelectItem key={w.id} value={w.id}>
                        {TYPE_LABEL[w.type]}: {w.title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
          <DialogFooter>
            <DialogClose render={<Button type="button" variant="outline" />}>Cancel</DialogClose>
            <Button type="submit" disabled={createWorkItem.isPending}>
              {createWorkItem.isPending ? "Creating…" : "Create"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
