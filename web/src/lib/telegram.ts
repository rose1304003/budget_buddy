export function tg() { return (window as any).Telegram?.WebApp ?? null; }
export function initTelegram() {
  const w = tg();
  if (!w) return;
  w.ready?.();
  w.expand?.();
  w.setHeaderColor?.("#0B1220");
  w.setBackgroundColor?.("#0B1220");
}
export function getInitData(): string { return tg()?.initData ?? ""; }
export function haptic(type: "light" | "medium" | "heavy" = "light") {
  tg()?.HapticFeedback?.impactOccurred?.(type);
}
