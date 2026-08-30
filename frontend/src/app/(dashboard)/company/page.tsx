"use client";

import { useAuth } from "@/lib/auth-context";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";

export default function CompanyPage() {
  const { org } = useAuth();
  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Company</h1>
        <p className="text-muted-foreground">Organization settings and departments</p>
      </div>
      {org && (
        <Card>
          <CardHeader><CardTitle>{org.name}</CardTitle></CardHeader>
          <p className="text-muted-foreground">{org.description || "No description"}</p>
          <p className="text-sm text-muted-foreground mt-2">Slug: {org.slug}</p>
        </Card>
      )}
    </div>
  );
}
