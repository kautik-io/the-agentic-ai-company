"use client";

import { DeliveryStrategiesDiagram } from "@/components/system-design/delivery-strategies-diagram";
import Link from "next/link";

/** Public page — no login required (LinkedIn reference / screenshots) */
export default function SystemDesignPage() {
  return (
    <div className="min-h-screen w-full bg-slate-100 flex flex-col items-center justify-center p-3 overflow-auto">
      <DeliveryStrategiesDiagram />
      <div className="mt-3 flex items-center gap-3 text-[10px] text-slate-500">
        <span>1080 × 1350 · screenshot for LinkedIn</span>
        <Link href="/dashboard" className="text-blue-500 hover:underline">
          Open app →
        </Link>
      </div>
    </div>
  );
}
