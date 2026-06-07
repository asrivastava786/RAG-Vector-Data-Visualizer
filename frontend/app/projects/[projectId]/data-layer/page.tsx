"use client";

import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Database,
  GitBranch,
  Layers,
  Network,
  ShieldCheck
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { DataLayerRecommendationResponse, DataLayerStoreRecommendation } from "@/types/api";

export default function DataLayerStrategyPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const recommendationQuery = useQuery({
    queryKey: ["data-layer-recommendation", projectId],
    queryFn: () => api.dataLayerRecommendation(projectId)
  });
  const recommendation = recommendationQuery.data;

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
            <h1 className="text-2xl font-semibold">Polyglot Data Layer Strategy</h1>
            <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
              Decide what should live in relational, vector, graph, cache, and object storage using
              project-scoped RAG signals.
            </p>
          </div>
          <Badge tone="info">Architecture recommendation</Badge>
        </div>

        {recommendationQuery.isError ? (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="flex items-center gap-3 p-4 text-sm text-red-800">
              <AlertTriangle className="h-4 w-4" />
              {recommendationQuery.error instanceof Error
                ? recommendationQuery.error.message
                : "Unable to load data-layer recommendation."}
            </CardContent>
          </Card>
        ) : null}

        {recommendation ? <RecommendationView recommendation={recommendation} /> : <LoadingState />}
      </section>
    </AppShell>
  );
}

function RecommendationView({ recommendation }: { recommendation: DataLayerRecommendationResponse }) {
  const facts = recommendation.facts;
  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-start justify-between">
          <div>
            <CardTitle>Recommended Architecture</CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">{recommendation.recommended_architecture}</p>
          </div>
          <Layers className="h-5 w-5 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-4">
            <Fact label="Documents" value={`${facts.processed_document_count}/${facts.document_count}`} />
            <Fact label="Chunks" value={facts.chunk_count.toString()} />
            <Fact label="Embeddings" value={`${facts.chunks_with_embeddings}/${facts.chunk_count}`} />
            <Fact label="Access profiles" value={facts.distinct_access_profiles.toString()} />
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-5 xl:grid-cols-3">
        {recommendation.stores.map((store) => (
          <StoreCard key={store.store} store={store} />
        ))}
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
        <Card>
          <CardHeader>
            <CardTitle>Data Routing Rules</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-hidden rounded-md border">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="px-4 py-3">Domain</th>
                    <th className="px-4 py-3">Primary</th>
                    <th className="px-4 py-3">Projection</th>
                    <th className="px-4 py-3">Sync</th>
                  </tr>
                </thead>
                <tbody>
                  {recommendation.routing_rules.map((rule) => (
                    <tr key={`${rule.data_domain}-${rule.primary_store}`} className="border-t align-top">
                      <td className="px-4 py-3">
                        <div className="font-medium">{rule.data_domain}</div>
                        <div className="mt-1 text-xs text-muted-foreground">{rule.reason}</div>
                      </td>
                      <td className="px-4 py-3">
                        <StoreBadge store={rule.primary_store} />
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {rule.secondary_stores.length ? (
                            rule.secondary_stores.map((store) => <StoreBadge key={store} store={store} />)
                          ) : (
                            <Badge tone="neutral">none</Badge>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{rule.sync_pattern}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-5">
          <SignalCard title="Efficiency Moves" items={recommendation.efficiency_recommendations} icon="check" />
          <SignalCard title="Governance Rules" items={recommendation.governance_rules} icon="shield" />
          {recommendation.warnings.length ? (
            <SignalCard title="Warnings" items={recommendation.warnings} icon="warn" />
          ) : null}
        </div>
      </div>
    </>
  );
}

function StoreCard({ store }: { store: DataLayerStoreRecommendation }) {
  const Icon = store.store === "relational" ? Database : store.store === "graph" ? GitBranch : Network;
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle className="capitalize">{store.store}</CardTitle>
          <p className="mt-1 text-sm text-muted-foreground">{store.role}</p>
        </div>
        <Icon className="h-5 w-5 text-muted-foreground" />
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
            <span>Fit score</span>
            <span>{Math.round(store.fit_score * 100)}%</span>
          </div>
          <div className="h-2 rounded-sm bg-muted">
            <div className="h-2 rounded-sm bg-primary" style={{ width: `${store.fit_score * 100}%` }} />
          </div>
        </div>
        <TagList label="Entities" items={store.primary_entities} />
        <BulletList label="Indexing strategy" items={store.indexing_strategy} />
        <BulletList label="Rationale" items={store.rationale} />
        {store.risks.length ? <BulletList label="Risks" items={store.risks} tone="warning" /> : null}
      </CardContent>
    </Card>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-background p-3">
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 text-xl font-semibold">{value}</div>
    </div>
  );
}

function SignalCard({ title, items, icon }: { title: string; items: string[]; icon: "check" | "shield" | "warn" }) {
  const Icon = icon === "shield" ? ShieldCheck : icon === "warn" ? AlertTriangle : CheckCircle2;
  const tone = icon === "warn" ? "warning" : "success";
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <CardTitle>{title}</CardTitle>
        <Badge tone={tone}>{items.length}</Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.map((item) => (
          <div key={item} className="flex gap-3 text-sm">
            <Icon className="mt-0.5 h-4 w-4 text-muted-foreground" />
            <span>{item}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function TagList({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <div className="mb-2 text-xs uppercase text-muted-foreground">{label}</div>
      <div className="flex flex-wrap gap-1">
        {items.map((item) => (
          <Badge key={item} tone="neutral">
            {item}
          </Badge>
        ))}
      </div>
    </div>
  );
}

function BulletList({ label, items, tone = "neutral" }: { label: string; items: string[]; tone?: "neutral" | "warning" }) {
  return (
    <div>
      <div className="mb-2 text-xs uppercase text-muted-foreground">{label}</div>
      <div className="space-y-2">
        {items.map((item) => (
          <div key={item} className="rounded-md border bg-background p-2 text-xs text-muted-foreground">
            {tone === "warning" ? <span className="font-medium text-amber-700">Risk: </span> : null}
            {item}
          </div>
        ))}
      </div>
    </div>
  );
}

function StoreBadge({ store }: { store: string }) {
  const tone = store === "vector" ? "info" : store === "graph" ? "warning" : store === "relational" ? "success" : "neutral";
  return (
    <Badge tone={tone}>
      <span className="capitalize">{store}</span>
    </Badge>
  );
}

function LoadingState() {
  return (
    <div className="grid gap-5 xl:grid-cols-3">
      {["Relational", "Vector", "Graph"].map((label) => (
        <Card key={label}>
          <CardHeader>
            <CardTitle>{label}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-28 rounded-md bg-muted" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
