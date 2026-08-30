const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Agent {
  id: string;
  organization_id: string;
  department_id: string | null;
  manager_id: string | null;
  execution_target_id: string | null;
  name: string;
  role: string;
  description: string | null;
  responsibilities: string[];
  skills: string[];
  ai_provider: string;
  ai_model: string;
  temperature: number;
  max_token_budget: number;
  status: string;
  last_error: string | null;
  tokens_used: number;
  current_task_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description: string | null;
  goals: string[];
  requirements: string[];
  tech_stack: string[];
  repository_url: string | null;
  workspace_path: string | null;
  logic_graph: string | null;
  status: string;
  settings?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ProjectPlan {
  project_id: string;
  planning_status: string;
  summary: string | null;
  epics: Array<{ title: string; description?: string }>;
  features: Array<{ epic: string; title: string; slug?: string }>;
  tasks: Array<{
    title: string;
    description?: string;
    epic: string;
    feature: string;
    agent_role: string;
    priority: string;
    phase: string;
    task_type?: string;
    depends_on?: string[];
    manual?: boolean;
  }>;
  manual_tasks: ProjectPlan["tasks"];
  total_tasks: number;
  approved_at: string | null;
}

export interface PlanApprovalResult {
  planning_status: string;
  tasks_created: number;
  epics_created: number;
  features_created: number;
  message: string;
}

export interface Epic {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  logic_graph: string | null;
  status: string;
  created_at: string;
}

export interface Feature {
  id: string;
  epic_id: string;
  title: string;
  slug: string | null;
  description: string | null;
  logic_graph: string | null;
  status: string;
  created_at: string;
}

export interface ProjectGraph {
  project_id: string;
  project_name: string;
  logic_graph: string | null;
  epics: Epic[];
  features: Feature[];
}

export interface ExecutionTarget {
  id: string;
  organization_id: string;
  project_id: string | null;
  name: string;
  target_type: "local" | "ssh" | "docker";
  workspace_path: string;
  host: string | null;
  port: number;
  username: string | null;
  ssh_key_path: string | null;
  ssh_password_set?: boolean;
  docker_image: string | null;
  is_default: boolean;
  status: string;
  last_error: string | null;
  last_verified_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConnectionTestResult {
  success: boolean;
  message: string;
  status: string;
}

export interface AiProviderConfig {
  id: string;
  organization_id: string;
  provider: string;
  api_key_masked: string;
  enabled_models: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProviderModelCatalog {
  provider: string;
  label: string;
  models: string[];
}

export interface TaskExecutionLogEntry {
  ts: string;
  level: string;
  message: string;
}

export interface TaskExecutionRun {
  id: string;
  status: string;
  agent_name: string | null;
  token_usage: number;
  error: string | null;
  started_at: string | null;
  ended_at: string | null;
  logs: TaskExecutionLogEntry[];
}

export interface TaskExecutionLogs {
  live: boolean;
  runs: TaskExecutionRun[];
}

export interface Task {
  id: string;
  project_id: string;
  epic_id?: string | null;
  feature_id?: string | null;
  task_number: number;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  assigned_agent_id: string | null;
  estimated_minutes: number | null;
  blocked_reason: string | null;
  failure_reason: string | null;
  retry_count?: number;
  screenshots?: TaskScreenshot[];
  created_at: string;
  updated_at: string;
}

export interface TaskScreenshot {
  id: string;
  task_id: string;
  feature_id: string | null;
  filename: string;
  url: string;
  caption: string | null;
  created_at: string;
}

export interface FeatureTaskReview {
  feature_id: string | null;
  feature_title: string;
  tasks: Array<{
    task_id: string;
    task_number: number;
    title: string;
    completed_at: string | null;
    screenshots: TaskScreenshot[];
  }>;
}

export interface DashboardStats {
  active_projects: number;
  total_agents: number;
  active_agents: number;
  total_tasks: number;
  completed_tasks: number;
  blocked_tasks: number;
  failed_tasks: number;
  completion_percentage: number;
}

export interface Activity {
  id: string;
  event_type: string;
  message: string;
  project_id: string | null;
  agent_id: string | null;
  task_id: string | null;
  created_at: string;
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== "undefined") {
      if (token) localStorage.setItem("access_token", token);
      else localStorage.removeItem("access_token");
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("access_token");
    }
    return this.token;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };
    const token = this.getToken();
    if (token) headers.Authorization = `Bearer ${token}`;

    const res = await fetch(`${API_URL}${path}`, { ...options, headers });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Request failed");
    }
    if (res.status === 204) return undefined as T;
    return res.json();
  }

  login(email: string, password: string) {
    return this.request<{ access_token: string; refresh_token: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  register(email: string, password: string, full_name: string) {
    return this.request<User>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    });
  }

  getMe() {
    return this.request<User>("/api/auth/me");
  }

  listOrganizations() {
    return this.request<Organization[]>("/api/organizations");
  }

  createOrganization(name: string, description?: string) {
    return this.request<Organization>("/api/organizations", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    });
  }

  getDashboard(orgId: string) {
    return this.request<DashboardStats>(`/api/organizations/${orgId}/dashboard`);
  }

  listActivities(orgId: string, limit = 50) {
    return this.request<Activity[]>(`/api/organizations/${orgId}/activities?limit=${limit}`);
  }

  listAgents(orgId: string) {
    return this.request<Agent[]>(`/api/organizations/${orgId}/agents`);
  }

  getAgent(orgId: string, agentId: string) {
    return this.request<Agent>(`/api/organizations/${orgId}/agents/${agentId}`);
  }

  updateAgent(orgId: string, agentId: string, data: Partial<Agent>) {
    return this.request<Agent>(`/api/organizations/${orgId}/agents/${agentId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  hireAgent(orgId: string, data: Partial<Agent> & { name: string; role: string; description: string; responsibilities: string[]; skills: string[] }) {
    return this.request<Agent>(`/api/organizations/${orgId}/agents`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  listProjects(orgId: string) {
    return this.request<Project[]>(`/api/organizations/${orgId}/projects`);
  }

  getProject(orgId: string, projectId: string) {
    return this.request<Project>(`/api/organizations/${orgId}/projects/${projectId}`);
  }

  getProjectGraph(orgId: string, projectId: string) {
    return this.request<ProjectGraph>(`/api/organizations/${orgId}/projects/${projectId}/graph`);
  }

  createEpic(orgId: string, projectId: string, data: { title: string; description?: string }) {
    return this.request<Epic>(`/api/organizations/${orgId}/projects/${projectId}/epics`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  createFeature(orgId: string, projectId: string, epicId: string, data: { title: string; description?: string }) {
    return this.request<Feature>(`/api/organizations/${orgId}/projects/${projectId}/epics/${epicId}/features`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  createProject(orgId: string, data: { name: string; description?: string; goals?: string[]; requirements?: string[]; tech_stack?: string[] }) {
    return this.request<Project>(`/api/organizations/${orgId}/projects`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  updateProject(orgId: string, projectId: string, data: { name?: string; description?: string; status?: string }) {
    return this.request<Project>(`/api/organizations/${orgId}/projects/${projectId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  deleteProject(orgId: string, projectId: string) {
    return this.request<void>(`/api/organizations/${orgId}/projects/${projectId}`, {
      method: "DELETE",
    });
  }

  createProjectFromNL(orgId: string, description: string, project_name?: string) {
    return this.request<Project>(`/api/organizations/${orgId}/projects/from-natural-language`, {
      method: "POST",
      body: JSON.stringify({ description, project_name }),
    });
  }

  listTasks(orgId: string, projectId: string) {
    return this.request<Task[]>(`/api/organizations/${orgId}/projects/${projectId}/tasks`);
  }

  getTaskExecutionLogs(orgId: string, projectId: string, taskId: string) {
    return this.request<TaskExecutionLogs>(
      `/api/organizations/${orgId}/projects/${projectId}/tasks/${taskId}/execution-logs`
    );
  }

  updateTask(orgId: string, projectId: string, taskId: string, data: { status?: string }) {
    return this.request<Task>(`/api/organizations/${orgId}/projects/${projectId}/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async completeTaskWithScreenshot(
    orgId: string,
    projectId: string,
    taskId: string,
    blob: Blob,
    caption?: string
  ) {
    const form = new FormData();
    form.append("file", blob, "screenshot.png");
    const token = this.getToken();
    const headers: Record<string, string> = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    let url = `${API_URL}/api/organizations/${orgId}/projects/${projectId}/tasks/${taskId}/screenshot`;
    if (caption) url += `?caption=${encodeURIComponent(caption)}`;
    const res = await fetch(url, { method: "POST", headers, body: form });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Upload failed");
    }
    return res.json() as Promise<TaskScreenshot>;
  }

  getFeatureReviews(orgId: string, projectId: string) {
    return this.request<FeatureTaskReview[]>(`/api/organizations/${orgId}/projects/${projectId}/feature-reviews`);
  }

  getProjectPlan(orgId: string, projectId: string) {
    return this.request<ProjectPlan>(`/api/organizations/${orgId}/projects/${projectId}/plan`);
  }

  approveProjectPlan(orgId: string, projectId: string) {
    return this.request<PlanApprovalResult>(`/api/organizations/${orgId}/projects/${projectId}/plan/approve`, {
      method: "POST",
    });
  }

  regenerateProjectPlan(orgId: string, projectId: string) {
    return this.request<ProjectPlan>(`/api/organizations/${orgId}/projects/${projectId}/plan/regenerate`, {
      method: "POST",
    });
  }

  addManualPlanTask(orgId: string, projectId: string, data: { title: string; description?: string; epic?: string; priority?: string }) {
    return this.request<ProjectPlan>(`/api/organizations/${orgId}/projects/${projectId}/plan/tasks`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  listExecutionTargets(orgId: string) {
    return this.request<ExecutionTarget[]>(`/api/organizations/${orgId}/execution-targets`);
  }

  createExecutionTarget(orgId: string, data: Partial<ExecutionTarget> & { name: string; workspace_path: string; target_type: string }) {
    return this.request<ExecutionTarget>(`/api/organizations/${orgId}/execution-targets`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  updateExecutionTarget(orgId: string, targetId: string, data: Partial<ExecutionTarget>) {
    return this.request<ExecutionTarget>(`/api/organizations/${orgId}/execution-targets/${targetId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  deleteExecutionTarget(orgId: string, targetId: string) {
    return this.request<void>(`/api/organizations/${orgId}/execution-targets/${targetId}`, {
      method: "DELETE",
    });
  }

  testExecutionTarget(orgId: string, targetId: string) {
    return this.request<ConnectionTestResult>(`/api/organizations/${orgId}/execution-targets/${targetId}/test`, {
      method: "POST",
    });
  }

  getProviderCatalog(orgId: string) {
    return this.request<ProviderModelCatalog[]>(`/api/organizations/${orgId}/ai-providers/catalog`);
  }

  listAiProviders(orgId: string) {
    return this.request<AiProviderConfig[]>(`/api/organizations/${orgId}/ai-providers`);
  }

  saveAiProvider(orgId: string, data: { provider: string; api_key: string; enabled_models: string[] }) {
    return this.request<AiProviderConfig>(`/api/organizations/${orgId}/ai-providers`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  updateAiProvider(orgId: string, configId: string, data: { api_key?: string; enabled_models?: string[]; is_active?: boolean }) {
    return this.request<AiProviderConfig>(`/api/organizations/${orgId}/ai-providers/${configId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  deleteAiProvider(orgId: string, configId: string) {
    return this.request<void>(`/api/organizations/${orgId}/ai-providers/${configId}`, {
      method: "DELETE",
    });
  }

  fetchProviderModels(orgId: string, provider: string, apiKey: string) {
    return this.request<{ provider: string; models: string[]; recommended: string[]; message: string | null }>(
      `/api/organizations/${orgId}/ai-providers/fetch-models`,
      {
        method: "POST",
        body: JSON.stringify({ provider, api_key: apiKey }),
      }
    );
  }
}

export const api = new ApiClient();
