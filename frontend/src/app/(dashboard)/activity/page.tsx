"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { api, Activity } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";

export default function ActivityPage() {
  const { org } = useAuth();
  const [activities, setActivities] = useState<Activity[]>([]);

  useEffect(() => {
    if (!org) return;
    api.listActivities(org.id, 100).then(setActivities).catch(console.error);
    const interval = setInterval(() => {
      api.listActivities(org.id, 100).then(setActivities).catch(console.error);
    }, 10000);
    return () => clearInterval(interval);
  }, [org]);

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Live Activity</h1>
        <p className="text-muted-foreground">Real-time event feed — WebSocket in Phase 7</p>
      </div>
      <Card>
        <CardHeader><CardTitle>Activity Timeline</CardTitle></CardHeader>
        <div className="space-y-3">
          {activities.map((a) => (
            <div key={a.id} className="flex gap-4 border-b border-border pb-3 last:border-0">
              <span className="text-sm text-muted-foreground whitespace-nowrap w-24">
                {new Date(a.created_at).toLocaleString()}
              </span>
              <span className="text-xs uppercase text-primary w-32">{a.event_type}</span>
              <span className="text-sm">{a.message}</span>
            </div>
          ))}
          {activities.length === 0 && (
            <p className="text-muted-foreground text-sm">No activity recorded yet.</p>
          )}
        </div>
      </Card>
    </div>
  );
}
