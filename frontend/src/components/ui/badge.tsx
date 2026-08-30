import { cn, statusColor } from "@/lib/utils";

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
        "bg-muted text-foreground",
        className
      )}
    >
      <span className={cn("h-2 w-2 rounded-full", statusColor(status))} />
      {status.replace(/_/g, " ").toUpperCase()}
    </span>
  );
}

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  variant?: "default" | "success" | "warning" | "danger";
}

export function StatCard({ title, value, subtitle, variant = "default" }: StatCardProps) {
  const borderColors = {
    default: "border-border",
    success: "border-emerald-500/30",
    warning: "border-amber-500/30",
    danger: "border-red-500/30",
  };
  return (
    <div className={cn("rounded-xl border bg-card p-5", borderColors[variant])}>
      <p className="text-sm text-muted-foreground">{title}</p>
      <p className="mt-1 text-3xl font-bold">{value}</p>
      {subtitle && <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>}
    </div>
  );
}
