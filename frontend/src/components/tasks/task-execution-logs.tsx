"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Terminal, X } from "lucide-react";
import { api, Task, TaskExecutionLogEntry } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

function levelColor(level: string) {
  switch (level) {
    case "cmd":
      return "text-cyan-300";
    case "success":
      return "text-emerald-400";
    case "error":
      return "text-red-400";
    default:
      return "text-zinc-300";
  }
}

function formatTime(ts: string) {
  try {
    return new Date(ts).toLocaleTimeString();
  } catch {
    return ts;
  }
}

interface TaskExecutionLogsPanelProps {
  orgId: string;
  projectId: string;
  task: Task;
  onClose: () => void;
}

export function TaskExecutionLogsPanel({
  orgId,
  projectId,
  task,
  onClose,
}: TaskExecutionLogsPanelProps) {
  const [logs, setLogs] = useState<TaskExecutionLogEntry[]>([]);
  const [live, setLive] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [agentName, setAgentName] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const fetchLogs = useCallback(async () => {
    try {
      const data = await api.getTaskExecutionLogs(orgId, projectId, task.id);
      const allLogs = data.runs.flatMap((run) => run.logs);
      setLogs(allLogs);
      setLive(data.live || task.status === "in_progress");
      setAgentName(data.runs[0]?.agent_name ?? null);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load logs");
    } finally {
      setLoading(false);
    }
  }, [orgId, projectId, task.id, task.status]);

  useEffect(() => {
    setLoading(true);
    fetchLogs();
  }, [fetchLogs]);

  useEffect(() => {
    const polling = live || task.status === "in_progress";
    if (!polling) return;
    const id = setInterval(fetchLogs, 2000);
    return () => clearInterval(id);
  }, [live, task.status, fetchLogs]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [logs]);

  return (
    <div className="fixed inset-0 z-[10000] flex items-center justify-center bg-black/60 p-4">
      <div className="flex h-[min(80vh,640px)] w-full max-w-3xl flex-col overflow-hidden rounded-xl border border-border bg-card shadow-2xl">
        <header className="flex shrink-0 items-center justify-between border-b border-border px-4 py-3">
          <div className="flex items-center gap-2 min-w-0">
            <Terminal className="h-4 w-4 text-primary shrink-0" />
            <div className="min-w-0">
              <p className="text-sm font-semibold truncate">
                TASK-{task.task_number} — Live execution
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {agentName ? `${agentName} · ` : ""}
                {task.title}
                {(live || task.status === "in_progress") && (
                  <span className="ml-2 inline-flex items-center gap-1 text-emerald-400">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    live
                  </span>
                )}
              </p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close logs">
            <X className="h-4 w-4" />
          </Button>
        </header>

        <div
          ref={scrollRef}
          className="min-h-0 flex-1 overflow-y-auto bg-zinc-950 p-4 font-mono text-xs leading-relaxed"
        >
          {loading && logs.length === 0 ? (
            <div className="flex items-center gap-2 text-zinc-500">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading execution logs…
            </div>
          ) : error ? (
            <p className="text-red-400">{error}</p>
          ) : logs.length === 0 ? (
            <div className="space-y-2 text-zinc-500">
              <p>No execution logs yet.</p>
              <p className="text-zinc-600">
                When an agent runs this task you will see LLM calls, file writes to SSH, tests, and validation here.
              </p>
            </div>
          ) : (
            logs.map((entry, i) => (
              <div key={`${entry.ts}-${i}`} className="flex gap-2 py-0.5">
                <span className="shrink-0 text-zinc-600 select-none">{formatTime(entry.ts)}</span>
                <span className={cn("whitespace-pre-wrap break-all", levelColor(entry.level))}>
                  {entry.message}
                </span>
              </div>
            ))
          )}
        </div>

        <footer className="shrink-0 border-t border-border px-4 py-2 text-[11px] text-muted-foreground">
          Real backend process — agent LLM calls, workspace writes, SSH tests. Refreshes every 2s while running.
        </footer>
      </div>
    </div>
  );
}
