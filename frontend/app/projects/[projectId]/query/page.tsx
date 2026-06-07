"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Brain, Network, Search, ShieldCheck, Sparkles } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { EmbeddingScatterPlot } from "@/components/retrieval/embedding-scatter-plot";
import { RetrievalFunnel } from "@/components/retrieval/retrieval-funnel";
import { SemanticGraph } from "@/components/retrieval/semantic-graph";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { QueryAnalyzeResponse, RetrievedChunk, WorkspaceRole } from "@/types/api";

const roles: WorkspaceRole[] = ["owner", "admin", "developer", "analyst", "viewer"];

export default function QueryAnalysisPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const [query, setQuery] = useState("Who is eligible for employee leave approval?");
  const [strategyId, setStrategyId] = useState("");
  const [role, setRole] = useState<WorkspaceRole>("viewer");
  const [topK, setTopK] = useState(5);
  const [error, setError] = useState<string | null>(null);

  const strategiesQuery = useQuery({
    queryKey: ["strategies", projectId],
    queryFn: () => api.strategies(projectId)
  });
  const strategies = strategiesQuery.data ?? [];
  const selectedStrategyId = strategyId || strategies[0]?.id || "";

  const analyzeMutation = useMutation({
    mutationFn: () => {
      if (!selectedStrategyId) {
        throw new Error("Create and index a strategy before running query analysis.");
      }
      return api.analyzeQuery(projectId, {
        query,
        strategy_id: selectedStrategyId,
        top_k: topK,
        dense_weight: 0.7,
        sparse_weight: 0.3,
        role_simulation: role,
        rerank: false
      });
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Query analysis failed"),
    onSuccess: () => setError(null)
  });

  const optimizeMutation = useMutation({
    mutationFn: () => api.optimizeQuery(projectId, query),
    onError: (err) => setError(err instanceof Error ? err.message : "Query optimization failed")
  });

  const result = analyzeMutation.data;
  const bestChunk = useMemo(() => result?.retrieved_chunks[0], [result]);
  const queryRunId = result?.query_run_id;
  const scatterQuery = useQuery({
    queryKey: ["query-run-scatter", queryRunId],
    queryFn: () => api.queryRunScatter(queryRunId ?? ""),
    enabled: Boolean(queryRunId)
  });
  const graphQuery = useQuery({
    queryKey: ["query-run-graph", queryRunId],
    queryFn: () => api.queryRunGraph(queryRunId ?? ""),
    enabled: Boolean(queryRunId)
  });
  const funnelQuery = useQuery({
    queryKey: ["query-run-funnel", queryRunId],
    queryFn: () => api.queryRunFunnel(queryRunId ?? ""),
    enabled: Boolean(queryRunId)
  });
  const funnelStages = funnelQuery.data?.stages ?? result?.funnel ?? [];

  return (
    <AppShell>
      <section className="space-y-5">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <Link
              className="mb-2 inline-flex items-center gap-2 text-sm text-muted-foreground"
              href={`/projects/${projectId}`}
            >
              <ArrowLeft className="h-4 w-4" />
              Project dashboard
            </Link>
            <h1 className="text-2xl font-semibold">Query Analysis</h1>
            <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
              Run RBAC-safe hybrid retrieval and inspect dense, sparse, fused, and latency signals.
            </p>
          </div>
          <Badge tone="info">Phase 5</Badge>
        </div>

        <div className="grid gap-5 xl:grid-cols-[0.75fr_1.25fr]">
          <Card>
            <CardHeader className="flex flex-row items-start justify-between">
              <CardTitle>Retrieval Controls</CardTitle>
              <Network className="h-5 w-5 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <form
                className="space-y-4"
                onSubmit={(event) => {
                  event.preventDefault();
                  analyzeMutation.mutate();
                }}
              >
                <label className="block text-sm">
                  <span className="font-medium">Query</span>
                  <textarea
                    className="mt-1 min-h-28 w-full rounded-md border bg-background p-3 outline-none focus:ring-2 focus:ring-primary"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                  />
                </label>
                <label className="block text-sm">
                  <span className="font-medium">Strategy</span>
                  <select
                    className="mt-1 h-10 w-full rounded-md border bg-background px-3 outline-none focus:ring-2 focus:ring-primary"
                    value={selectedStrategyId}
                    onChange={(event) => setStrategyId(event.target.value)}
                  >
                    {strategies.map((strategy) => (
                      <option key={strategy.id} value={strategy.id}>
                        {strategy.name}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="grid gap-3 md:grid-cols-2">
                  <label className="block text-sm">
                    <span className="font-medium">Role simulation</span>
                    <select
                      className="mt-1 h-10 w-full rounded-md border bg-background px-3 capitalize outline-none focus:ring-2 focus:ring-primary"
                      value={role}
                      onChange={(event) => setRole(event.target.value as WorkspaceRole)}
                    >
                      {roles.map((roleName) => (
                        <option key={roleName} value={roleName}>
                          {roleName}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="block text-sm">
                    <span className="font-medium">Top K</span>
                    <input
                      className="mt-1 h-10 w-full rounded-md border bg-background px-3 outline-none focus:ring-2 focus:ring-primary"
                      max={20}
                      min={1}
                      type="number"
                      value={topK}
                      onChange={(event) => setTopK(Number(event.target.value))}
                    />
                  </label>
                </div>
                {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
                <div className="flex flex-wrap gap-2">
                  <Button disabled={analyzeMutation.isPending} type="submit">
                    <Search className="h-4 w-4" />
                    {analyzeMutation.isPending ? "Analyzing" : "Run analysis"}
                  </Button>
                  <Button
                    disabled={optimizeMutation.isPending}
                    type="button"
                    variant="secondary"
                    onClick={() => optimizeMutation.mutate()}
                  >
                    <Sparkles className="h-4 w-4" />
                    Optimize query
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          <div className="space-y-5">
            <MetricsPanel result={result} />
            <Card>
              <CardHeader>
                <CardTitle>Retrieval Funnel</CardTitle>
              </CardHeader>
              <CardContent>
                {funnelStages.length ? (
                  <RetrievalFunnel stages={funnelStages} />
                ) : (
                  <Empty label="Run analysis to populate pipeline counts and latencies." />
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {optimizeMutation.data ? (
          <Card>
            <CardHeader className="flex flex-row items-start justify-between">
              <CardTitle>Optimized Query Variants</CardTitle>
              <Brain className="h-5 w-5 text-muted-foreground" />
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-2">
              {optimizeMutation.data.optimized_queries.map((item) => (
                <button
                  key={`${item.method}-${item.query}`}
                  className="rounded-md border bg-background p-3 text-left hover:border-primary"
                  type="button"
                  onClick={() => setQuery(item.query)}
                >
                  <div className="text-sm font-medium">{item.query}</div>
                  <div className="mt-1 text-xs text-muted-foreground">{item.reason}</div>
                </button>
              ))}
            </CardContent>
          </Card>
        ) : null}

        <div className="grid gap-5 xl:grid-cols-2">
          <Card>
            <CardHeader className="flex flex-row items-start justify-between">
              <CardTitle>Semantic Scatter</CardTitle>
              <Badge tone="neutral">
                {scatterQuery.isFetching ? "Refreshing" : scatterQuery.data?.projection_method ?? "2D projection"}
              </Badge>
            </CardHeader>
            <CardContent>
              <EmbeddingScatterPlot data={scatterQuery.data} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-start justify-between">
              <CardTitle>Query-to-Chunk Graph</CardTitle>
              <Badge tone="neutral">{graphQuery.isFetching ? "Refreshing" : "Relationship map"}</Badge>
            </CardHeader>
            <CardContent>
              <SemanticGraph data={graphQuery.data} />
            </CardContent>
          </Card>
        </div>

        <div>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Retrieved Chunks</h2>
            {bestChunk ? <Badge tone="success">Best score {formatPercent(bestChunk.scores.hybrid_score)}</Badge> : null}
          </div>
          {result ? <ChunkResults chunks={result.retrieved_chunks} /> : <Empty label="No query run yet." />}
        </div>
      </section>
    </AppShell>
  );
}

function MetricsPanel({ result }: { result?: QueryAnalyzeResponse }) {
  const metrics = result?.metrics;
  return (
    <div className="grid gap-3 md:grid-cols-4">
      <Metric label="Overall" value={metrics ? formatPercent(metrics.overall_score) : "-"} />
      <Metric label="Precision" value={metrics ? formatPercent(metrics.context_precision) : "-"} />
      <Metric label="Recall" value={metrics ? formatPercent(metrics.context_recall) : "-"} />
      <Metric label="RBAC leaks" value={metrics ? metrics.rbac_leakage_count.toString() : "-"} />
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-xs uppercase text-muted-foreground">{label}</div>
        <div className="mt-1 text-xl font-semibold">{value}</div>
      </CardContent>
    </Card>
  );
}

function ChunkResults({ chunks }: { chunks: RetrievedChunk[] }) {
  if (!chunks.length) {
    return <Empty label="No chunks matched the query and role simulation." />;
  }
  return (
    <div className="grid gap-4">
      {chunks.map((chunk) => (
        <Card key={chunk.id}>
          <CardHeader className="flex flex-row items-start justify-between gap-4">
            <div>
              <CardTitle>Chunk {chunk.chunk_index + 1}</CardTitle>
              <div className="mt-1 text-xs text-muted-foreground">
                {chunk.token_count} tokens - {chunk.section_heading ?? "No section heading"}
              </div>
            </div>
            <div className="flex flex-wrap justify-end gap-2">
              {chunk.allowed_roles.map((role) => (
                <Badge key={role} tone="info">
                  <ShieldCheck className="mr-1 h-3 w-3" />
                  {role}
                </Badge>
              ))}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="rounded-md border bg-background p-4 text-sm leading-6">{chunk.text}</p>
            <div className="grid gap-2 md:grid-cols-4">
              <Score label="Dense" value={chunk.scores.dense_score} />
              <Score label="Sparse" value={chunk.scores.sparse_score} />
              <Score label="Hybrid" value={chunk.scores.hybrid_score} />
              <Score label="Rerank" value={chunk.scores.rerank_score ?? 0} />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function Score({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border bg-background p-3">
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 font-semibold">{formatPercent(value)}</div>
    </div>
  );
}

function Empty({ label }: { label: string }) {
  return (
    <div className="flex min-h-36 items-center justify-center rounded-md border bg-background text-sm text-muted-foreground">
      {label}
    </div>
  );
}

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}
