"use client";

import { useEffect, useId, useRef } from "react";

interface LogicGraphViewerProps {
  chart: string;
  className?: string;
}

export function LogicGraphViewer({ chart, className }: LogicGraphViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const id = useId().replace(/:/g, "");

  useEffect(() => {
    let cancelled = false;

    async function render() {
      if (!chart || !containerRef.current) return;
      const mermaid = (await import("mermaid")).default;
      mermaid.initialize({
        startOnLoad: false,
        theme: "dark",
        securityLevel: "loose",
        flowchart: { curve: "basis" },
      });
      if (cancelled || !containerRef.current) return;
      try {
        const { svg } = await mermaid.render(`graph-${id}`, chart);
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      } catch {
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = `<pre class="text-xs text-muted-foreground overflow-auto p-4">${chart}</pre>`;
        }
      }
    }

    render();
    return () => {
      cancelled = true;
    };
  }, [chart, id]);

  return (
    <div
      ref={containerRef}
      className={`rounded-lg border border-border bg-card/50 p-4 overflow-auto min-h-[200px] ${className ?? ""}`}
    />
  );
}
