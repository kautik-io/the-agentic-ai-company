"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, Project, Task } from "@/lib/api";
import { TaskKanbanCard } from "@/components/tasks/task-kanban-card";
import { Select } from "@/components/ui/input";
import { AlertTriangle } from "lucide-react";

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
];

export default function TasksPage() {
  const { org } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [tasks, setTasks] = useState<Task[]>([]);

  useEffect(() => {
    if (!org) return;
    api.listProjects(org.id).then((p) => {
      setProjects(p);
      if (p.length > 0) setSelectedProject(p[0].id);
    });
  }, [org]);

  useEffect(() => {
    if (!org || !selectedProject) return;
    api.listTasks(org.id, selectedProject).then(setTasks).catch(console.error);
  }, [org, selectedProject]);

  const tasksByStatus = (status: string) => tasks.filter((t) => t.status === status);

  const stuckTasks = tasks.filter(
    (t) => t.status === "blocked" || t.status === "failed" || t.status === "waiting"
  );

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Tasks</h1>
          <p className="text-muted-foreground">
            Hover blocked, failed, or waiting tasks to see why they&apos;re stuck
          </p>
        </div>
        {projects.length > 0 && (
          <Select value={selectedProject} onChange={(e) => setSelectedProject(e.target.value)}>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </Select>
        )}
      </div>

      {stuckTasks.length > 0 && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-amber-200">
              {stuckTasks.length} task{stuckTasks.length !== 1 ? "s" : ""} need attention
            </p>
            <p className="text-muted-foreground mt-0.5">
              {stuckTasks.map((t) => `TASK-${t.task_number}`).join(", ")} — hover the card for details
            </p>
          </div>
        </div>
      )}

      <div className="flex gap-4 overflow-x-auto overflow-y-visible pb-8 pt-2">
        {COLUMNS.map((col) => (
          <div key={col} className="min-w-[260px] flex-shrink-0 overflow-visible">
            <h3 className="text-sm font-medium uppercase tracking-wide text-muted-foreground mb-3">
              {col.replace(/_/g, " ")}
              <span className="ml-2 rounded-full bg-muted px-2 py-0.5 text-xs">
                {tasksByStatus(col).length}
              </span>
            </h3>
            <div className="space-y-2">
              {tasksByStatus(col).map((task) => (
                <TaskKanbanCard key={task.id} task={task} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
