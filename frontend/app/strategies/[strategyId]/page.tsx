"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, DatabaseZap, GitBranch, RefreshCw } from "lucide-react";
import Link from "next/link";
import { ChunkBoundaryViewer } from "@/components/chunks/chunk-boundary-viewer";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export default function StrategyDetailPage({ params }: { params: { strategyId: string } }) {
  const queryClient = useQueryClient();
  const strategyQuery = useQuery({
    queryKey: ["strategy", params.strategyId],
    queryFn: () => api.strategy(params.strategyId)
  });
  const chunksQuery = useQuery({
    queryKey: ["strategy-chunks", params.strategyId],
    queryFn: () => api.strategyChunks(params.strategyId, 100)
  });
  const indexMutation = useMutation({
    mutationFn: () => api.indexStrategy(params.strategyId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["strategy-chunks", params.strategyId] });
    }
  });

  const strategy = strategyQuery.data;
  const chunks = chunksQuery.data ?? [];
  const warningCount = chunks.reduce(
    (total, chunk) => total + (chunk.metadata_json.warnings?.length ?? 0),
    0
  );

  return (
    <AppShell>
      <section className="space-y-5">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <Link
              className="mb-2 inline-flex items-center gap-2 text-sm text-muted-foreground"
              href={strategy ? `/projects/${strategy.project_id}` : "/dashboard"}
            >
              <ArrowLeft className="h-4 w-4" />
              {strategy ? "Project dashboard" : "Dashboard"}
            </Link>
            <h1 className="text-2xl font-semibold">{strategy?.name ?? "Chunking Strategy"}</h1>
            <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
              Index processed documents, inspect generated chunk boundaries, and confirm access metadata.
            </p>
          </div>
          <Button disabled={indexMutation.isPending} onClick={() => indexMutation.mutate()}>
            <DatabaseZap className="h-4 w-4" />
            {indexMutation.isPending ? "Indexing" : "Run indexing"}
          </Button>
        </div>

        {strategyQuery.error ? (
          <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {strategyQuery.error instanceof Error ? strategyQuery.error.message : "Unable to load strategy"}
          </div>
        ) : null}
        {indexMutation.error ? (
          <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {indexMutation.error instanceof Error ? indexMutation.error.message : "Indexing failed"}
          </div>
        ) : null}
        {indexMutation.data ? (
          <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
            Indexed {indexMutation.data.documents_indexed} documents into {indexMutation.data.chunks_created} chunks.
          </div>
        ) : null}

        <div className="grid gap-4 md:grid-cols-4">
          <MetricCard icon={GitBranch} label="Chunks visible" value={chunks.length.toString()} />
          <MetricCard icon={RefreshCw} label="Splitter" value={strategy?.splitter_type ?? "-"} />
          <MetricCard label="Chunk size" value={strategy?.chunk_size.toString() ?? "-"} />
          <MetricCard label="Warnings" value={warningCount.toString()} tone={warningCount ? "warning" : "neutral"} />
        </div>

        <Card>
          <CardHeader className="flex flex-row items-start justify-between">
            <CardTitle>Strategy Configuration</CardTitle>
            <Badge tone="info">RBAC indexed</Badge>
          </CardHeader>
          <CardContent>
            {strategy ? (
              <div className="grid gap-3 md:grid-cols-5">
                <ConfigPill label="Splitter" value={strategy.splitter_type} />
                <ConfigPill label="Chunk size" value={strategy.chunk_size.toString()} />
                <ConfigPill label="Overlap" value={strategy.overlap.toString()} />
                <ConfigPill label="Headings" value={strategy.preserve_headings ? "Preserved" : "Off"} />
                <ConfigPill label="Tables" value={strategy.preserve_tables ? "Preserved" : "Off"} />
              </div>
            ) : (
              <div className="h-20 animate-pulse rounded-md bg-muted" />
            )}
          </CardContent>
        </Card>

        <div>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Chunk Boundary Inspector</h2>
            <Badge tone="neutral">{chunksQuery.isFetching ? "Refreshing" : "Live API"}</Badge>
          </div>
          <ChunkBoundaryViewer chunks={chunks} />
        </div>
      </section>
    </AppShell>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  tone = "neutral"
}: {
  icon?: React.ElementType;
  label: string;
  value: string;
  tone?: "neutral" | "warning";
}) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-4">
        <div>
          <div className="text-xs uppercase text-muted-foreground">{label}</div>
          <div className="mt-1 text-xl font-semibold">{value}</div>
        </div>
        {Icon ? <Icon className="h-5 w-5 text-muted-foreground" /> : <Badge tone={tone}>{tone}</Badge>}
      </CardContent>
    </Card>
  );
}

function ConfigPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-background p-3">
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 truncate text-sm font-medium">{value}</div>
    </div>
  );
}
