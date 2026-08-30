"use client";

import { Card, CardHeader, CardTitle } from "@/components/ui/card";

export default function PlaceholderPage({ title, phase }: { title: string; phase: string }) {
  return (
    <div className="p-8">
      <Card className="max-w-lg">
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <p className="text-muted-foreground">
          This feature is planned for {phase}. The navigation and API foundation are in place.
        </p>
      </Card>
    </div>
  );
}
