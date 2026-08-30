"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Building2,
  FolderKanban,
  Bot,
  ListTodo,
  Activity,
  Settings,
  LogOut,
  Workflow,
  DollarSign,
  Bell,
  Rocket,
  Network,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth-context";
import { BRAND } from "@/lib/brand";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/agents", label: "AI Employees", icon: Bot },
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/tasks", label: "Tasks", icon: ListTodo },
  { href: "/workflows", label: "Workflows", icon: Workflow },
  { href: "/activity", label: "Live Activity", icon: Activity },
  { href: "/deployments", label: "Deployments", icon: Rocket },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/costs", label: "AI Costs", icon: DollarSign },
  { href: "/company", label: "Company", icon: Building2 },
  { href: "/system-design", label: "System Design", icon: Network },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { org, orgs, setOrg, logout, user } = useAuth();

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-border bg-card">
      <div className="border-b border-border p-5">
        <h1 className="text-lg font-bold tracking-tight">{BRAND.short}</h1>
        <p className="text-xs text-muted-foreground mt-0.5">{BRAND.name}</p>
      </div>

      {orgs.length > 0 && (
        <div className="border-b border-border p-3">
          <label className="text-xs text-muted-foreground mb-1 block">Organization</label>
          <select
            value={org?.id || ""}
            onChange={(e) => {
              const selected = orgs.find((o) => o.id === e.target.value);
              if (selected) setOrg(selected);
            }}
            className="w-full rounded-lg border border-border bg-background px-2 py-1.5 text-sm"
          >
            {orgs.map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>
        </div>
      )}

      <nav className="flex-1 overflow-y-auto p-3 space-y-0.5">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
              pathname === href
                ? "bg-primary/10 text-primary font-medium"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>

      <div className="border-t border-border p-4">
        <p className="text-sm font-medium truncate">{user?.full_name}</p>
        <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
        <button
          onClick={logout}
          className="mt-3 flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
