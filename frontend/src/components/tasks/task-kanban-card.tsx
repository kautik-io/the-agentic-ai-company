"use client";

import { useCallback, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { AlertCircle, AlertTriangle, Clock, Terminal } from "lucide-react";
import { cn } from "@/lib/utils";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Task } from "@/lib/api";
import { TaskScreenshotThumb } from "@/components/tasks/task-complete-button";
import { TaskExecutionLogsPanel } from "@/components/tasks/task-execution-logs";

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
  orgId: string;
  projectId: string;
}

export function TaskKanbanCard({ task, orgId, projectId }: TaskKanbanCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState<{ top: number; left: number; above: boolean } | null>(null);
  const [showLogs, setShowLogs] = useState(false);
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

  const showTooltip = useCallback(() => {
    const rect = cardRef.current?.getBoundingClientRect();
    if (!rect || !stuck) return;
    const above = rect.top > 140;
    setTooltip({
      top: above ? rect.top - 8 : rect.bottom + 8,
      left: rect.left + rect.width / 2,
      above,
    });
  }, [stuck]);

  const hideTooltip = useCallback(() => setTooltip(null), []);

  const tooltipColors =
    stuck?.type === "failed"
      ? "border-red-500/40 bg-red-950 text-red-100"
      : stuck?.type === "blocked"
        ? "border-amber-500/40 bg-amber-950 text-amber-100"
        : "border-yellow-500/40 bg-yellow-950 text-yellow-100";

  return (
    <>
      <div
        ref={cardRef}
        className="relative"
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
      >
        <Card className={cn("p-3 transition-all hover:shadow-md hover:border-border/80", borderClass, isStuck && "cursor-help")}>
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

          <Button
            variant="ghost"
            size="sm"
            className="mt-2 h-7 w-full justify-start px-2 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => setShowLogs(true)}
          >
            <Terminal className="h-3 w-3 mr-1.5" />
            Logs
            {task.status === "in_progress" && (
              <span className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            )}
          </Button>

          {task.status === "completed" && task.screenshots && task.screenshots.length > 0 && (
            <>
              <TaskScreenshotThumb
                url={task.screenshots[0].url}
                title={task.screenshots[0].caption || task.title}
              />
              {task.screenshots.length > 1 && (
                <p className="mt-1 text-[10px] text-muted-foreground">
                  +{task.screenshots.length - 1} more screenshot{task.screenshots.length > 2 ? "s" : ""}
                </p>
              )}
            </>
          )}
        </Card>
      </div>

      {stuck && tooltip && typeof document !== "undefined" &&
        createPortal(
          <div
            role="tooltip"
            className={cn(
              "pointer-events-none fixed z-[9999] w-72 max-w-[calc(100vw-2rem)] -translate-x-1/2 rounded-lg border px-3 py-2 text-xs shadow-xl",
              tooltipColors
            )}
            style={{
              top: tooltip.above ? tooltip.top : tooltip.top,
              left: tooltip.left,
              transform: tooltip.above
                ? "translate(-50%, -100%)"
                : "translate(-50%, 0)",
            }}
          >
            <p className="font-semibold mb-1 uppercase tracking-wide">
              {stuck.type === "failed" ? "Error" : stuck.type === "blocked" ? "Blocked" : "Waiting"}
            </p>
            <p className="leading-relaxed">{stuck.message}</p>
          </div>,
          document.body
        )}

      {showLogs && (
        <TaskExecutionLogsPanel
          orgId={orgId}
          projectId={projectId}
          task={task}
          onClose={() => setShowLogs(false)}
        />
      )}
    </>
  );
}
