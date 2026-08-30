"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, ExecutionTarget } from "@/lib/api";
import { AiProviderSettings } from "@/components/settings/ai-provider-settings";
import { PageLoader } from "@/components/ui/page-loader";
import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input, Label, Select, Textarea } from "@/components/ui/input";
import { Plus, Server, FolderOpen, Container, PlugZap } from "lucide-react";

const EMPTY_FORM = {
  name: "",
  target_type: "local" as "local" | "ssh" | "docker",
  workspace_path: "/home/aividmini/PS",
  host: "",
  port: 22,
  username: "",
  ssh_key_path: "",
  ssh_password: "",
  docker_image: "",
  is_default: true,
};

export default function SettingsPage() {
  const { org } = useAuth();
  const [targets, setTargets] = useState<ExecutionTarget[]>([]);
  const [fetching, setFetching] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(false);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<string | null>(null);

  const load = () => {
    if (!org) return;
    setFetching(true);
    api.listExecutionTargets(org.id)
      .then(setTargets)
      .catch(console.error)
      .finally(() => setFetching(false));
  };

  useEffect(load, [org]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!org) return;
    setLoading(true);
    setTestResult(null);
    try {
      const payload = {
        name: form.name,
        target_type: form.target_type,
        workspace_path: form.workspace_path,
        host: form.host || undefined,
        port: form.port,
        username: form.username || undefined,
        ssh_key_path: form.ssh_key_path || undefined,
        ssh_password: form.ssh_password || undefined,
        docker_image: form.docker_image || undefined,
        is_default: form.is_default,
      };
      if (editingId) {
        await api.updateExecutionTarget(org.id, editingId, payload);
      } else {
        await api.createExecutionTarget(org.id, payload);
      }
      setShowForm(false);
      setEditingId(null);
      setForm(EMPTY_FORM);
      load();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to save target");
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (target: ExecutionTarget) => {
    setEditingId(target.id);
    setForm({
      name: target.name,
      target_type: target.target_type,
      workspace_path: target.workspace_path,
      host: target.host || "",
      port: target.port,
      username: target.username || "",
      ssh_key_path: target.ssh_key_path || "",
      ssh_password: "",
      docker_image: target.docker_image || "",
      is_default: target.is_default,
    });
    setShowForm(true);
    setTestResult(null);
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setEditingId(null);
    setForm(EMPTY_FORM);
  };

  const handleTest = async (targetId: string) => {
    if (!org) return;
    setTestingId(targetId);
    setTestResult(null);
    try {
      const result = await api.testExecutionTarget(org.id, targetId);
      setTestResult(result.message);
      load();
    } catch (err) {
      setTestResult(err instanceof Error ? err.message : "Test failed");
    } finally {
      setTestingId(null);
    }
  };

  const typeIcon = (type: string) => {
    if (type === "ssh") return <Server className="h-4 w-4" />;
    if (type === "docker") return <Container className="h-4 w-4" />;
    return <FolderOpen className="h-4 w-4" />;
  };

  return (
    <div className="p-8 space-y-10 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-muted-foreground">
          AI provider keys, models, and run environments for your agents
        </p>
      </div>

      <AiProviderSettings />

      <hr className="border-border" />

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Run Environments</h2>
          <p className="text-sm text-muted-foreground">
            Where AI agents run code — local paths, SSH, or Docker
          </p>
        </div>
        <Button onClick={() => { setEditingId(null); setForm(EMPTY_FORM); setShowForm(!showForm); }}>
          <Plus className="h-4 w-4 mr-2" />
          Add Run Environment
        </Button>
      </div>

      <Card className="border-primary/20 bg-primary/5">
        <CardHeader>
          <CardTitle className="text-base">How this works</CardTitle>
          <CardDescription>
            Each AI employee runs in an isolated workspace on a target machine. Set a <strong>local path</strong> on
            this server (e.g. Raspberry Pi), or an <strong>SSH login</strong> to a remote VM, similar to Cursor&apos;s
            remote development.
          </CardDescription>
        </CardHeader>
        <div className="px-6 pb-6 text-sm text-muted-foreground space-y-1">
          <p><strong>Local:</strong> /home/aividmini/PS/my-project</p>
          <p><strong>SSH:</strong> user@192.168.1.50 → /var/www/app</p>
          <p><strong>SSH key:</strong> path on this server, e.g. /home/aividmini/.ssh/id_rsa</p>
        </div>
      </Card>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>{editingId ? "Edit Run Environment" : "Add Run Environment"}</CardTitle>
          </CardHeader>
          <form onSubmit={handleCreate} className="grid md:grid-cols-2 gap-4">
            <div>
              <Label>Name</Label>
              <Input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Raspberry Pi — Main Projects"
                required
              />
            </div>
            <div>
              <Label>Type</Label>
              <Select
                value={form.target_type}
                onChange={(e) => setForm({ ...form, target_type: e.target.value as typeof form.target_type })}
              >
                <option value="local">Local path (this machine)</option>
                <option value="ssh">SSH (remote VM / server)</option>
                <option value="docker">Docker container</option>
              </Select>
            </div>
            <div className="md:col-span-2">
              <Label>Workspace path (on target machine)</Label>
              <Input
                value={form.workspace_path}
                onChange={(e) => setForm({ ...form, workspace_path: e.target.value })}
                placeholder="/home/aividmini/PS/the-agentic-ai-company"
                required
              />
            </div>
            {form.target_type === "ssh" && (
              <>
                <div>
                  <Label>SSH host</Label>
                  <Input
                    value={form.host}
                    onChange={(e) => setForm({ ...form, host: e.target.value })}
                    placeholder="192.168.1.50 or vm.example.com"
                    required
                  />
                </div>
                <div>
                  <Label>SSH port</Label>
                  <Input
                    type="number"
                    value={form.port}
                    onChange={(e) => setForm({ ...form, port: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <Label>SSH username</Label>
                  <Input
                    value={form.username}
                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                    placeholder="aividmini"
                    required
                  />
                </div>
                <div>
                  <Label>SSH private key path (on dashboard server)</Label>
                  <Input
                    value={form.ssh_key_path}
                    onChange={(e) => setForm({ ...form, ssh_key_path: e.target.value })}
                    placeholder="/home/aividmini/.ssh/id_rsa"
                  />
                </div>
                <div>
                  <Label>SSH password (optional if using key)</Label>
                  <Input
                    type="password"
                    value={form.ssh_password}
                    onChange={(e) => setForm({ ...form, ssh_password: e.target.value })}
                    placeholder="Leave blank to keep existing"
                    autoComplete="new-password"
                  />
                </div>
              </>
            )}
            {form.target_type === "docker" && (
              <div className="md:col-span-2">
                <Label>Docker image</Label>
                <Input
                  value={form.docker_image}
                  onChange={(e) => setForm({ ...form, docker_image: e.target.value })}
                  placeholder="python:3.12-slim"
                />
              </div>
            )}
            <div className="md:col-span-2 flex items-center gap-2">
              <input
                type="checkbox"
                id="is_default"
                checked={form.is_default}
                onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
              />
              <Label htmlFor="is_default" className="mb-0">Set as default run environment</Label>
            </div>
            <div className="md:col-span-2 flex gap-3">
              <Button type="submit" disabled={loading}>
                {loading ? "Saving..." : editingId ? "Update environment" : "Save environment"}
              </Button>
              <Button type="button" variant="outline" onClick={handleCancelForm}>Cancel</Button>
            </div>
          </form>
        </Card>
      )}

      {testResult && (
        <div className="rounded-lg border border-border bg-muted px-4 py-3 text-sm">{testResult}</div>
      )}

      <div className="space-y-3">
        {targets.length === 0 ? (
          <Card className="text-center py-8 text-muted-foreground">
            No run environments configured. Add a local path or SSH target so agents know where to work.
          </Card>
        ) : (
          targets.map((t) => (
            <Card key={t.id}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex gap-3">
                  <div className="mt-1 text-primary">{typeIcon(t.target_type)}</div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{t.name}</h3>
                      {t.is_default && (
                        <span className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded-full">Default</span>
                      )}
                      <StatusBadge status={t.status} />
                    </div>
                    <p className="text-sm text-muted-foreground mt-1 font-mono">{t.workspace_path}</p>
                    {t.target_type === "ssh" && t.host && (
                      <p className="text-sm text-muted-foreground">
                        ssh {t.username}@{t.host}:{t.port}
                        {t.ssh_key_path ? ` — key: ${t.ssh_key_path}` : ""}
                        {t.ssh_password_set ? " — password saved" : ""}
                      </p>
                    )}
                    {t.last_error && (
                      <p className="text-sm text-red-400 mt-1">{t.last_error}</p>
                    )}
                  </div>
                </div>
                <div className="flex gap-2 shrink-0">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(t)}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleTest(t.id)}
                    disabled={testingId === t.id}
                  >
                    <PlugZap className="h-4 w-4 mr-1" />
                    {testingId === t.id ? "Testing..." : "Test"}
                  </Button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
