import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import { Card } from "../ui/Card";
import { Chip } from "../ui/Chip";

export default function SettingsPage() {
  const meQ = useQuery({ queryKey: ["me"], queryFn: api.me });
  const me = meQ.data;

  return (
    <div className="space-y-4">
      <header>
        <p className="text-muted text-sm">Settings</p>
        <h1 className="text-2xl font-semibold tracking-tight">Account & app</h1>
      </header>

      <Card className="p-4 space-y-2">
        <p className="text-sm font-medium">Telegram profile</p>
        <p className="text-sm text-muted">Name: {me ? `${me.first_name} ${me.last_name}`.trim() : "—"}</p>
        <p className="text-sm text-muted">Username: {me?.username ? `@${me.username}` : "—"}</p>
        <div className="flex flex-wrap gap-2 pt-2">
          <Chip tone="accent">Secure initData auth</Chip>
          <Chip>Palette A</Chip>
        </div>
      </Card>

      <Card className="p-4 space-y-2">
        <p className="text-sm font-medium">Next upgrades</p>
        <p className="text-sm text-muted">Voice-to-transaction bot, limits, exporting, and multilingual UI are easy next steps.</p>
      </Card>
    </div>
  );
}
