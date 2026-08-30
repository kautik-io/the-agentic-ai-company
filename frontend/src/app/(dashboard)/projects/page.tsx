"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, Project } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label, Textarea } from "@/components/ui/input";
import { Plus, Sparkles } from "lucide-react";

export default function ProjectsPage() {
  const { org } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [showNL, setShowNL] = useState(false);
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [nlDescription, setNlDescription] = useState("");

  const load = () => {
    if (!org) return;
    api.listProjects(org.id).then(setProjects).catch(console.error);
  };

  useEffect(load, [org]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!org) return;
    setLoading(true);
    try {
      await api.createProject(org.id, { name, description });
      setShowForm(false);
      setName("");
      setDescription("");
      load();
    } finally {
      setLoading(false);
    }
  };

  const handleNLCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!org) return;
    setLoading(true);
    try {
      await api.createProjectFromNL(org.id, nlDescription);
      setShowNL(false);
      setNlDescription("");
      load();
    } finally {
      setLoading(false);
    }
  };

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

      {showForm && (
        <Card>
          <CardHeader><CardTitle>Create Project</CardTitle></CardHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <Label>Name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div>
              <Label>Description</Label>
              <Textarea value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>
            <div className="flex gap-3">
              <Button type="submit" disabled={loading}>Create</Button>
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
              <Label>Describe your project</Label>
              <Textarea
                value={nlDescription}
                onChange={(e) => setNlDescription(e.target.value)}
                placeholder="Build a customer support platform with customer login, agent login, ticket management..."
                rows={4}
                required
              />
            </div>
            <p className="text-xs text-muted-foreground">
              PM Agent will analyze requirements and create epics, tasks, and sprint plan (Phase 4+).
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
          <Card key={project.id}>
            <CardHeader>
              <CardTitle>{project.name}</CardTitle>
            </CardHeader>
            <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
              {project.description || "No description"}
            </p>
            <div className="flex flex-wrap gap-1 mb-3">
              {project.tech_stack.map((t) => (
                <span key={t} className="rounded bg-muted px-2 py-0.5 text-xs">{t}</span>
              ))}
            </div>
            <span className="text-xs uppercase tracking-wide text-muted-foreground">{project.status}</span>
          </Card>
        ))}
      </div>
    </div>
  );
}
