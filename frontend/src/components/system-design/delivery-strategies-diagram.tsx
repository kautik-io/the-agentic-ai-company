"use client";

import { useEffect, useState } from "react";
import { BRAND } from "@/lib/brand";
import { ClaudeIcon, GoogleIcon, OpenAIIcon, ProviderBadge } from "./provider-icons";
import {
  Bot,
  Rocket,
  Sparkles,
  TestTube2,
  Wrench,
  Zap,
} from "lucide-react";

/** LinkedIn portrait post: 1080 × 1350 px (4:5) */
const LI_WIDTH = 1080;
const LI_HEIGHT = 1350;

const PIPELINE = [
  { key: "plan", label: "Auto Plan", sub: "PM Agent", icon: Sparkles, from: "#7C3AED", to: "#4F46E5" },
  { key: "build", label: "Build", sub: "Real code", icon: Wrench, from: "#2563EB", to: "#0891B2" },
  { key: "test", label: "Test", sub: "SSH + QA", icon: TestTube2, from: "#D97706", to: "#EA580C" },
  { key: "deploy", label: "Deploy", sub: "Docker", icon: Rocket, from: "#059669", to: "#16A34A" },
] as const;

function Chip({
  children,
  active,
  glow,
  mono,
}: {
  children: React.ReactNode;
  active?: boolean;
  glow?: boolean;
  mono?: boolean;
}) {
  return (
    <span
      className={`inline-flex items-center rounded px-1 py-0.5 text-[8px] font-semibold leading-none border transition-all ${
        mono ? "font-mono" : ""
      } ${
        glow
          ? "border-emerald-500 bg-emerald-50 text-emerald-800 shadow-sm"
          : active
            ? "border-blue-500 bg-blue-50 text-blue-800"
            : "border-slate-200 bg-slate-50 text-slate-700"
      }`}
    >
      {children}
    </span>
  );
}

function StaticArrow({ dir = "right" }: { dir?: "right" | "down" }) {
  return (
    <span className="text-[9px] text-slate-400 font-bold shrink-0 px-0.5 leading-none select-none">
      {dir === "down" ? "↓" : "→"}
    </span>
  );
}

function FlowArrow({
  path,
  width,
  height,
  dots = 1,
  speed = 1.8,
  active = true,
  markerId,
  animate = true,
}: {
  path: string;
  width: number;
  height: number;
  dots?: number;
  speed?: number;
  active?: boolean;
  markerId: string;
  animate?: boolean;
}) {
  const stroke = active ? "#64748B" : "#CBD5E1";
  const showDots = animate && active && dots > 0;
  return (
    <svg width={width} height={height} className="shrink-0 overflow-hidden">
      <defs>
        <marker id={markerId} markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
          <path d="M0,0 L0,6 L6,3 z" fill={stroke} />
        </marker>
      </defs>
      <path d={path} fill="none" stroke={stroke} strokeWidth={1.5} strokeDasharray="3 3" markerEnd={`url(#${markerId})`} />
      {showDots &&
        Array.from({ length: dots }).map((_, i) => (
          <circle key={i} r={2.5} fill="#EAB308" stroke="#fff" strokeWidth={0.75}>
            <animateMotion dur={`${speed}s`} repeatCount="indefinite" path={path} begin={`${(i * speed) / dots}s`} />
          </circle>
        ))}
    </svg>
  );
}

function Panel({
  num,
  title,
  tone,
  children,
}: {
  num: string;
  title: string;
  tone: "blue" | "gold";
  children: React.ReactNode;
}) {
  const header = tone === "blue" ? "bg-[#2563EB] text-white" : "bg-[#EAB308] text-slate-900";
  return (
    <div className="relative rounded-lg border border-slate-200 bg-white overflow-hidden flex flex-col min-h-0 h-full shadow-sm isolate">
      <div className={`flex items-center gap-1.5 px-2 py-1 shrink-0 ${header}`}>
        <span className="text-[9px] font-black opacity-60">{num}</span>
        <span className="text-[10px] font-bold leading-tight truncate">{title}</span>
      </div>
      <div className="p-1.5 flex-1 flex flex-col justify-start gap-1 min-h-0 overflow-hidden bg-slate-50/50">{children}</div>
    </div>
  );
}

export function DeliveryStrategiesDiagram() {
  const [playing, setPlaying] = useState(true);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => setTick((t) => t + 1), 800);
    return () => clearInterval(id);
  }, [playing]);

  const pulse = playing;
  const activePipeline = tick % 4;

  return (
    <div className="w-full flex flex-col items-center">
      <div
        className="relative overflow-hidden shadow-xl ring-1 ring-slate-200 mx-auto bg-white"
        style={{
          width: "min(1080px, calc(100vw - 24px), calc((100vh - 56px) * 4 / 5))",
          aspectRatio: `${LI_WIDTH} / ${LI_HEIGHT}`,
        }}
      >
        {/* Subtle grid texture */}
        <div
          className="absolute inset-0 opacity-[0.35]"
          style={{
            backgroundImage: "radial-gradient(circle, #CBD5E1 1px, transparent 1px)",
            backgroundSize: "18px 18px",
          }}
        />

        <div className="absolute inset-0 flex flex-col p-3 gap-2">
          {/* Hero */}
          <div className="shrink-0 rounded-xl border border-slate-200 bg-white px-3 py-2.5 shadow-sm">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-violet-600 text-[8px] font-black text-white tracking-tighter">
                    {BRAND.short}
                  </div>
                  <div>
                    <h1 className="text-lg font-black text-slate-900 leading-none tracking-tight">{BRAND.name}</h1>
                    <p className="text-[9px] text-violet-600 font-semibold mt-0.5">{BRAND.tagline}</p>
                  </div>
                </div>
                <p className="text-[10px] text-slate-600 leading-snug max-w-[90%]">
                  Describe once → PM plans → agents code on SSH → tests pass → deploy live.
                  <span className="text-emerald-600 font-semibold"> No fake progress.</span>
                </p>
              </div>
              <button
                type="button"
                onClick={() => setPlaying(!playing)}
                className="shrink-0 rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-[9px] font-semibold text-slate-600"
              >
                {playing ? "⏸" : "▶"}
              </button>
            </div>
          </div>

          {/* Pipeline */}
          <div className="shrink-0 rounded-xl border border-slate-200 bg-white p-1.5 shadow-sm">
            <div className="flex items-center gap-0.5">
              <Zap className="h-3 w-3 text-amber-500 shrink-0 ml-1" />
              <span className="text-[8px] font-bold uppercase tracking-wider text-slate-400 mr-1">Pipeline</span>
              {PIPELINE.map((step, i) => {
                const Icon = step.icon;
                const isActive = activePipeline === i;
                return (
                  <div key={step.key} className="flex items-center flex-1 min-w-0">
                    <div
                      className={`flex-1 rounded-lg px-1 py-1.5 transition-all duration-500 border ${
                        isActive ? "border-transparent shadow-md scale-[1.02] text-white" : "border-slate-200 bg-slate-50 text-slate-700"
                      }`}
                      style={isActive ? { background: `linear-gradient(135deg, ${step.from}, ${step.to})` } : undefined}
                    >
                      <div className="flex items-center justify-center gap-1">
                        <Icon className={`h-3 w-3 ${isActive ? "text-white" : "text-slate-500"}`} />
                        <div className="text-center min-w-0">
                          <div className="text-[9px] font-bold leading-none">{step.label}</div>
                          <div className={`text-[7px] leading-none mt-0.5 ${isActive ? "text-white/80" : "text-slate-400"}`}>
                            {step.sub}
                          </div>
                        </div>
                      </div>
                    </div>
                    {i < PIPELINE.length - 1 && (
                      <FlowArrow path="M 0 5 L 10 5" width={12} height={10} active={pulse} markerId={`p-${i}`} />
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* 2×3 grid */}
          <div className="flex-1 grid grid-cols-2 grid-rows-3 gap-1.5 min-h-0 overflow-hidden">
            <Panel num="01" title="Automated Planning" tone="blue">
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-center gap-0.5 flex-wrap">
                  <Chip active={tick % 5 === 0}>You · brief</Chip>
                  <StaticArrow />
                  <Chip glow={activePipeline === 0}>PM Agent</Chip>
                </div>
                <div className="flex flex-wrap gap-0.5 justify-center">
                  <Chip active={activePipeline === 0}>design.md</Chip>
                  <Chip active={activePipeline === 1}>build</Chip>
                  <Chip active={activePipeline === 2}>QA</Chip>
                  <Chip glow={activePipeline === 3}>deploy</Chip>
                </div>
                <p className="text-[7px] text-slate-500 text-center font-mono leading-tight">epics → features → tasks</p>
              </div>
            </Panel>

            <Panel num="02" title="Multi-Model Agents" tone="gold">
              <div className="flex flex-col gap-1 items-center">
                <div className="flex justify-between w-full px-0.5">
                  <ProviderBadge icon={<OpenAIIcon size={22} />} company="OpenAI" />
                  <ProviderBadge icon={<ClaudeIcon size={22} />} company="Claude" />
                  <ProviderBadge icon={<GoogleIcon size={22} />} company="Google" />
                </div>
                <StaticArrow dir="down" />
                <Chip active={tick % 5 === 1}>
                  <Bot className="h-2 w-2 mr-0.5 inline" />
                  Orchestrator
                </Chip>
              </div>
            </Panel>

            <Panel num="03" title="Auto-Start Engine" tone="blue">
              <div className="flex flex-col gap-1 items-center">
                <Chip glow={tick % 5 === 2}>plan → READY</Chip>
                <StaticArrow dir="down" />
                <div className="flex items-center gap-0.5 flex-wrap justify-center">
                  <Chip active>orchestrator</Chip>
                  <StaticArrow />
                  <Chip glow>parallel</Chip>
                </div>
                <p className="text-[7px] text-emerald-600 text-center font-semibold leading-tight">instant · zero wait</p>
              </div>
            </Panel>

            <Panel num="04" title="Build → Test Loop" tone="gold">
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-center gap-0.5 flex-wrap">
                  <Chip mono active={tick % 4 === 0}>spec</Chip>
                  <StaticArrow />
                  <Chip mono glow={activePipeline === 1}>code</Chip>
                  <StaticArrow />
                  <Chip mono glow={activePipeline === 2}>test</Chip>
                </div>
                <div className="rounded border border-dashed border-amber-400 bg-amber-50 px-1.5 py-0.5">
                  <p className="text-[7px] text-amber-800 text-center leading-tight">
                    fix unlocks on FAIL
                  </p>
                </div>
              </div>
            </Panel>

            <Panel num="05" title="SSH Workspace" tone="blue">
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-center gap-0.5 flex-wrap">
                  <Chip active>agent</Chip>
                  <StaticArrow />
                  <Chip mono>ssh://host</Chip>
                </div>
                <div className="w-full rounded-md border border-cyan-200 bg-gradient-to-br from-white to-cyan-50/70 px-1.5 py-1">
                  <div className="flex items-center gap-1 mb-1">
                    <span className="h-1 w-1 rounded-full bg-rose-400" />
                    <span className="h-1 w-1 rounded-full bg-amber-400" />
                    <span className="h-1 w-1 rounded-full bg-emerald-400" />
                    <span className="text-[6px] font-semibold text-cyan-700">ssh session</span>
                  </div>
                  <div className="space-y-0.5 font-mono text-[7px] leading-tight">
                    <div className="rounded bg-white border border-slate-200 px-1 py-0.5 text-slate-700">
                      <span className="text-blue-500">→</span> write <span className="text-violet-600">index.html</span>
                    </div>
                    <div className="rounded bg-white border border-slate-200 px-1 py-0.5 text-slate-700">
                      <span className="text-blue-500">→</span> docker compose <span className="text-cyan-600">up</span>
                    </div>
                    <div
                      className={`rounded px-1 py-0.5 border font-semibold ${
                        tick % 2 === 0
                          ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                          : "bg-rose-50 border-rose-200 text-rose-700"
                      }`}
                    >
                      {tick % 2 === 0 ? "✓ tests passed" : "↻ retry fix"}
                    </div>
                  </div>
                </div>
              </div>
            </Panel>

            <Panel num="06" title="Deploy & Monitor" tone="gold">
              <div className="flex flex-col gap-1 items-center">
                <div className="flex items-center gap-0.5">
                  <Chip glow={activePipeline === 3}>deploy</Chip>
                  <StaticArrow />
                  <Chip active>live UI</Chip>
                </div>
                <div className="flex flex-wrap gap-0.5 justify-center">
                  <Chip>Kanban</Chip>
                  <Chip active={tick % 3 === 0}>logs</Chip>
                  <Chip>shots</Chip>
                </div>
                <p className="text-[7px] text-slate-500 text-center leading-tight">live activity feed</p>
              </div>
            </Panel>
          </div>

          {/* Footer */}
          <div className="shrink-0 rounded-xl border border-violet-200 bg-gradient-to-r from-violet-50 via-blue-50 to-emerald-50 px-3 py-2 flex items-center justify-between gap-2">
            <div>
              <p className="text-[10px] font-black text-slate-900 leading-none">Idea → Production</p>
              <p className="text-[8px] text-slate-500 mt-0.5">One platform · real agents · real servers</p>
            </div>
            <div className="flex gap-1 shrink-0">
              <Chip mono>FastAPI</Chip>
              <Chip mono>Next.js</Chip>
              <Chip mono>Docker</Chip>
              <Chip mono>SSH</Chip>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
