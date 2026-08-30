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
  name: string;
  role: string;
  description: string | null;
  responsibilities: string[];
  skills: string[];
  ai_provider: string;
  ai_model: string;
  temperature: number;
  status: string;
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
  status: string;
  created_at: string;
  updated_at: string;
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

export interface Task {
  id: string;
  project_id: string;
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
  created_at: string;
  updated_at: string;
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

  hireAgent(orgId: string, data: Partial<Agent> & { name: string; role: string }) {
    return this.request<Agent>(`/api/organizations/${orgId}/agents`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  listProjects(orgId: string) {
    return this.request<Project[]>(`/api/organizations/${orgId}/projects`);
  }

  createProject(orgId: string, data: { name: string; description?: string }) {
    return this.request<Project>(`/api/organizations/${orgId}/projects`, {
      method: "POST",
      body: JSON.stringify(data),
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
}

export const api = new ApiClient();
