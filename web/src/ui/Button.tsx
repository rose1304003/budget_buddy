import { cn } from "./cn";

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
};

export function Button({ className, variant="primary", size="md", ...props }: Props) {
  const base = "tap inline-flex items-center justify-center gap-2 rounded-2xl font-medium outline-none focus:ring-2 focus:ring-accent/40 disabled:opacity-50 disabled:pointer-events-none";
  const variants: Record<string,string> = {
    primary: "bg-accent text-bg shadow-glow",
    ghost: "bg-transparent border border-border text-fg hover:bg-card/40",
    danger: "bg-danger text-bg shadow-soft",
  };
  const sizes: Record<string,string> = { sm: "h-9 px-3 text-sm", md: "h-11 px-4 text-sm", lg: "h-12 px-5 text-base" };
  return <button className={cn(base, variants[variant], sizes[size], className)} {...props} />;
}
