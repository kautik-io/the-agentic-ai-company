"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { api, Project } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorBanner } from "@/components/ui/error-banner";
import { Input, Label, Textarea } from "@/components/ui/input";
import { PageLoader } from "@/components/ui/page-loader";
import { Plus, Sparkles, GitBranch, FolderOpen } from "lucide-react";

export default function ProjectsPage() {
  const { org } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [showNL, setShowNL] = useState(false);
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [requirements, setRequirements] = useState("");
  const [nlDescription, setNlDescription] = useState("");

  const load = async () => {
    if (!org) return;
    setFetching(true);
    setError(null);
    try {
      setProjects(await api.listProjects(org.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load projects");
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    load();
  }, [org]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!org) return;
    setLoading(true);
    setError(null);
    try {
      await api.createProject(org.id, {
        name,
        description,
        requirements: requirements.split("\n").map((r) => r.trim()).filter(Boolean),
      });
      setShowForm(false);
      setName("");
      setDescription("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setLoading(false);
    }
  };

  const handleNLCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!org) return;
    setLoading(true);
    setError(null);
    try {
      await api.createProjectFromNL(org.id, nlDescription);
      setShowNL(false);
      setNlDescription("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setLoading(false);
    }
  };

  if (fetching) {
    return <PageLoader label="Loading projects..." />;
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Projects</h1>
          <p className="text-muted-foreground">Manage software projects</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => { setShowNL(!showNL); setShowForm(false); }}>
            <Sparkles className="h-4 w-4 mr-2" />
            Natural Language
          </Button>
          <Button onClick={() => { setShowForm(!showForm); setShowNL(false); }}>
            <Plus className="h-4 w-4 mr-2" />
            New Project
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      {showForm && (
        <Card>
          <CardHeader><CardTitle>Create Project</CardTitle></CardHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <Label>Name *</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div>
              <Label>Description</Label>
              <Textarea value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>
            <div>
              <Label>Requirements (one per line — auto-plans tasks)</Label>
              <Textarea
                value={requirements}
                onChange={(e) => setRequirements(e.target.value)}
                placeholder={"Customer login\nTicket management\nAdmin dashboard"}
                rows={4}
              />
            </div>
            <div className="flex gap-3">
              <Button type="submit" disabled={loading}>{loading ? "Creating..." : "Create & Auto-Plan"}</Button>
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
            </div>
          </form>
        </Card>
      )}

      {showNL && (
        <Card>
          <CardHeader>
            <CardTitle>Create Project from Natural Language</CardTitle>
          </CardHeader>
          <form onSubmit={handleNLCreate} className="space-y-4">
            <div>
              <Label>Describe your project *</Label>
              <Textarea
                value={nlDescription}
                onChange={(e) => setNlDescription(e.target.value)}
                placeholder="Build a customer support platform with customer login, agent login, ticket management..."
                rows={4}
                required
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Creates project folder + logic graphs for AI context (no full code read needed).
            </p>
            <div className="flex gap-3">
              <Button type="submit" disabled={loading}>{loading ? "Creating..." : "Create with AI Planning"}</Button>
              <Button type="button" variant="outline" onClick={() => setShowNL(false)}>Cancel</Button>
            </div>
          </form>
        </Card>
      )}

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects.map((project) => (
          <Link key={project.id} href={`/projects/${project.id}`}>
            <Card className="hover:border-primary/50 transition-colors cursor-pointer h-full">
              <CardHeader>
                <CardTitle>{project.name}</CardTitle>
              </CardHeader>
              <p className="text-sm text-muted-foreground mb-3 line-clamp-2 px-6">
                {project.description || "No description"}
              </p>
              {project.workspace_path && (
                <p className="text-xs text-muted-foreground mb-2 px-6 flex items-center gap-1">
                  <FolderOpen className="h-3 w-3" />
                  {project.workspace_path.split("/").slice(-2).join("/")}
                </p>
              )}
              {project.logic_graph && (
                <p className="text-xs text-primary mb-2 px-6 flex items-center gap-1">
                  <GitBranch className="h-3 w-3" />
                  Logic graph ready
                </p>
              )}
              <div className="flex flex-wrap gap-1 mb-3 px-6">
                {project.tech_stack.map((t) => (
                  <span key={t} className="rounded bg-muted px-2 py-0.5 text-xs">{t}</span>
                ))}
              </div>
              <span className="text-xs uppercase tracking-wide text-muted-foreground px-6 pb-4 block">{project.status}</span>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
