import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ErrorBannerProps {
  message: string;
  className?: string;
}

export function ErrorBanner({ message, className }: ErrorBannerProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 flex items-start gap-3 text-sm text-red-200",
        className
      )}
      role="alert"
    >
      <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" aria-hidden />
      <p>{message}</p>
    </div>
  );
}
