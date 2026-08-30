"use client";

import { useState } from "react";
import { Task, api } from "@/lib/api";
import { captureViewportScreenshot } from "@/lib/screenshot";
import { Button } from "@/components/ui/button";
import { Camera, CheckCircle2, Loader2 } from "lucide-react";

interface Props {
  orgId: string;
  projectId: string;
  task: Task;
  onDone: () => void;
}

const COMPLETABLE = new Set(["ready", "in_progress", "testing", "in_review"]);

export function TaskCompleteButton({ orgId, projectId, task, onDone }: Props) {
  const [loading, setLoading] = useState(false);

  if (task.status === "completed") return null;
  if (!COMPLETABLE.has(task.status)) return null;

  const handleComplete = async () => {
    setLoading(true);
    try {
      const blob = await captureViewportScreenshot();
      await api.completeTaskWithScreenshot(orgId, projectId, task.id, blob, task.title);
      onDone();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to complete task");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      size="sm"
      variant="outline"
      className="mt-2 w-full text-xs"
      onClick={handleComplete}
      disabled={loading}
    >
      {loading ? (
        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
      ) : (
        <Camera className="h-3 w-3 mr-1" />
      )}
      {loading ? "Capturing..." : "Complete + Screenshot"}
    </Button>
  );
}

export function TaskScreenshotThumb({ url, title }: { url: string; title: string }) {
  const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
  const fullUrl = url.startsWith("http") ? url : `${base}${url}`;
  const isUi = /working|preview|login|ui/i.test(title);
  return (
    <a href={fullUrl} target="_blank" rel="noopener noreferrer" className="block mt-2 group">
      <img
        src={fullUrl}
        alt={title}
        className="rounded border border-border w-full h-24 object-cover object-top group-hover:opacity-90"
      />
      <span className="text-[10px] text-muted-foreground flex items-center gap-1 mt-1">
        <CheckCircle2 className="h-3 w-3 text-green-400" />
        {isUi ? "Working UI screenshot" : "AI output screenshot"}
      </span>
    </a>
  );
}
