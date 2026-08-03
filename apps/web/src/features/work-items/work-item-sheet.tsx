"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import {
  useAddComment,
  useComments,
  useDeleteWorkItem,
  useUpdateWorkItem,
  useWorkItem,
} from "@/features/work-items/hooks";
import { PRIORITY_BADGE_CLASS, STATUS_COLUMNS, TYPE_LABEL } from "@/features/work-items/status-config";
import type { Priority, WorkItemStatus } from "@/lib/types";

const PRIORITIES: Priority[] = ["low", "medium", "high", "critical"];

export function WorkItemSheet({
  workItemId,
  projectId,
  onClose,
}: {
  workItemId: string | null;
  projectId: string;
  onClose: () => void;
}) {
  const { data: workItem } = useWorkItem(workItemId);
  const updateWorkItem = useUpdateWorkItem(projectId);
  const deleteWorkItem = useDeleteWorkItem(projectId);
  const { data: comments } = useComments(workItemId);
  const addComment = useAddComment(workItemId ?? "");
  const [commentBody, setCommentBody] = useState("");

  async function handleDelete() {
    if (!workItemId) return;
    if (!confirm("Delete this work item and everything under it?")) return;
    await deleteWorkItem.mutateAsync(workItemId);
    onClose();
  }

  async function handleAddComment(e: React.FormEvent) {
    e.preventDefault();
    if (!commentBody.trim() || !workItemId) return;
    await addComment.mutateAsync(commentBody);
    setCommentBody("");
  }

  return (
    <Sheet open={!!workItemId} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="flex w-full flex-col sm:max-w-md">
        {workItem && (
          <>
            <SheetHeader>
              <Badge variant="outline" className="w-fit text-[10px]">
                {TYPE_LABEL[workItem.type]}
              </Badge>
              <SheetTitle>{workItem.title}</SheetTitle>
              {workItem.description && (
                <SheetDescription>{workItem.description}</SheetDescription>
              )}
            </SheetHeader>

            <div className="flex flex-col gap-4 overflow-y-auto px-4">
              <div className="flex items-center gap-3">
                <Select
                  value={workItem.status}
                  onValueChange={(value) =>
                    updateWorkItem.mutate({
                      id: workItem.id,
                      body: { status: value as WorkItemStatus },
                    })
                  }
                >
                  <SelectTrigger size="sm">
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

                <Select
                  value={workItem.priority}
                  onValueChange={(value) =>
                    updateWorkItem.mutate({
                      id: workItem.id,
                      body: { priority: value as Priority },
                    })
                  }
                >
                  <SelectTrigger size="sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PRIORITIES.map((p) => (
                      <SelectItem key={p} value={p}>
                        <span className={`rounded px-1.5 py-0.5 text-xs ${PRIORITY_BADGE_CLASS[p]}`}>
                          {p}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>Progress</span>
                <span className="font-medium text-foreground">
                  {Math.round(workItem.progress_override ?? workItem.progress)}%
                </span>
                {workItem.story_points != null && <span>· {workItem.story_points} pts</span>}
              </div>

              <div className="flex flex-col gap-2">
                <p className="text-xs font-medium text-muted-foreground">Comments</p>
                <div className="flex flex-col gap-3">
                  {comments?.length === 0 && (
                    <p className="text-xs text-muted-foreground">No comments yet.</p>
                  )}
                  {comments?.map((comment) => (
                    <div key={comment.id} className="rounded-lg bg-muted/50 p-2.5 text-sm">
                      <p>{comment.body}</p>
                      <p className="mt-1 text-[11px] text-muted-foreground">
                        {new Date(comment.created_at).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
                <form onSubmit={handleAddComment} className="flex flex-col gap-2">
                  <Textarea
                    placeholder="Add a comment…"
                    value={commentBody}
                    onChange={(e) => setCommentBody(e.target.value)}
                    rows={2}
                  />
                  <Button
                    type="submit"
                    size="sm"
                    className="self-end"
                    disabled={!commentBody.trim() || addComment.isPending}
                  >
                    Comment
                  </Button>
                </form>
              </div>
            </div>

            <SheetFooter>
              <Button variant="destructive" size="sm" onClick={handleDelete}>
                Delete work item
              </Button>
            </SheetFooter>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
