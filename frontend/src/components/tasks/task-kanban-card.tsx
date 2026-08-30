"use client";

import { AlertCircle, AlertTriangle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import { StatusBadge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Task } from "@/lib/api";

function getStuckReason(task: Task): { type: "blocked" | "failed" | "waiting"; message: string } | null {
  if (task.status === "blocked" && task.blocked_reason) {
    return { type: "blocked", message: task.blocked_reason };
  }
  if (task.status === "failed" && task.failure_reason) {
    return { type: "failed", message: task.failure_reason };
  }
  if (task.status === "blocked" && !task.blocked_reason) {
    return { type: "blocked", message: "Task is blocked — no reason recorded yet." };
  }
  if (task.status === "failed" && !task.failure_reason) {
    return { type: "failed", message: "Task failed — no error details recorded yet." };
  }
  if (task.status === "waiting") {
    return { type: "waiting", message: "Waiting on a dependency or another agent to finish." };
  }
  if (task.status === "changes_requested") {
    return { type: "blocked", message: "Changes requested — review feedback and retry." };
  }
  return null;
}

interface TaskKanbanCardProps {
  task: Task;
}

export function TaskKanbanCard({ task }: TaskKanbanCardProps) {
  const stuck = getStuckReason(task);
  const isStuck = task.status === "blocked" || task.status === "failed" || task.status === "waiting";

  const borderClass =
    task.status === "failed"
      ? "border-red-500/60 bg-red-500/5"
      : task.status === "blocked"
        ? "border-amber-500/60 bg-amber-500/5"
        : task.status === "waiting"
          ? "border-yellow-500/40 bg-yellow-500/5"
          : "border-border";

  const Icon =
    task.status === "failed" ? AlertCircle : task.status === "blocked" ? AlertTriangle : Clock;

  const iconClass =
    task.status === "failed"
      ? "text-red-400"
      : task.status === "blocked"
        ? "text-amber-400"
        : "text-yellow-400";

  return (
    <div className="group relative">
      <Card className={cn("p-4 transition-shadow", borderClass, isStuck && "cursor-help")}>
        <div className="flex items-start justify-between gap-2">
          <p className="text-xs text-muted-foreground mb-1">TASK-{task.task_number}</p>
          {isStuck && <Icon className={cn("h-4 w-4 flex-shrink-0", iconClass)} aria-hidden />}
        </div>
        <p className="font-medium text-sm">{task.title}</p>

        {stuck && (
          <p className="mt-2 text-xs text-red-400/90 line-clamp-2 md:hidden">{stuck.message}</p>
        )}

        <div className="mt-2 flex items-center justify-between">
          <StatusBadge status={task.priority} />
          <StatusBadge status={task.status} />
        </div>

        {(task.retry_count ?? 0) > 0 && (
          <p className="mt-1.5 text-xs text-muted-foreground">Retries: {task.retry_count}</p>
        )}
      </Card>

      {stuck && (
        <div
          role="tooltip"
          className={cn(
            "pointer-events-none absolute left-1/2 z-50 hidden w-72 max-w-[calc(100vw-2rem)] -translate-x-1/2 rounded-lg border px-3 py-2 text-xs shadow-xl",
            "group-hover:block group-focus-within:block",
            "bottom-full mb-2",
            stuck.type === "failed"
              ? "border-red-500/40 bg-red-950 text-red-100"
              : stuck.type === "blocked"
                ? "border-amber-500/40 bg-amber-950 text-amber-100"
                : "border-yellow-500/40 bg-yellow-950 text-yellow-100"
          )}
        >
          <p className="font-semibold mb-1 uppercase tracking-wide">
            {stuck.type === "failed" ? "Error" : stuck.type === "blocked" ? "Blocked" : "Waiting"}
          </p>
          <p className="leading-relaxed">{stuck.message}</p>
          <span
            className={cn(
              "absolute -bottom-1.5 left-1/2 h-3 w-3 -translate-x-1/2 rotate-45 border-r border-b",
              stuck.type === "failed"
                ? "border-red-500/40 bg-red-950"
                : stuck.type === "blocked"
                  ? "border-amber-500/40 bg-amber-950"
                  : "border-yellow-500/40 bg-yellow-950"
            )}
          />
        </div>
      )}
    </div>
  );
}
