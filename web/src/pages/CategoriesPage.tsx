import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, EyeOff, Eye } from "lucide-react";
import { api, Category, ApiError } from "../lib/api";
import { Card } from "../ui/Card";
import { Button } from "../ui/Button";
import { useToast } from "../ui/Toast";
import { haptic } from "../lib/telegram";

export default function CategoriesPage() {
  const qc = useQueryClient();
  const toast = useToast();
  const q = useQuery({ queryKey: ["cats"], queryFn: api.categories });

  const [kind, setKind] = useState<"expense"|"income"|"debt">("expense");
  const [name, setName] = useState("");

  const createM = useMutation({
    mutationFn: () =>
      api.createCategory({ name, kind, color: "#22d3ee", icon: "tag" }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["cats"] });
      setName("");
      haptic("light");
      toast.push({ title: "Category added ✅", kind: "success" });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
          ? error.message
          : "Failed to create category";
      toast.push({ title: message, kind: "error" });
    },
  });

  const patchM = useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: number;
      payload: Partial<Category>;
    }) => api.patchCategory(id, payload),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["cats"] });
      toast.push({ title: "Updated", kind: "info" });
    },
    onError: (error: unknown) => {
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
          ? error.message
          : "Failed to update category";
      toast.push({ title: message, kind: "error" });
    },
  });

  const items = useMemo(() => (q.data || []).filter(c => c.kind === kind).sort((a,b)=>a.name.localeCompare(b.name)), [q.data, kind]);

  return (
    <div className="space-y-4">
      <header>
        <p className="text-muted text-sm">Categories</p>
        <h1 className="text-2xl font-semibold tracking-tight">Manage categories</h1>
      </header>

      <Card className="p-4 space-y-3">
        <div className="grid grid-cols-3 gap-2">
          {(["expense","income","debt"] as const).map(k => (
            <button key={k} className={`tap rounded-2xl border border-border p-3 text-sm font-medium ${kind===k ? "text-accent bg-bg/40" : "text-muted hover:text-fg"}`}
              onClick={()=>setKind(k)}>{k}</button>
          ))}
        </div>

        <label className="block">
          <span className="text-xs text-muted">New category name</span>
          <input className="mt-1 w-full h-12 rounded-2xl border border-border bg-bg/40 px-4 text-sm outline-none focus:ring-2 focus:ring-accent/40"
            value={name} onChange={e=>setName(e.target.value)} placeholder="e.g. Books, Taxi, Electricity..." />
        </label>

        <Button onClick={()=>createM.mutate()} disabled={!name.trim() || createM.isPending} className="w-full">
          <Plus size={18}/> Add category
        </Button>
      </Card>

      <Card className="overflow-hidden">
        {items.length ? items.map((c,i)=>(
          <Row key={c.id} c={c} divider={i!==0}
            onRename={()=>{ const next=prompt("Rename category", c.name); if(next && next.trim() && next!==c.name) patchM.mutate({ id:c.id, payload:{ name: next.trim() } }); }}
            onToggle={()=>patchM.mutate({ id:c.id, payload:{ is_active: !c.is_active } })}
          />
        )) : <div className="p-4"><p className="text-sm text-muted">No categories yet.</p></div>}
      </Card>
    </div>
  );
}

function Row({ c, divider, onRename, onToggle }: { c: Category; divider:boolean; onRename:()=>void; onToggle:()=>void }) {
  return (
    <div className={`px-4 py-3 flex items-center justify-between ${divider ? "border-t border-border" : ""}`}>
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{c.name}</p>
        <p className="text-xs text-muted">{c.is_active ? "Active" : "Hidden"}</p>
      </div>
      <div className="flex items-center gap-2">
        <button className="tap h-10 w-10 rounded-2xl border border-border grid place-items-center text-muted hover:text-fg" onClick={onRename}><Pencil size={18}/></button>
        <button className="tap h-10 w-10 rounded-2xl border border-border grid place-items-center text-muted hover:text-fg" onClick={onToggle}>
          {c.is_active ? <EyeOff size={18}/> : <Eye size={18}/>}
        </button>
      </div>
    </div>
  );
}
