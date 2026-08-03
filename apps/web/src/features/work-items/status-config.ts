import type { Priority, WorkItemStatus, WorkItemType } from "@/lib/types";

export const STATUS_COLUMNS: { value: WorkItemStatus; label: string }[] = [
  { value: "todo", label: "To Do" },
  { value: "in_progress", label: "In Progress" },
  { value: "in_review", label: "In Review" },
  { value: "blocked", label: "Blocked" },
  { value: "done", label: "Done" },
];

export const STATUS_LABEL: Record<WorkItemStatus, string> = {
  todo: "To Do",
  in_progress: "In Progress",
  in_review: "In Review",
  blocked: "Blocked",
  done: "Done",
};

export const STATUS_BADGE_CLASS: Record<WorkItemStatus, string> = {
  todo: "bg-muted text-muted-foreground",
  in_progress: "bg-info/15 text-info",
  in_review: "bg-ai/15 text-ai",
  blocked: "bg-destructive/15 text-destructive",
  done: "bg-success/15 text-success",
};

export const PRIORITY_BADGE_CLASS: Record<Priority, string> = {
  low: "bg-muted text-muted-foreground",
  medium: "bg-info/15 text-info",
  high: "bg-warning/15 text-warning",
  critical: "bg-destructive/15 text-destructive",
};

export const TYPE_LABEL: Record<WorkItemType, string> = {
  epic: "Epic",
  feature: "Feature",
  story: "Story",
  task: "Task",
  subtask: "Subtask",
  checklist_item: "Checklist",
};
