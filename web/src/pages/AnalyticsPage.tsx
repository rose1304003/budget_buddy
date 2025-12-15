import { useQuery } from "@tanstack/react-query";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";
import { api } from "../lib/api";
import { Card } from "../ui/Card";
import { formatUZS } from "../utils/money";

export default function AnalyticsPage() {
  const sQ = useQuery({ queryKey: ["stats"], queryFn: api.stats });
  const s = sQ.data;

  const data = [
    { name: "Week", income: s?.week_income ?? 0, expense: s?.week_spent ?? 0 },
    { name: "Month", income: s?.month_income ?? 0, expense: s?.month_spent ?? 0 },
  ];

  return (
    <div className="space-y-4">
      <header>
        <p className="text-muted text-sm">Analytics</p>
        <h1 className="text-2xl font-semibold tracking-tight">Trends & summary</h1>
      </header>

      <Card className="p-4 space-y-3">
        <div className="flex items-end justify-between">
          <div>
            <p className="text-xs text-muted">Balance</p>
            <p className="text-2xl font-semibold">{s ? formatUZS(s.balance) : "—"}</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-muted">Monthly net</p>
            <p className="text-base font-semibold text-accent">{s ? (s.month_income - s.month_spent >= 0 ? "+" : "") + formatUZS(s.month_income - s.month_spent) : "—"}</p>
          </div>
        </div>

        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <XAxis dataKey="name" stroke="rgba(162,179,194,.6)" />
              <YAxis stroke="rgba(162,179,194,.6)" />
              <Tooltip contentStyle={{ background: "rgba(20,28,45,.95)", border: "1px solid rgba(45,58,80,1)", borderRadius: 16 }} />
              <Bar dataKey="income" />
              <Bar dataKey="expense" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}
