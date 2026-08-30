"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, Project, Task } from "@/lib/api";
import { KanbanBoard } from "@/components/tasks/kanban-board";
import { ErrorBanner } from "@/components/ui/error-banner";
import { PageLoader } from "@/components/ui/page-loader";
import { Select } from "@/components/ui/input";
import { AlertTriangle, LayoutGrid } from "lucide-react";

export default function TasksPage() {
  const { org } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [fetchingProjects, setFetchingProjects] = useState(true);
  const [fetchingTasks, setFetchingTasks] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!org) return;
    setFetchingProjects(true);
    setError(null);
    api.listProjects(org.id)
      .then((p) => {
        setProjects(p);
        if (p.length > 0) setSelectedProject(p[0].id);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load projects"))
      .finally(() => setFetchingProjects(false));
  }, [org]);

  useEffect(() => {
    if (!org || !selectedProject) return;
    setFetchingTasks(true);
    setError(null);
    api.listTasks(org.id, selectedProject)
      .then(setTasks)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load tasks"))
      .finally(() => setFetchingTasks(false));
  }, [org, selectedProject]);

  const stuckTasks = tasks.filter(
    (t) => t.status === "blocked" || t.status === "failed" || t.status === "waiting"
  );

  if (fetchingProjects) {
    return <PageLoader label="Loading projects..." />;
  }

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      <div className="shrink-0 border-b border-border/60 bg-card/30 px-6 py-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <LayoutGrid className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">Task Board</h1>
              <p className="text-sm text-muted-foreground">
                Trello-style columns — scroll cards inside each lane
              </p>
            </div>
          </div>
          {projects.length > 0 && (
            <Select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="min-w-[220px]"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </Select>
          )}
        </div>

        {error && <div className="mt-4"><ErrorBanner message={error} /></div>}

        {!fetchingTasks && stuckTasks.length > 0 && (
          <div className="mt-4 flex items-start gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-400" />
            <div className="text-sm">
              <p className="font-medium text-amber-200">
                {stuckTasks.length} task{stuckTasks.length !== 1 ? "s" : ""} need attention
              </p>
              <p className="mt-0.5 text-muted-foreground">
                {stuckTasks.map((t) => `TASK-${t.task_number}`).join(", ")} — hover a card for details
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-hidden px-4 py-4">
        {fetchingTasks ? (
          <PageLoader label="Loading tasks..." />
        ) : (
          <KanbanBoard tasks={tasks} orgId={org!.id} projectId={selectedProject} />
        )}
      </div>
    </div>
  );
}
