"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, Agent } from "@/lib/api";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Textarea, Select } from "@/components/ui/input";
import { Plus } from "lucide-react";

export default function AgentsPage() {
  const { org } = useAuth();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    name: "",
    role: "",
    description: "",
    ai_provider: "openai",
    ai_model: "gpt-4o",
    responsibilities: "",
    skills: "",
    execution_target_id: "",
  });
  const [targets, setTargets] = useState<{ id: string; name: string }[]>([]);

  const loadAgents = () => {
    if (!org) return;
    api.listAgents(org.id).then(setAgents).catch(console.error);
  };

  useEffect(loadAgents, [org]);

  useEffect(() => {
    if (!org) return;
    api.listExecutionTargets(org.id).then((t) => setTargets(t.map((x) => ({ id: x.id, name: x.name })))).catch(console.error);
  }, [org]);

  const handleHire = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!org) return;
    setLoading(true);
    try {
      await api.hireAgent(org.id, {
        name: form.name,
        role: form.role,
        description: form.description || undefined,
        ai_provider: form.ai_provider,
        ai_model: form.ai_model,
        responsibilities: form.responsibilities.split("\n").filter(Boolean),
        skills: form.skills.split(",").map((s) => s.trim()).filter(Boolean),
        execution_target_id: form.execution_target_id || undefined,
      });
      setShowForm(false);
      setForm({ name: "", role: "", description: "", ai_provider: "openai", ai_model: "gpt-4o", responsibilities: "", skills: "", execution_target_id: "" });
      loadAgents();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to hire agent");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">AI Employees</h1>
          <p className="text-muted-foreground">Manage your virtual team</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4 mr-2" />
          Hire AI Employee
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Hire New AI Employee</CardTitle>
          </CardHeader>
          <form onSubmit={handleHire} className="grid md:grid-cols-2 gap-4">
            <div>
              <Label>Name</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div>
              <Label>Role</Label>
              <Input value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} required />
            </div>
            <div className="md:col-span-2">
              <Label>Job Description</Label>
              <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div>
              <Label>AI Provider</Label>
              <Select value={form.ai_provider} onChange={(e) => setForm({ ...form, ai_provider: e.target.value })}>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="google">Google</option>
              </Select>
            </div>
            <div>
              <Label>AI Model</Label>
              <Input value={form.ai_model} onChange={(e) => setForm({ ...form, ai_model: e.target.value })} />
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
              <Label>Responsibilities (one per line)</Label>
              <Textarea value={form.responsibilities} onChange={(e) => setForm({ ...form, responsibilities: e.target.value })} />
            </div>
            <div>
              <Label>Skills (comma-separated)</Label>
              <Input value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} />
            </div>
            <div className="md:col-span-2 flex gap-3">
              <Button type="submit" disabled={loading}>{loading ? "Hiring..." : "Hire Employee"}</Button>
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
            </div>
          </form>
        </Card>
      )}

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map((agent) => (
          <Card key={agent.id}>
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold">{agent.name}</h3>
                <p className="text-sm text-muted-foreground">{agent.role}</p>
              </div>
              <StatusBadge status={agent.status} />
            </div>
            {agent.description && (
              <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{agent.description}</p>
            )}
            <div className="flex flex-wrap gap-1 mb-3">
              {agent.skills.slice(0, 4).map((skill) => (
                <span key={skill} className="rounded bg-muted px-2 py-0.5 text-xs">{skill}</span>
              ))}
            </div>
            <p className="text-xs text-muted-foreground">
              {agent.ai_provider} / {agent.ai_model}
            </p>
          </Card>
        ))}
      </div>
    </div>
  );
}
