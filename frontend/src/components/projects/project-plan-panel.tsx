"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ProjectPlan } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { StatusBadge } from "@/components/ui/badge";
import { CheckCircle2, RefreshCw, Plus, ClipboardList } from "lucide-react";

interface Props {
  orgId: string;
  projectId: string;
}

const PHASE_COLORS: Record<string, string> = {
  design: "text-blue-400",
  build: "text-green-400",
  test: "text-yellow-400",
  fix: "text-orange-400",
  approval: "text-purple-400",
  manual: "text-cyan-400",
};

export function ProjectPlanPanel({ orgId, projectId }: Props) {
  const [plan, setPlan] = useState<ProjectPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);
  const [manualTitle, setManualTitle] = useState("");
  const [showManual, setShowManual] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    api.getProjectPlan(orgId, projectId)
      .then(setPlan)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(load, [orgId, projectId]);

  const handleApprove = async () => {
    if (!plan || !window.confirm(`Approve plan and create ${plan.total_tasks} tasks?`)) return;
    setActing(true);
    setMessage(null);
    try {
      const result = await api.approveProjectPlan(orgId, projectId);
      setMessage(result.message);
      load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setActing(false);
    }
  };

  const handleRegenerate = async () => {
    setActing(true);
    try {
      await api.regenerateProjectPlan(orgId, projectId);
      load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Regenerate failed");
    } finally {
      setActing(false);
    }
  };

  const handleAddManual = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualTitle.trim()) return;
    setActing(true);
    try {
      await api.addManualPlanTask(orgId, projectId, { title: manualTitle.trim() });
      setManualTitle("");
      setShowManual(false);
      load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Failed to add task");
    } finally {
      setActing(false);
    }
  };

  if (loading || !plan) return null;

  if (plan.planning_status === "approved") {
    return (
      <Card className="border-green-500/30 bg-green-500/5">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-green-400" />
            Plan approved
          </CardTitle>
          <CardDescription>
            PM auto-planned and started the build pipeline.{" "}
            <Link href={`/tasks?project=${projectId}`} className="text-primary hover:underline">
              View Kanban →
            </Link>
            {" · "}
            <Link href="/system-design" className="text-primary hover:underline">
              System Design →
            </Link>
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (plan.planning_status === "none" || plan.planning_status === "rejected") {
    return (
      <Card className="border-border">
        <CardHeader>
          <CardTitle className="text-base">No task plan yet</CardTitle>
          <CardDescription>
            Generate an auto-plan from project requirements — PM starts the pipeline automatically.
          </CardDescription>
          {message && <p className="text-sm text-red-400 mt-2">{message}</p>}
          <Button size="sm" className="mt-2 w-fit" onClick={handleRegenerate} disabled={acting}>
            <RefreshCw className="h-4 w-4 mr-1" /> Generate Plan
          </Button>
        </CardHeader>
      </Card>
    );
  }

  const allTasks = [...plan.tasks, ...plan.manual_tasks];

  return (
    <Card className="border-amber-500/30 bg-amber-500/5">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="text-base flex items-center gap-2">
              <ClipboardList className="h-4 w-4" />
              Auto Plan — PM Review (optional approve)
            </CardTitle>
            <CardDescription className="mt-1">
              {plan.summary || `${plan.total_tasks} tasks planned`}
            </CardDescription>
            <div className="mt-2">
              <StatusBadge status={plan.planning_status} />
            </div>
          </div>
          <div className="flex gap-2 flex-wrap">
            <Button size="sm" onClick={handleApprove} disabled={acting}>
              <CheckCircle2 className="h-4 w-4 mr-1" /> Approve Plan
            </Button>
            <Button size="sm" variant="outline" onClick={handleRegenerate} disabled={acting}>
              <RefreshCw className="h-4 w-4 mr-1" /> Regenerate
            </Button>
            <Button size="sm" variant="outline" onClick={() => setShowManual(!showManual)}>
              <Plus className="h-4 w-4 mr-1" /> Add Task
            </Button>
          </div>
        </div>
      </CardHeader>

      {message && (
        <div className="mx-6 mb-4 rounded-lg border border-border bg-muted px-3 py-2 text-sm">{message}</div>
      )}

      {showManual && (
        <form onSubmit={handleAddManual} className="mx-6 mb-4 flex gap-2">
          <Input
            value={manualTitle}
            onChange={(e) => setManualTitle(e.target.value)}
            placeholder="Manual task title..."
            className="flex-1"
            required
          />
          <Button type="submit" disabled={acting}>Add</Button>
        </form>
      )}

      <div className="px-6 pb-6 max-h-80 overflow-y-auto space-y-1">
        <p className="text-xs text-muted-foreground mb-2">
          Each feature gets design → build → test → fix tasks. New projects auto-start; use Approve to launch manually.
        </p>
        {allTasks.map((t, i) => (
          <div key={i} className="flex items-start gap-2 text-sm py-1 border-b border-border/50 last:border-0">
            <span className={`text-xs uppercase w-14 shrink-0 ${PHASE_COLORS[t.phase] || "text-muted-foreground"}`}>
              {t.task_type || t.phase}
            </span>
            <span className="flex-1">{t.title}</span>
            <span className="text-xs text-muted-foreground shrink-0">{t.agent_role}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}
