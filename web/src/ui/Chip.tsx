import { cn } from "./cn";
export function Chip({ className, tone="muted", ...props }: React.HTMLAttributes<HTMLSpanElement> & { tone?: "muted"|"accent" }) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-1 text-xs border",
      tone==="accent" ? "border-accent/40 text-accent" : "border-border text-muted",
      className)} {...props} />
  );
}
