import type { FunnelStage } from "@/types/api";

export function RetrievalFunnel({ stages }: { stages: FunnelStage[] }) {
  const maxCount = Math.max(1, ...stages.map((stage) => stage.count));

  return (
    <div className="space-y-3">
      {stages.map((stage) => (
        <div key={stage.name} className="rounded-md border bg-background p-3">
          <div className="flex items-center justify-between gap-3 text-sm">
            <span className="font-medium">{stage.name}</span>
            <span className="text-muted-foreground">
              {stage.count} · {stage.latency_ms} ms
            </span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-sm bg-muted">
            <div
              className="h-full rounded-sm bg-primary"
              style={{ width: `${Math.max(6, (stage.count / maxCount) * 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
