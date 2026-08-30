import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatStatus(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function statusColor(status: string): string {
  const map: Record<string, string> = {
    idle: "bg-slate-500",
    working: "bg-emerald-500",
    analyzing: "bg-blue-500",
    testing: "bg-purple-500",
    reviewing: "bg-indigo-500",
    waiting: "bg-amber-500",
    waiting_for_agent: "bg-amber-500",
    blocked: "bg-red-500",
    failed: "bg-red-600",
    escalated: "bg-orange-500",
    completed: "bg-emerald-600",
    offline: "bg-gray-600",
    in_progress: "bg-blue-500",
    backlog: "bg-slate-600",
    ready: "bg-sky-500",
    in_review: "bg-indigo-500",
    changes_requested: "bg-orange-500",
    high: "bg-orange-500",
    critical: "bg-red-500",
    medium: "bg-blue-500",
    low: "bg-slate-500",
  };
  return map[status] || "bg-slate-500";
}
