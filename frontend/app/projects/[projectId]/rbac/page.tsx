"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, ShieldAlert, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { RBACSimulationResponse, WorkspaceRole } from "@/types/api";

const roles: WorkspaceRole[] = ["owner", "admin", "developer", "analyst", "viewer"];

export default function RBACSafetyPage({ params }: { params: { projectId: string } }) {
  const [query, setQuery] = useState("Who is eligible for employee leave approval?");
  const [role, setRole] = useState<WorkspaceRole>("viewer");
  const [strategyId, setStrategyId] = useState("");
  const [error, setError] = useState<string | null>(null);

  const strategiesQuery = useQuery({
    queryKey: ["strategies", params.projectId],
    queryFn: () => api.strategies(params.projectId)
  });
  const matrixQuery = useQuery({
    queryKey: ["rbac-matrix", params.projectId],
    queryFn: () => api.rbacMatrix(params.projectId)
  });
  const strategies = strategiesQuery.data ?? [];
  const selectedStrategyId = strategyId || strategies[0]?.id || "";

  const simulationMutation = useMutation({
    mutationFn: () => {
      if (!selectedStrategyId) {
        throw new Error("Index a strategy before simulating RBAC retrieval.");
      }
      return api.simulateRbac(params.projectId, {
        strategy_id: selectedStrategyId,
        query,
        role_simulation: role,
        top_k: 5
      });
    },
    onError: (err) => setError(err instanceof Error ? err.message : "RBAC simulation failed"),
    onSuccess: () => setError(null)
  });
  const result = simulationMutation.data;

  return (
    <AppShell>
      <section className="space-y-5">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <Link
              className="mb-2 inline-flex items-center gap-2 text-sm text-muted-foreground"
              href={`/projects/${params.projectId}`}
            >
              <ArrowLeft className="h-4 w-4" />
              Project dashboard
            </Link>
            <h1 className="text-2xl font-semibold">RBAC Safety</h1>
            <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
              Simulate role-scoped retrieval and verify blocked chunks never enter returned context.
            </p>
          </div>
          <Badge tone="info">Phase 7</Badge>
        </div>

        <div className="grid gap-5 xl:grid-cols-[0.7fr_1.3fr]">
          <Card>
            <CardHeader className="flex flex-row items-start justify-between">
              <CardTitle>Role Simulator</CardTitle>
              <ShieldCheck className="h-5 w-5 text-muted-foreground" />
            </CardHeader>
            <CardContent className="space-y-4">
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
              <label className="block text-sm">
                <span className="font-medium">Simulated role</span>
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
              {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
              <Button disabled={simulationMutation.isPending} onClick={() => simulationMutation.mutate()}>
                <ShieldAlert className="h-4 w-4" />
                {simulationMutation.isPending ? "Simulating" : "Run simulation"}
              </Button>
            </CardContent>
          </Card>

          <SafetySummary result={result} />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Access Matrix</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-hidden rounded-md border">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2">Document</th>
                    {roles.map((roleName) => (
                      <th key={roleName} className="px-3 py-2 capitalize">{roleName}</th>
                    ))}
                    <th className="px-3 py-2">Warnings</th>
                  </tr>
                </thead>
                <tbody>
                  {(matrixQuery.data?.rows ?? []).map((row) => (
                    <tr key={row.entity_id} className="border-t bg-background">
                      <td className="px-3 py-3 font-medium">{row.label}</td>
                      {roles.map((roleName) => (
                        <td key={roleName} className="px-3 py-3">
                          <Badge tone={row.role_access[roleName] ? "success" : "neutral"}>
                            {row.role_access[roleName] ? "allowed" : "blocked"}
                          </Badge>
                        </td>
                      ))}
                      <td className="px-3 py-3">{row.warnings.join(", ") || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </section>
    </AppShell>
  );
}

function SafetySummary({ result }: { result?: RBACSimulationResponse }) {
  if (!result) {
    return (
      <Card>
        <CardContent className="flex min-h-64 items-center justify-center p-5 text-sm text-muted-foreground">
          Run a simulation to inspect allowed, blocked, and returned chunks.
        </CardContent>
      </Card>
    );
  }
  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Metric label="Allowed chunks" value={result.allowed_chunks.length.toString()} />
      <Metric label="Blocked chunks" value={result.blocked_chunks.length.toString()} />
      <Metric label="Leakage count" value={result.leakage_count.toString()} danger={result.leakage_count > 0} />
      <Card className="md:col-span-3">
        <CardHeader>
          <CardTitle>Blocked Chunk List</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {result.blocked_chunks.length ? (
            result.blocked_chunks.map((chunk) => (
              <div key={chunk.chunk_id} className="rounded-md border bg-background p-3 text-sm">
                <div className="font-medium">Chunk {chunk.chunk_index + 1}</div>
                <div className="mt-1 text-xs text-muted-foreground">
                  Roles: {chunk.allowed_roles.join(", ")} - {chunk.token_count} tokens
                </div>
              </div>
            ))
          ) : (
            <div className="text-sm text-muted-foreground">No blocked chunks for this simulation.</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Metric({ label, value, danger = false }: { label: string; value: string; danger?: boolean }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-xs uppercase text-muted-foreground">{label}</div>
        <div className={`mt-1 text-xl font-semibold ${danger ? "text-red-700" : ""}`}>{value}</div>
      </CardContent>
    </Card>
  );
}
