import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Plus, Sparkles, ArrowDownRight, ArrowUpRight } from "lucide-react";
import { api } from "../lib/api";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { Chip } from "../ui/Chip";
import { formatUZS } from "../utils/money";
import { useToast } from "../ui/Toast";
import { haptic } from "../lib/telegram";

export default function HomePage() {
  const toast = useToast();
  const meQ = useQuery({ queryKey: ["me"], queryFn: api.me });
  const statsQ = useQuery({ queryKey: ["stats"], queryFn: api.stats });
  const txQ = useQuery({ queryKey: ["tx", 8], queryFn: () => api.transactions(8) });

  const me = meQ.data;
  const s = statsQ.data;

  return (
    <div className="space-y-4">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-muted text-sm">Hello{me?.first_name ? `, ${me.first_name}` : ""}</p>
          <h1 className="text-2xl font-semibold tracking-tight">Your budget dashboard</h1>
        </div>
        <div className="h-11 w-11 rounded-2xl bg-card border border-border grid place-items-center shadow-soft">
          <span className="text-sm text-muted">{me?.first_name?.[0] ?? "T"}</span>
        </div>
      </header>

      <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
        <div className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_30%_20%,rgba(34,211,238,.35),transparent_45%),radial-gradient(circle_at_80%_70%,rgba(34,211,238,.15),transparent_50%)]" />
        <div className="relative p-4">
          <div className="flex items-center justify-between">
            <div className="inline-flex items-center gap-2 text-accent text-sm">
              <Sparkles size={16} /> Smart expense tracker
            </div>
            <Button onClick={() => { haptic("light"); toast.push({ title: "Use “Wallet” tab to add transactions ✨" }); }}
              className="rounded-full" size="sm">
              <Plus size={16} /> Add
            </Button>
          </div>

          <div className="mt-4">
            <p className="text-muted text-sm">Current balance</p>
            <p className="text-3xl font-semibold tracking-tight">{s ? formatUZS(s.balance) : "—"}</p>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-3">
            <MiniStat label="This week spent" value={s ? formatUZS(s.week_spent) : "—"} tone="danger" icon={<ArrowDownRight size={18} />} />
            <MiniStat label="This week income" value={s ? formatUZS(s.week_income) : "—"} tone="good" icon={<ArrowUpRight size={18} />} />
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <Chip tone="accent">Monthly net: {s ? (s.month_income - s.month_spent >= 0 ? "+" : "") + formatUZS(s.month_income - s.month_spent) : "—"}</Chip>
            <Chip>Secure initData auth</Chip>
          </div>
        </div>
      </motion.section>

      <section className="space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold">Recent activity</h2>
        </div>

        <Card className="overflow-hidden">
          {txQ.data?.length ? (
            txQ.data.map((t, i) => (
              <div key={t.id} className={`px-4 py-3 flex items-center justify-between ${i!==0 ? "border-t border-border" : ""}`}>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{t.note || (t.type==="expense" ? "Expense" : "Income")}</p>
                  <p className="text-xs text-muted">{t.occurred_at ? new Date(t.occurred_at).toLocaleString() : ""}</p>
                </div>
                <p className={`text-sm font-semibold ${t.type==="expense" ? "text-danger" : "text-accent"}`}>
                  {t.type==="expense" ? "-" : "+"}{formatUZS(t.amount)}
                </p>
              </div>
            ))
          ) : (
            <div className="p-4"><p className="text-sm text-muted">No transactions yet. Add your first one in the Wallet tab.</p></div>
          )}
        </Card>
      </section>
    </div>
  );
}

function MiniStat({ label, value, icon, tone }: { label: string; value: string; icon: React.ReactNode; tone: "danger"|"good" }) {
  return (
    <div className="rounded-2xl border border-border bg-bg/40 p-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted">{label}</p>
        <div className={`h-9 w-9 rounded-xl grid place-items-center border border-border ${tone==="danger" ? "text-danger" : "text-accent"}`}>{icon}</div>
      </div>
      <p className="mt-2 text-base font-semibold">{value}</p>
    </div>
  );
}
