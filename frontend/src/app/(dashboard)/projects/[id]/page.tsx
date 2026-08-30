"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, Epic, Feature, Project, ProjectGraph } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorBanner } from "@/components/ui/error-banner";
import { Input, Label, Textarea } from "@/components/ui/input";
import { PageLoader } from "@/components/ui/page-loader";
import { LogicGraphViewer } from "@/components/projects/logic-graph-viewer";
import { ProjectPlanPanel } from "@/components/projects/project-plan-panel";
import { ArrowLeft, FolderOpen, GitBranch, Pencil, Plus, Trash2 } from "lucide-react";

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  const { org } = useAuth();
  const [project, setProject] = useState<Project | null>(null);
  const [graph, setGraph] = useState<ProjectGraph | null>(null);
  const [selectedGraph, setSelectedGraph] = useState<string>("");
  const [selectedLabel, setSelectedLabel] = useState("Project");
  const [showEpicForm, setShowEpicForm] = useState(false);
  const [showFeatureForm, setShowFeatureForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [epicTitle, setEpicTitle] = useState("");
  const [featureTitle, setFeatureTitle] = useState("");
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [targetEpicId, setTargetEpicId] = useState("");
  const [fetching, setFetching] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    if (!org) return;
    setFetching(true);
    setError(null);
    try {
      const [p, g] = await Promise.all([
        api.getProject(org.id, projectId),
        api.getProjectGraph(org.id, projectId),
      ]);
      setProject(p);
      setGraph(g);
      setSelectedGraph(p.logic_graph || "");
      setEditName(p.name);
      setEditDescription(p.description || "");
      if (!targetEpicId && g.epics.length > 0) {
        setTargetEpicId(g.epics[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load project");
    } finally {
      setFetching(false);
    }
  };

  useEffect(() => {
    load();
  }, [org, projectId]);

  const handleAddEpic = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!org) return;
    setLoading(true);
    setError(null);
    try {
      await api.createEpic(org.id, projectId, { title: epicTitle });
      setEpicTitle("");
      setShowEpicForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add epic");
    } finally {
      setLoading(false);
    }
  };

  const handleAddFeature = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!org || !targetEpicId) return;
    setLoading(true);
    setError(null);
    try {
      await api.createFeature(org.id, projectId, targetEpicId, { title: featureTitle });
      setFeatureTitle("");
      setShowFeatureForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add feature");
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!org) return;
    setLoading(true);
    setError(null);
    try {
      await api.updateProject(org.id, projectId, { name: editName, description: editDescription });
      setShowEditForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update project");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!org || !project) return;
    if (!window.confirm(`Delete project "${project.name}"? This cannot be undone.`)) return;
    setLoading(true);
    setError(null);
    try {
      await api.deleteProject(org.id, projectId);
      router.push("/projects");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete project");
      setLoading(false);
    }
  };

  if (fetching || !project || !graph) {
    return <PageLoader label="Loading project..." />;
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link href="/projects" className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 mb-2">
            <ArrowLeft className="h-4 w-4" /> Back to projects
          </Link>
          <h1 className="text-2xl font-bold">{project.name}</h1>
          <p className="text-muted-foreground">{project.description || "No description"}</p>
          {project.workspace_path && (
            <p className="text-xs text-muted-foreground mt-2 flex items-center gap-1">
              <FolderOpen className="h-3 w-3" />
              Workspace: <code className="text-primary">{project.workspace_path}</code>
            </p>
          )}
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button variant="outline" onClick={() => { setShowEditForm(!showEditForm); setShowEpicForm(false); setShowFeatureForm(false); }}>
            <Pencil className="h-4 w-4 mr-1" /> Edit
          </Button>
          <Button variant="danger" onClick={handleDelete} disabled={loading}>
            <Trash2 className="h-4 w-4 mr-1" /> Delete
          </Button>
          <Button variant="outline" onClick={() => { setShowEpicForm(!showEpicForm); setShowFeatureForm(false); setShowEditForm(false); }}>
            <Plus className="h-4 w-4 mr-1" /> Epic
          </Button>
          <Button variant="outline" onClick={() => { setShowFeatureForm(!showFeatureForm); setShowEpicForm(false); setShowEditForm(false); }}>
            <Plus className="h-4 w-4 mr-1" /> Feature
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      {org && <ProjectPlanPanel orgId={org.id} projectId={projectId} />}

      {showEditForm && (
        <Card>
          <CardHeader><CardTitle>Edit Project</CardTitle></CardHeader>
          <form onSubmit={handleEdit} className="space-y-3">
            <div>
              <Label>Name *</Label>
              <Input value={editName} onChange={(e) => setEditName(e.target.value)} required />
            </div>
            <div>
              <Label>Description</Label>
              <Textarea value={editDescription} onChange={(e) => setEditDescription(e.target.value)} />
            </div>
            <Button type="submit" disabled={loading}>{loading ? "Saving..." : "Save Changes"}</Button>
          </form>
        </Card>
      )}

      {showEpicForm && (
        <Card>
          <CardHeader><CardTitle>New Epic</CardTitle></CardHeader>
          <form onSubmit={handleAddEpic} className="space-y-3">
            <div>
              <Label>Title *</Label>
              <Input value={epicTitle} onChange={(e) => setEpicTitle(e.target.value)} required />
            </div>
            <Button type="submit" disabled={loading}>Add Epic (auto-generates graph)</Button>
          </form>
        </Card>
      )}

      {showFeatureForm && (
        <Card>
          <CardHeader><CardTitle>New Feature</CardTitle></CardHeader>
          <form onSubmit={handleAddFeature} className="space-y-3">
            <div>
              <Label>Epic</Label>
              <select
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={targetEpicId}
                onChange={(e) => setTargetEpicId(e.target.value)}
              >
                {graph.epics.map((epic: Epic) => (
                  <option key={epic.id} value={epic.id}>{epic.title}</option>
                ))}
              </select>
            </div>
            <div>
              <Label>Title *</Label>
              <Input value={featureTitle} onChange={(e) => setFeatureTitle(e.target.value)} required />
            </div>
            <Button type="submit" disabled={loading || !targetEpicId}>Add Feature (auto-generates graph)</Button>
          </form>
        </Card>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-3">
          <h2 className="font-semibold flex items-center gap-2">
            <GitBranch className="h-4 w-4" /> Logic Graphs
          </h2>
          <p className="text-xs text-muted-foreground">
            AI agents read these diagrams instead of full code to understand project logic.
          </p>
          <button
            type="button"
            onClick={() => { setSelectedGraph(project.logic_graph || ""); setSelectedLabel("Project"); }}
            className={`w-full text-left rounded-lg border p-3 text-sm ${selectedLabel === "Project" ? "border-primary bg-primary/10" : "border-border"}`}
          >
            Project overview
          </button>
          {graph.epics.map((epic: Epic) => (
            <button
              key={epic.id}
              type="button"
              onClick={() => { setSelectedGraph(epic.logic_graph || ""); setSelectedLabel(`Epic: ${epic.title}`); }}
              className={`w-full text-left rounded-lg border p-3 text-sm ${selectedLabel === `Epic: ${epic.title}` ? "border-primary bg-primary/10" : "border-border"}`}
            >
              Epic: {epic.title}
            </button>
          ))}
          {graph.features.map((feature: Feature) => (
            <button
              key={feature.id}
              type="button"
              onClick={() => { setSelectedGraph(feature.logic_graph || ""); setSelectedLabel(`Feature: ${feature.title}`); }}
              className={`w-full text-left rounded-lg border p-3 text-sm ${selectedLabel === `Feature: ${feature.title}` ? "border-primary bg-primary/10" : "border-border"}`}
            >
              Feature: {feature.title}
            </button>
          ))}
        </div>

        <div className="lg:col-span-2 space-y-3">
          <h2 className="font-semibold">{selectedLabel}</h2>
          {selectedGraph ? (
            <LogicGraphViewer chart={selectedGraph} />
          ) : (
            <p className="text-muted-foreground text-sm">No graph yet.</p>
          )}
          <details className="text-xs">
            <summary className="cursor-pointer text-muted-foreground">View Mermaid source</summary>
            <Textarea readOnly value={selectedGraph} rows={8} className="font-mono mt-2" />
          </details>
        </div>
      </div>
    </div>
  );
}
