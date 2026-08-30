"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, Agent, Activity, DashboardStats } from "@/lib/api";
import { BRAND } from "@/lib/brand";
import { StatCard } from "@/components/ui/badge";
import { StatusBadge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ErrorBanner } from "@/components/ui/error-banner";
import { PageLoader } from "@/components/ui/page-loader";
import { AlertTriangle } from "lucide-react";

function budgetPercent(agent: Agent) {
  if (!agent.max_token_budget) return 0;
  return Math.min(100, Math.round((agent.tokens_used / agent.max_token_budget) * 100));
}

export default function DashboardPage() {
  const { org, orgs, refreshOrgs } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creatingOrg, setCreatingOrg] = useState(false);

  useEffect(() => {
    if (!org) return;
    setFetching(true);
    setError(null);
    Promise.all([
      api.getDashboard(org.id),
      api.listAgents(org.id),
      api.listActivities(org.id, 20),
    ])
      .then(([s, a, acts]) => {
        setStats(s);
        setAgents(a);
        setActivities(acts);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load dashboard"))
      .finally(() => setFetching(false));
  }, [org]);

  const handleCreateOrg = async () => {
    setCreatingOrg(true);
    try {
      await api.createOrganization("My Engineering Team", "AIOS organization");
      await refreshOrgs();
    } finally {
      setCreatingOrg(false);
    }
  };

  if (!org && orgs.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-8">
        <Card className="max-w-md text-center">
          <CardHeader>
            <CardTitle>Welcome to {BRAND.name}</CardTitle>
          </CardHeader>
          <p className="text-muted-foreground mb-6">
            {BRAND.tagline} Hire agents, create projects, and watch them plan, build, test & deploy.
          </p>
          <Button onClick={handleCreateOrg} disabled={creatingOrg}>
            {creatingOrg ? "Creating..." : "Create Organization"}
          </Button>
        </Card>
      </div>
    );
  }

  if (fetching) {
    return <PageLoader label="Loading dashboard..." />;
  }

  const troubledAgents = agents.filter(
    (a) => a.status === "failed" || a.last_error || budgetPercent(a) >= 90
  );

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Executive Dashboard</h1>
        <p className="text-muted-foreground">{org?.name} — Company overview</p>
      </div>

      {error && <ErrorBanner message={error} />}

      {troubledAgents.length > 0 && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 space-y-2">
          <p className="text-sm font-medium text-red-200 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Agent API / balance issues
          </p>
          {troubledAgents.map((a) => (
            <p key={a.id} className="text-xs text-muted-foreground">
              <span className="font-medium text-foreground">{a.name}</span>
              {a.last_error || `Token budget at ${budgetPercent(a)}%`}
            </p>
          ))}
        </div>
      )}

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
          <StatCard title="Active Projects" value={stats.active_projects} />
          <StatCard title="Total Agents" value={stats.total_agents} />
          <StatCard title="Active Agents" value={stats.active_agents} variant="success" />
          <StatCard title="Total Tasks" value={stats.total_tasks} />
          <StatCard title="Completion" value={`${stats.completion_percentage}%`} />
          <StatCard title="Blocked" value={stats.blocked_tasks} variant="warning" />
          <StatCard title="Failed" value={stats.failed_tasks} variant="danger" />
          <StatCard title="Completed" value={stats.completed_tasks} variant="success" />
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Live Agents</CardTitle>
          </CardHeader>
          <div className="space-y-3">
            {agents.length === 0 ? (
              <p className="text-sm text-muted-foreground">No agents hired yet.</p>
            ) : (
              agents.map((agent) => (
                <div
                  key={agent.id}
                  className="flex items-center justify-between rounded-lg border border-border p-3"
                >
                  <div>
                    <p className="font-medium">{agent.name}</p>
                    <p className="text-sm text-muted-foreground">{agent.role}</p>
                    {agent.last_error && (
                      <p className="text-xs text-red-400 mt-1 line-clamp-1">{agent.last_error}</p>
                    )}
                  </div>
                  <StatusBadge status={agent.status} />
                </div>
              ))
            )}
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Live Activity</CardTitle>
          </CardHeader>
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {activities.length === 0 ? (
              <p className="text-sm text-muted-foreground">No activity yet.</p>
            ) : (
              activities.map((a) => (
                <div key={a.id} className="flex gap-3 text-sm border-b border-border pb-2 last:border-0">
                  <span className="text-muted-foreground whitespace-nowrap">
                    {new Date(a.created_at).toLocaleTimeString()}
                  </span>
                  <span>{a.message}</span>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {(stats?.blocked_tasks ?? 0) > 0 || (stats?.failed_tasks ?? 0) > 0 ? (
        <Card className="border-amber-500/30">
          <CardHeader>
            <CardTitle>Requires Your Attention</CardTitle>
          </CardHeader>
          <div className="space-y-2 text-sm">
            {stats!.blocked_tasks > 0 && (
              <p className="text-amber-400">⚠️ {stats!.blocked_tasks} blocked task(s) need resolution</p>
            )}
            {stats!.failed_tasks > 0 && (
              <p className="text-red-400">🚨 {stats!.failed_tasks} failed task(s) require review</p>
            )}
          </div>
        </Card>
      ) : null}
    </div>
  );
}
