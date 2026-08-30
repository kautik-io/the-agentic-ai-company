"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { api, Agent, AiProviderConfig } from "@/lib/api";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorBanner } from "@/components/ui/error-banner";
import { Input, Label, Textarea, Select } from "@/components/ui/input";
import { PageLoader } from "@/components/ui/page-loader";
import { AlertTriangle, Pencil, Plus } from "lucide-react";

const emptyForm = {
  name: "",
  role: "",
  description: "",
  ai_provider: "openai",
  ai_model: "gpt-4o",
  responsibilities: "",
  skills: "",
  execution_target_id: "",
  max_token_budget: "100000",
};

function budgetPercent(agent: Agent) {
  if (!agent.max_token_budget) return 0;
  return Math.min(100, Math.round((agent.tokens_used / agent.max_token_budget) * 100));
}

export default function AgentsPage() {
  const { org } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [targets, setTargets] = useState<{ id: string; name: string }[]>([]);
  const [providerConfigs, setProviderConfigs] = useState<AiProviderConfig[]>([]);

  const loadAgents = async () => {
    if (!org) return;
    setFetching(true);
    setError(null);
    try {
      const [agents, configs] = await Promise.all([
        api.listAgents(org.id),
        api.listAiProviders(org.id),
      ]);
      setAgents(agents);
      setProviderConfigs(configs.filter((c) => c.is_active));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load agents");
    } finally {
      setFetching(false);
    }
  };

  const modelsForProvider = (provider: string) =>
    providerConfigs.find((c) => c.provider === provider)?.enabled_models ?? [];

  const providerOptions = providerConfigs.map((c) => c.provider);

  useEffect(() => {
    loadAgents();
  }, [org]);

  useEffect(() => {
    if (providerOptions.length > 0 && !providerOptions.includes(form.ai_provider)) {
      const first = providerOptions[0];
      const models = modelsForProvider(first);
      setForm((f) => ({
        ...f,
        ai_provider: first,
        ai_model: models[0] || f.ai_model,
      }));
    }
  }, [providerConfigs]);

  useEffect(() => {
    if (!org) return;
    api.listExecutionTargets(org.id)
      .then((t) => setTargets(t.map((x) => ({ id: x.id, name: x.name }))))
      .catch(() => {});
  }, [org]);

  const openCreate = () => {
    if (providerConfigs.length === 0) {
      setError("Add at least one API key in Settings before hiring agents.");
      return;
    }
    setEditingId(null);
    const first = providerConfigs[0].provider;
    const models = modelsForProvider(first);
    setForm({
      ...emptyForm,
      ai_provider: first,
      ai_model: models[0] || "gpt-4o",
    });
    setShowForm(true);
  };

  const openEdit = (agent: Agent) => {
    setEditingId(agent.id);
    setForm({
      name: agent.name,
      role: agent.role,
      description: agent.description || "",
      ai_provider: agent.ai_provider,
      ai_model: agent.ai_model,
      responsibilities: agent.responsibilities.join("\n"),
      skills: agent.skills.join(", "),
      execution_target_id: agent.execution_target_id || "",
      max_token_budget: String(agent.max_token_budget || 100000),
    });
    setShowForm(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!org) return;
    setLoading(true);
    setError(null);
    const payload = {
      name: form.name,
      role: form.role,
      description: form.description,
      ai_provider: form.ai_provider,
      ai_model: form.ai_model,
      responsibilities: form.responsibilities.split("\n").filter(Boolean),
      skills: form.skills.split(",").map((s) => s.trim()).filter(Boolean),
      execution_target_id: form.execution_target_id || undefined,
      max_token_budget: Number(form.max_token_budget) || 100000,
    };
    try {
      if (editingId) {
        await api.updateAgent(org.id, editingId, payload);
      } else {
        await api.hireAgent(org.id, payload);
      }
      setShowForm(false);
      setEditingId(null);
      setForm(emptyForm);
      await loadAgents();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save agent");
    } finally {
      setLoading(false);
    }
  };

  const troubledAgents = agents.filter(
    (a) => a.status === "failed" || a.last_error || budgetPercent(a) >= 90
  );

  if (fetching) {
    return <PageLoader label="Loading AI employees..." />;
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">AI Employees</h1>
          <p className="text-muted-foreground">Manage your virtual team</p>
        </div>
        <Button onClick={openCreate} disabled={providerConfigs.length === 0}>
          <Plus className="h-4 w-4 mr-2" />
          Hire AI Employee
        </Button>
      </div>

      {error && <ErrorBanner message={error} />}

      {providerConfigs.length === 0 && (
        <Card className="border-amber-500/30 bg-amber-500/10">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-400" />
              No API keys configured
            </CardTitle>
          </CardHeader>
          <p className="px-6 pb-6 text-sm text-muted-foreground">
            Add your OpenAI, Anthropic, or Google API keys in{" "}
            <Link href="/settings" className="text-primary hover:underline">Settings → AI Provider Keys</Link>.
            AI employees only appear here after their provider key is saved.
          </p>
        </Card>
      )}

      {troubledAgents.length > 0 && providerConfigs.length > 0 && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 space-y-2">
          <p className="text-sm font-medium text-amber-200 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            {troubledAgents.length} agent{troubledAgents.length !== 1 ? "s" : ""} need attention
          </p>
          {troubledAgents.map((a) => (
            <p key={a.id} className="text-xs text-muted-foreground">
              <span className="font-medium text-foreground">{a.name}</span>
              {a.last_error ? ` — ${a.last_error}` : budgetPercent(a) >= 90 ? ` — Token budget at ${budgetPercent(a)}%` : ` — Status: ${a.status}`}
            </p>
          ))}
        </div>
      )}

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>{editingId ? "Edit AI Employee" : "Hire New AI Employee"}</CardTitle>
          </CardHeader>
          <form onSubmit={handleSubmit} className="grid md:grid-cols-2 gap-4">
            <div>
              <Label>Name *</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div>
              <Label>Role *</Label>
              <Input value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} required />
            </div>
            <div className="md:col-span-2">
              <Label>Job Description *</Label>
              <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} required />
            </div>
            <div>
              <Label>AI Provider *</Label>
              <Select
                value={form.ai_provider}
                onChange={(e) => {
                  const p = e.target.value;
                  const models = modelsForProvider(p);
                  setForm({ ...form, ai_provider: p, ai_model: models[0] || "" });
                }}
                required
              >
                {providerConfigs.map((c) => (
                  <option key={c.provider} value={c.provider}>
                    {c.provider === "openai" ? "OpenAI" : c.provider === "anthropic" ? "Anthropic" : "Google AI"}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>AI Model *</Label>
              <Select
                value={form.ai_model}
                onChange={(e) => setForm({ ...form, ai_model: e.target.value })}
                required
              >
                {modelsForProvider(form.ai_provider).map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </Select>
            </div>
            <div>
              <Label>Token Budget</Label>
              <Input type="number" min={1000} value={form.max_token_budget} onChange={(e) => setForm({ ...form, max_token_budget: e.target.value })} />
            </div>
            {targets.length > 0 && (
              <div className="md:col-span-2">
                <Label>Run environment (path / SSH / VM)</Label>
                <Select
                  value={form.execution_target_id}
                  onChange={(e) => setForm({ ...form, execution_target_id: e.target.value })}
                >
                  <option value="">Default organization environment</option>
                  {targets.map((t) => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </Select>
              </div>
            )}
            <div>
              <Label>Responsibilities * (one per line)</Label>
              <Textarea value={form.responsibilities} onChange={(e) => setForm({ ...form, responsibilities: e.target.value })} required />
            </div>
            <div>
              <Label>Skills * (comma-separated)</Label>
              <Input value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} required />
            </div>
            <div className="md:col-span-2 flex gap-3">
              <Button type="submit" disabled={loading}>{loading ? "Saving..." : editingId ? "Save Changes" : "Hire Employee"}</Button>
              <Button type="button" variant="outline" onClick={() => { setShowForm(false); setEditingId(null); }}>Cancel</Button>
            </div>
          </form>
        </Card>
      )}

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent) => {
          const pct = budgetPercent(agent);
          return (
            <Card key={agent.id} className={agent.last_error || agent.status === "failed" ? "border-red-500/40" : ""}>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold">{agent.name}</h3>
                  <p className="text-sm text-muted-foreground">{agent.role}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="sm" onClick={() => openEdit(agent)} aria-label={`Edit ${agent.name}`}>
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <StatusBadge status={agent.status} />
                </div>
              </div>
              {agent.description && (
                <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{agent.description}</p>
              )}
              {agent.last_error && (
                <p className="text-xs text-red-400 mb-3 line-clamp-3">{agent.last_error}</p>
              )}
              <div className="mb-3">
                <div className="flex justify-between text-xs text-muted-foreground mb-1">
                  <span>Token usage</span>
                  <span className={pct >= 90 ? "text-red-400" : ""}>{agent.tokens_used.toLocaleString()} / {agent.max_token_budget.toLocaleString()}</span>
                </div>
                <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                  <div
                    className={`h-full rounded-full ${pct >= 90 ? "bg-red-500" : pct >= 70 ? "bg-amber-500" : "bg-primary"}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
              <div className="flex flex-wrap gap-1 mb-3">
                {agent.skills.slice(0, 4).map((skill) => (
                  <span key={skill} className="rounded bg-muted px-2 py-0.5 text-xs">{skill}</span>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">
                {agent.ai_provider} / {agent.ai_model}
              </p>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
