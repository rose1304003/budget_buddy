import { useEffect } from "react";
import { Routes, Route, Navigate, useLocation, Link } from "react-router-dom";
import { Home, Wallet, Tags, BarChart3, Settings } from "lucide-react";
import { initTelegram } from "./lib/telegram";
import { ToastProvider } from "./ui/Toast";
import HomePage from "./pages/HomePage";
import TransactionsPage from "./pages/TransactionsPage";
import CategoriesPage from "./pages/CategoriesPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import SettingsPage from "./pages/SettingsPage";
import { cn } from "./ui/cn";

export default function App() {
  useEffect(() => { initTelegram(); }, []);
  return (
    <ToastProvider>
      <div className="min-h-screen bg-bg text-fg">
        <div className="mx-auto max-w-md px-4 pb-24 pt-4">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/transactions" element={<TransactionsPage />} />
            <Route path="/categories" element={<CategoriesPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
        <BottomNav />
      </div>
    </ToastProvider>
  );
}

function BottomNav() {
  const { pathname } = useLocation();
  const items = [
    { to: "/", label: "Home", icon: Home },
    { to: "/transactions", label: "Wallet", icon: Wallet },
    { to: "/categories", label: "Tags", icon: Tags },
    { to: "/analytics", label: "Analytics", icon: BarChart3 },
    { to: "/settings", label: "Settings", icon: Settings },
  ];
  return (
    <div className="fixed bottom-0 left-0 right-0 z-40">
      <div className="mx-auto max-w-md px-4 pb-4">
        <div className="rounded-2xl border border-border bg-card/90 backdrop-blur shadow-soft px-2 py-2">
          <div className="grid grid-cols-5">
            {items.map((it) => {
              const active = pathname === it.to;
              const Icon = it.icon;
              return (
                <Link key={it.to} to={it.to}
                  className={cn("tap flex flex-col items-center justify-center gap-1 rounded-2xl py-2 text-xs",
                    active ? "text-accent" : "text-muted hover:text-fg")}>
                  <Icon size={18} />
                  {it.label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
