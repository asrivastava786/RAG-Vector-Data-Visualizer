"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, FlaskConical, Play, Settings2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { StrategyLeaderboard } from "@/components/experiments/strategy-leaderboard";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { ExperimentRunResponse } from "@/types/api";

const defaultQueries = [
  "Who is eligible for employee leave approval?",
  "Where can employees request paid leave?",
  "What role approves leave requests?"
].join("\n");

export default function StrategyComparisonPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const queryClient = useQueryClient();
  const [name, setName] = useState("HR retrieval baseline comparison");
  const [description, setDescription] = useState("Compare indexed chunking strategies with RBAC-safe retrieval.");
  const [queryText, setQueryText] = useState(defaultQueries);
  const [selectedStrategyIds, setSelectedStrategyIds] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [runResult, setRunResult] = useState<ExperimentRunResponse | null>(null);

  const strategiesQuery = useQuery({
    queryKey: ["strategies", projectId],
    queryFn: () => api.strategies(projectId)
  });
  const experimentsQuery = useQuery({
    queryKey: ["experiments", projectId],
    queryFn: () => api.experiments(projectId)
  });
  const recommendationQuery = useQuery({
    queryKey: ["project-recommendation", projectId],
    queryFn: () => api.projectRecommendation(projectId)
  });
  const strategies = strategiesQuery.data ?? [];
  const effectiveStrategyIds = selectedStrategyIds.length
    ? selectedStrategyIds
    : strategies.slice(0, 3).map((strategy) => strategy.id);
  const leaderboard = runResult?.leaderboard ?? recommendationQuery.data?.leaderboard ?? [];
  const querySet = useMemo(
    () =>
      queryText
        .split("\n")
        .map((query) => query.trim())
        .filter(Boolean),
    [queryText]
  );

  const createAndRunMutation = useMutation({
    mutationFn: async () => {
      if (!effectiveStrategyIds.length) {
        throw new Error("Select at least one strategy.");
      }
      if (!querySet.length) {
        throw new Error("Add at least one evaluation query.");
      }
      const experiment = await api.createExperiment(projectId, {
        name,
        description,
        strategy_ids: effectiveStrategyIds,
        query_set: querySet.map((query) => ({ query, expected_chunk_ids: [] })),
        role_simulation: null
      });
      return api.runExperiment(experiment.id);
    },
    onSuccess: (result) => {
      setRunResult(result);
      setError(null);
      void queryClient.invalidateQueries({ queryKey: ["experiments", projectId] });
      void queryClient.invalidateQueries({ queryKey: ["project-recommendation", projectId] });
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Experiment run failed")
  });

  function toggleStrategy(strategyId: string) {
    setSelectedStrategyIds((current) =>
      current.includes(strategyId)
        ? current.filter((id) => id !== strategyId)
        : [...current, strategyId]
    );
  }

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
            <h1 className="text-2xl font-semibold">Strategy Comparison</h1>
            <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
              Run the same evaluation query set across indexed strategies and promote the safest configuration.
            </p>
          </div>
          <Badge tone="info">Phase 6</Badge>
        </div>

        <div className="grid gap-5 xl:grid-cols-[0.72fr_1.28fr]">
          <Card>
            <CardHeader className="flex flex-row items-start justify-between">
              <CardTitle>Experiment Setup</CardTitle>
              <FlaskConical className="h-5 w-5 text-muted-foreground" />
            </CardHeader>
            <CardContent className="space-y-4">
              <Field label="Experiment name" value={name} onChange={(event) => setName(event.target.value)} />
              <Field
                label="Description"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
              />
              <label className="block text-sm">
                <span className="font-medium">Evaluation queries</span>
                <textarea
                  className="mt-1 min-h-32 w-full rounded-md border bg-background p-3 outline-none focus:ring-2 focus:ring-primary"
                  value={queryText}
                  onChange={(event) => setQueryText(event.target.value)}
                />
              </label>
              <div>
                <div className="text-sm font-medium">Strategies</div>
                <div className="mt-2 space-y-2">
                  {strategies.map((strategy) => {
                    const selected = effectiveStrategyIds.includes(strategy.id);
                    return (
                      <button
                        key={strategy.id}
                        className={`w-full rounded-md border p-3 text-left text-sm ${
                          selected ? "border-primary bg-primary/5" : "bg-background"
                        }`}
                        type="button"
                        onClick={() => toggleStrategy(strategy.id)}
                      >
                        <div className="font-medium">{strategy.name}</div>
                        <div className="mt-1 text-xs text-muted-foreground">
                          {strategy.splitter_type} - {strategy.chunk_size}/{strategy.overlap}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
              {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
              <Button disabled={createAndRunMutation.isPending} onClick={() => createAndRunMutation.mutate()}>
                <Play className="h-4 w-4" />
                {createAndRunMutation.isPending ? "Running" : "Run comparison"}
              </Button>
            </CardContent>
          </Card>

          <div className="space-y-5">
            <div className="grid gap-3 md:grid-cols-3">
              <Metric label="Experiments" value={(experimentsQuery.data?.length ?? 0).toString()} />
              <Metric label="Strategies" value={strategies.length.toString()} />
              <Metric label="Queries" value={querySet.length.toString()} />
            </div>
            <Card>
              <CardHeader className="flex flex-row items-start justify-between">
                <CardTitle>Leaderboard</CardTitle>
                <Badge tone="neutral">
                  {runResult ? "Latest run" : recommendationQuery.data ? "Recommendation" : "Waiting"}
                </Badge>
              </CardHeader>
              <CardContent>
                <StrategyLeaderboard rows={leaderboard} />
              </CardContent>
            </Card>
          </div>
        </div>

        <Card>
          <CardHeader className="flex flex-row items-start justify-between">
            <CardTitle>Recommended Config</CardTitle>
            <Settings2 className="h-5 w-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {recommendationQuery.data?.recommended_config ? (
              <pre className="max-h-96 overflow-auto rounded-md border bg-background p-4 text-sm">
                {JSON.stringify(recommendationQuery.data.recommended_config, null, 2)}
              </pre>
            ) : (
              <div className="flex min-h-32 items-center justify-center rounded-md border bg-background text-sm text-muted-foreground">
                Run a comparison to generate a production retrieval config.
              </div>
            )}
          </CardContent>
        </Card>
      </section>
    </AppShell>
  );
}

function Field(props: React.InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  const { label, ...inputProps } = props;
  return (
    <label className="block text-sm">
      <span className="font-medium">{label}</span>
      <input
        className="mt-1 h-10 w-full rounded-md border bg-background px-3 outline-none focus:ring-2 focus:ring-primary"
        {...inputProps}
      />
    </label>
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
