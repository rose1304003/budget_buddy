import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

type Toast = { id: string; title: string; kind?: "info"|"error"|"success" };
const Ctx = createContext<{ push: (t: Omit<Toast,"id">) => void } | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const push = useCallback((t: Omit<Toast,"id">) => {
    const id = crypto.randomUUID();
    setItems(s => [...s, { id, ...t }]);
    setTimeout(() => setItems(s => s.filter(x => x.id !== id)), 2400);
  }, []);
  const value = useMemo(() => ({ push }), [push]);

  return (
    <Ctx.Provider value={value}>
      {children}
      <div className="fixed top-3 left-0 right-0 z-50 flex justify-center px-3 pointer-events-none">
        <div className="w-full max-w-md space-y-2">
          <AnimatePresence>
            {items.map(t => (
              <motion.div key={t.id}
                initial={{ opacity: 0, y: -10, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.98 }}
                className={`rounded-2xl border border-border bg-card shadow-soft px-4 py-3 ${
                  t.kind==="error" ? "text-danger" : t.kind==="success" ? "text-accent" : "text-fg"
                }`}>
                <p className="text-sm font-medium">{t.title}</p>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </Ctx.Provider>
  );
}

export function useToast() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
