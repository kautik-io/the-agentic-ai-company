/** Provider brand icons — product/company names for system design */

const OPENAI_PATH =
  "M14.949 6.547a3.94 3.94 0 0 0-.348-3.273 4.11 4.11 0 0 0-4.4-1.934A4.1 4.1 0 0 0 8.423.2 4.15 4.15 0 0 0 6.305.086a4.1 4.1 0 0 0-1.891.948 4.04 4.04 0 0 0-1.158 1.753 4.1 4.1 0 0 0-1.563.679A4 4 0 0 0 .554 4.72a3.99 3.99 0 0 0 .502 4.731 3.94 3.94 0 0 0 .346 3.274 4.11 4.11 0 0 0 4.402 1.933c.382.425.852.764 1.377.995.526.231 1.095.35 1.67.346 1.78.002 3.358-1.132 3.901-2.804a4.1 4.1 0 0 0 1.563-.68 4 4 0 0 0 1.14-1.253 3.99 3.99 0 0 0-.506-4.716m-6.097 8.406a3.05 3.05 0 0 1-1.945-.694l.096-.054 3.23-1.838a.53.53 0 0 0 .265-.455v-4.49l1.366.778q.02.011.025.035v3.722c-.003 1.653-1.361 2.992-3.037 2.996m-6.53-2.75a2.95 2.95 0 0 1-.36-2.01l.095.057L5.29 12.09a.53.53 0 0 0 .527 0l3.949-2.246v1.555a.05.05 0 0 1-.022.041L6.473 13.3c-1.454.826-3.311.335-4.15-1.098m-.85-6.94A3.02 3.02 0 0 1 3.07 3.949v3.785a.51.51 0 0 0 .262.451l3.93 2.237-1.366.779a.05.05 0 0 1-.048 0L2.585 9.342a2.98 2.98 0 0 1-1.113-4.094zm11.216 2.571L8.747 5.576l1.362-.776a.05.05 0 0 1 .048 0l3.265 1.86a3 3 0 0 1 1.173 1.207 2.96 2.96 0 0 1-.27 3.2 3.05 3.05 0 0 1-1.36.997V8.279a.52.52 0 0 0-.276-.445m1.36-2.015-.097-.057-3.226-1.855a.53.53 0 0 0-.53 0L6.249 6.153V4.598a.04.04 0 0 1 .019-.04L9.533 2.7a3.07 3.07 0 0 1 3.257.139c.474.325.843.778 1.066 1.303.223.526.289 1.103.191 1.664zM5.503 8.575 4.139 7.8a.05.05 0 0 1-.026-.037V4.049c0-.57.166-1.127.476-1.607s.752-.864 1.275-1.105a3.08 3.08 0 0 1 3.234.41l-.096.054-3.23 1.838a.53.53 0 0 0-.265.455zm.742-1.577 1.758-1 1.762 1v2l-1.755 1-1.762-1z";

const GEMINI_PATH =
  "M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96 2.19.93 3.81 2.55t2.55 3.81";

/** OpenAI — blossom knot */
export function OpenAIIcon({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-label="OpenAI" role="img">
      <rect width="32" height="32" rx="7" fill="#10A37F" />
      <path fill="#fff" transform="translate(4 4) scale(1.5)" d={OPENAI_PATH} />
    </svg>
  );
}

/** Claude — coral starburst mark */
export function ClaudeIcon({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-label="Claude" role="img">
      <rect width="32" height="32" rx="7" fill="#D97757" />
      <g fill="#FAF0EB" transform="translate(16 16)">
        <rect x="-1.1" y="-9" width="2.2" height="18" rx="1.1" />
        <rect x="-1.1" y="-9" width="2.2" height="18" rx="1.1" transform="rotate(45)" />
        <rect x="-1.1" y="-9" width="2.2" height="18" rx="1.1" transform="rotate(90)" />
        <rect x="-1.1" y="-9" width="2.2" height="18" rx="1.1" transform="rotate(135)" />
        <rect x="-1.1" y="-6.5" width="2.2" height="13" rx="1.1" transform="rotate(22.5)" />
        <rect x="-1.1" y="-6.5" width="2.2" height="13" rx="1.1" transform="rotate(67.5)" />
        <rect x="-1.1" y="-6.5" width="2.2" height="13" rx="1.1" transform="rotate(112.5)" />
        <rect x="-1.1" y="-6.5" width="2.2" height="13" rx="1.1" transform="rotate(157.5)" />
      </g>
    </svg>
  );
}

/** Google Gemini — sparkle mark */
export function GoogleIcon({ size = 28 }: { size?: number }) {
  const id = `gemini-grad-${size}`;
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-label="Google" role="img">
      <defs>
        <linearGradient id={id} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4285F4" />
          <stop offset="50%" stopColor="#9B72F2" />
          <stop offset="100%" stopColor="#D96570" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="7" fill="#fff" stroke="#E2E8F0" strokeWidth="0.5" />
      <path fill={`url(#${id})`} transform="translate(4 4) scale(1)" d={GEMINI_PATH} />
    </svg>
  );
}

/** @deprecated use ClaudeIcon */
export const AnthropicIcon = ClaudeIcon;

/** @deprecated use GoogleIcon */
export const GeminiIcon = GoogleIcon;

export function ProviderBadge({ icon, company }: { icon: React.ReactNode; company: string }) {
  return (
    <div className="flex flex-col items-center gap-1 min-w-0">
      {icon}
      <span className="text-[9px] font-bold text-slate-800 leading-none">{company}</span>
    </div>
  );
}
