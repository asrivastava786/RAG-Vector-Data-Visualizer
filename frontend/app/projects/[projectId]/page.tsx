"use client";

import {
  BarChart3,
  BrainCircuit,
  FileJson,
  FileText,
  GitBranch,
  Layers,
  Network,
  ShieldCheck,
  SlidersHorizontal,
  Upload,
  type LucideIcon
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const surfaces: Array<[string, string, LucideIcon]> = [
  ["Documents", "Upload, parse, classify, and preview source material.", FileText],
  ["Chunk Inspector", "Inspect boundaries, overlaps, access tags, and split warnings.", GitBranch],
  ["Query Analysis", "Trace dense, sparse, hybrid, rerank, and funnel stages.", Network],
  ["Strategy Comparison", "Compare precision, recall, citation quality, latency, and cost.", BarChart3],
  ["Data Layer", "Route facts, embeddings, relationships, policies, and files across polyglot stores.", Layers],
  ["RBAC Safety", "Simulate roles and hard-fail unauthorized chunk exposure.", ShieldCheck],
  ["Reports", "Export JSON, YAML, pseudocode, and FastAPI integration snippets.", FileJson],
  ["Optimization", "Tune chunking, query expansion, retrieval weights, and reranking.", SlidersHorizontal]
];

export default function ProjectDashboardPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  return (
    <AppShell>
      <section className="space-y-5">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <div className="mb-2 flex items-center gap-2">
              <Badge tone="info">Project</Badge>
              <span className="text-xs text-muted-foreground">{projectId}</span>
            </div>
            <h1 className="text-2xl font-semibold">RAG Optimization Project</h1>
            <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
              Project command center for documents, strategies, experiments, query analysis,
              visualizations, safety reports, and exportable production retrieval configs.
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary">Export config</Button>
            <Link
              className={cn(
                "inline-flex h-10 items-center justify-center gap-2 rounded-md bg-muted px-4 text-sm font-medium text-foreground hover:bg-muted/80"
              )}
              href={`/projects/${projectId}/strategies/new`}
            >
              <BrainCircuit className="h-4 w-4" />
              New strategy
            </Link>
            <Link
              className={cn(
                "inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              )}
              href={`/projects/${projectId}/documents/upload`}
            >
              <Upload className="h-4 w-4" />
              Upload document
            </Link>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          {surfaces.map(([title, description, Icon]) => (
            <Card key={title}>
              <CardHeader className="flex flex-row items-start justify-between space-y-0">
                <CardTitle>{title}</CardTitle>
                <Icon className="h-5 w-5 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{description}</p>
                <div className="mt-4">
                  {title === "Query Analysis" ? (
                    <Link
                      className="text-sm font-medium text-primary hover:underline"
                      href={`/projects/${projectId}/query`}
                    >
                      Open query analysis
                    </Link>
                  ) : title === "Strategy Comparison" ? (
                    <Link
                      className="text-sm font-medium text-primary hover:underline"
                      href={`/projects/${projectId}/compare`}
                    >
                      Compare strategies
                    </Link>
                  ) : title === "Data Layer" ? (
                    <Link
                      className="text-sm font-medium text-primary hover:underline"
                      href={`/projects/${projectId}/data-layer`}
                    >
                      Open data strategy
                    </Link>
                  ) : title === "Chunk Inspector" ? (
                    <Link
                      className="text-sm font-medium text-primary hover:underline"
                      href={`/projects/${projectId}/strategies/new`}
                    >
                      Create strategy
                    </Link>
                  ) : title === "RBAC Safety" ? (
                    <Link
                      className="text-sm font-medium text-primary hover:underline"
                      href={`/projects/${projectId}/rbac`}
                    >
                      Simulate access
                    </Link>
                  ) : title === "Documents" ? (
                    <Link
                      className="text-sm font-medium text-primary hover:underline"
                      href={`/projects/${projectId}/documents/upload`}
                    >
                      Upload document
                    </Link>
                  ) : title === "Reports" ? (
                    <Link
                      className="text-sm font-medium text-primary hover:underline"
                      href={`/projects/${projectId}/reports`}
                    >
                      Open reports
                    </Link>
                  ) : (
                    <Badge tone="warning">Phase roadmap</Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Current Retrieval Governance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-4">
              {["workspace_id", "project_id", "allowed_roles", "allowed_users"].map((field) => (
                <div key={field} className="rounded-md border bg-background p-3 text-sm">
                  <div className="font-medium">{field}</div>
                  <div className="mt-1 text-xs text-muted-foreground">Required retrieval filter</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>
    </AppShell>
  );
}
