"use client";

import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface PageLoaderProps {
  label?: string;
  className?: string;
}

export function PageLoader({ label = "Loading...", className }: PageLoaderProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-3 p-12 text-muted-foreground", className)}>
      <Loader2 className="h-8 w-8 animate-spin text-primary" aria-hidden />
      <p className="text-sm">{label}</p>
    </div>
  );
}
