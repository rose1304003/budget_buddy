import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2, Plus, ArrowDownRight, ArrowUpRight } from "lucide-react";
import { api, Tx, ApiError } from "../lib/api";
import { Card } from "../ui/Card";
import { Button } from "../ui/Button";
import { formatUZS } from "../utils/money";
import { useToast } from "../ui/Toast";
import { haptic } from "../lib/telegram";

export default function TransactionsPage() {
  const qc = useQueryClient();
  const toast = useToast();
  const catQ = useQuery({ queryKey: ["cats"], queryFn: api.categories });
  const txQ = useQuery({ queryKey: ["tx", 50], queryFn: () => api.transactions(50) });

  const [type, setType] = useState<"expense" | "income">("expense");
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [categoryId, setCategoryId] = useState<number | "">("");

  const createM = useMutation({
    mutationFn: () =>
      api.createTx({
        type,
        amount: Number(amount || 0),
        note,
        category_id: categoryId === "" ? null : categoryId,
      }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["tx"] });
      await qc.invalidateQueries({ queryKey: ["stats"] });
      setAmount("");
      setNote("");
      setCategoryId("");
      haptic("light");
      toast.push({ title: "Saved ✅", kind: "success" });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
          ? error.message
          : "Failed to save transaction";
      toast.push({ title: message, kind: "error" });
    },
  });

  const delM = useMutation({
    mutationFn: (id: number) => api.deleteTx(id),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["tx"] });
      await qc.invalidateQueries({ queryKey: ["stats"] });
      toast.push({ title: "Deleted", kind: "info" });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
          ? error.message
          : "Failed to delete transaction";
      toast.push({ title: message, kind: "error" });
    },
  });

  const cats = useMemo(() => (catQ.data || []).filter(c => c.kind === (type === "expense" ? "expense" : "income") && c.is_active), [catQ.data, type]);

  return (
    <div className="space-y-4">
      <header>
        <p className="text-muted text-sm">Wallet</p>
        <h1 className="text-2xl font-semibold tracking-tight">Add transaction</h1>
      </header>

      <Card className="p-4 space-y-3">
        <div className="grid grid-cols-2 gap-2">
          <button className={`tap rounded-2xl border border-border p-3 text-sm font-medium ${type==="expense" ? "text-danger bg-bg/40" : "text-muted hover:text-fg"}`}
            onClick={() => setType("expense")}>
            <span className="inline-flex items-center gap-2"><ArrowDownRight size={16}/> Expense</span>
          </button>
          <button className={`tap rounded-2xl border border-border p-3 text-sm font-medium ${type==="income" ? "text-accent bg-bg/40" : "text-muted hover:text-fg"}`}
            onClick={() => setType("income")}>
            <span className="inline-flex items-center gap-2"><ArrowUpRight size={16}/> Income</span>
          </button>
        </div>

        <label className="block">
          <span className="text-xs text-muted">Amount (UZS)</span>
          <input className="mt-1 w-full h-12 rounded-2xl border border-border bg-bg/40 px-4 text-base outline-none focus:ring-2 focus:ring-accent/40"
            inputMode="numeric" value={amount} onChange={e => setAmount(e.target.value.replace(/[^0-9]/g,""))} placeholder="e.g. 30000" />
        </label>

        <label className="block">
          <span className="text-xs text-muted">Category</span>
          <select className="mt-1 w-full h-12 rounded-2xl border border-border bg-bg/40 px-4 text-sm outline-none focus:ring-2 focus:ring-accent/40"
            value={categoryId} onChange={e => setCategoryId(e.target.value ? Number(e.target.value) : "")}>
            <option value="">No category</option>
            {cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </label>

        <label className="block">
          <span className="text-xs text-muted">Note</span>
          <input className="mt-1 w-full h-12 rounded-2xl border border-border bg-bg/40 px-4 text-sm outline-none focus:ring-2 focus:ring-accent/40"
            value={note} onChange={e => setNote(e.target.value)} placeholder="e.g. Taxi, groceries..." />
        </label>

        <Button onClick={() => createM.mutate()} disabled={!amount || Number(amount)<=0 || createM.isPending} className="w-full" size="lg">
          <Plus size={18}/> Save transaction
        </Button>
      </Card>

      <section className="space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold">Transactions</h2>
          <span className="text-muted text-sm">{txQ.isLoading ? "Loading..." : ""}</span>
        </div>

        <Card className="overflow-hidden">
          {txQ.data?.length ? txQ.data.map((t,i) => (
            <Row key={t.id} t={t} divider={i!==0} onDelete={() => delM.mutate(t.id)} />
          )) : <div className="p-4"><p className="text-sm text-muted">No transactions yet.</p></div>}
        </Card>
      </section>
    </div>
  );
}

function Row({ t, divider, onDelete }: { t: Tx; divider: boolean; onDelete: () => void }) {
  return (
    <div className={`px-4 py-3 flex items-center justify-between ${divider ? "border-t border-border" : ""}`}>
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{t.note || (t.type==="expense" ? "Expense" : "Income")}</p>
        <p className="text-xs text-muted">{t.occurred_at ? new Date(t.occurred_at).toLocaleString() : ""}</p>
      </div>
      <div className="flex items-center gap-3">
        <p className={`text-sm font-semibold ${t.type==="expense" ? "text-danger" : "text-accent"}`}>
          {t.type==="expense" ? "-" : "+"}{formatUZS(t.amount)}
        </p>
        <button className="tap h-10 w-10 rounded-2xl border border-border grid place-items-center text-muted hover:text-fg" onClick={onDelete}>
          <Trash2 size={18}/>
        </button>
      </div>
    </div>
  );
}
