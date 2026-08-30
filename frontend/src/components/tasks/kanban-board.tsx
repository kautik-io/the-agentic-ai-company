"use client";

import { Task } from "@/lib/api";
import { TaskKanbanCard } from "@/components/tasks/task-kanban-card";
import { cn } from "@/lib/utils";

const COLUMNS = [
  "backlog",
  "ready",
  "in_progress",
  "waiting",
  "blocked",
  "failed",
  "in_review",
  "changes_requested",
  "testing",
  "completed",
] as const;

const COLUMN_LABELS: Record<string, string> = {
  backlog: "Backlog",
  ready: "Ready",
  in_progress: "In Progress",
  waiting: "Waiting",
  blocked: "Blocked",
  failed: "Failed",
  in_review: "In Review",
  changes_requested: "Changes Requested",
  testing: "Testing",
  completed: "Done",
};

const COLUMN_ACCENT: Record<string, string> = {
  backlog: "border-t-slate-500",
  ready: "border-t-sky-500",
  in_progress: "border-t-blue-500",
  waiting: "border-t-yellow-500",
  blocked: "border-t-amber-500",
  failed: "border-t-red-500",
  in_review: "border-t-violet-500",
  changes_requested: "border-t-orange-500",
  testing: "border-t-cyan-500",
  completed: "border-t-emerald-500",
};

interface KanbanBoardProps {
  tasks: Task[];
  orgId: string;
  projectId: string;
}

export function KanbanBoard({ tasks, orgId, projectId }: KanbanBoardProps) {
  const tasksByStatus = (status: string) => tasks.filter((t) => t.status === status);

  return (
    <div className="flex h-full min-h-0 gap-3 overflow-x-auto pb-1 pt-1">
      {COLUMNS.map((col) => {
        const count = tasksByStatus(col).length;
        return (
          <section
            key={col}
            className={cn(
              "flex h-full w-[288px] shrink-0 flex-col rounded-xl border border-border/60 bg-muted/15 shadow-sm",
              "border-t-[3px]",
              COLUMN_ACCENT[col]
            )}
          >
            <header className="flex shrink-0 items-center justify-between px-3 py-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground/90">
                {COLUMN_LABELS[col]}
              </h3>
              <span className="rounded-md bg-background/80 px-2 py-0.5 text-[11px] font-medium text-muted-foreground tabular-nums">
                {count}
              </span>
            </header>

            <div className="kanban-column-scroll min-h-0 flex-1 space-y-2 overflow-y-auto px-2 pb-3">
              {count === 0 ? (
                <div className="rounded-lg border border-dashed border-border/50 px-3 py-6 text-center text-xs text-muted-foreground">
                  No tasks
                </div>
              ) : (
                tasksByStatus(col).map((task) => (
                  <TaskKanbanCard key={task.id} task={task} orgId={orgId} projectId={projectId} />
                ))
              )}
            </div>
          </section>
        );
      })}
    </div>
  );
}
