"use client";

import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileSearch,
  FolderPlus,
  ShieldCheck
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

const recentExperiments = [
  ["Heading recursive vs semantic", "context precision", "0.82"],
  ["Employee role leakage simulation", "RBAC leakage", "0"],
  ["Hybrid alpha sweep", "latency p95", "186 ms"]
];

export default function DashboardPage() {
  const projectsQuery = useQuery({ queryKey: ["dashboard-projects"], queryFn: () => api.projects() });
  const projects = projectsQuery.data ?? [];
  const firstProject = projects[0];

  return (
    <AppShell>
      <section className="space-y-5">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal">Workspace Dashboard</h1>
            <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
              Visualize retrieval quality, chunk boundaries, semantic coverage, and RBAC safety across
              enterprise RAG projects.
            </p>
          </div>
          <Link
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            href="/projects/new"
          >
            <FolderPlus className="h-4 w-4" />
            New project
          </Link>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <MetricCard icon={CheckCircle2} label="Projects" value={projects.length.toString()} tone="success" />
          <MetricCard icon={FileSearch} label="Indexed chunks" value={firstProject ? "Ready" : "-"} tone="info" />
          <MetricCard icon={ShieldCheck} label="Leakage findings" value="0" tone="success" />
          <MetricCard icon={Clock} label="Avg retrieval" value="Live" tone="warning" />
        </div>

        <div className="grid gap-5 xl:grid-cols-[1.4fr_0.8fr]">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Projects</CardTitle>
              <Badge tone="neutral">Workspace scoped</Badge>
            </CardHeader>
            <CardContent>
              <div className="overflow-hidden rounded-md border">
                <table className="w-full text-left text-sm">
                  <thead className="bg-muted text-xs uppercase text-muted-foreground">
                    <tr>
                      <th className="px-4 py-3">Project</th>
                      <th className="px-4 py-3">Use case</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {projects.map((project) => (
                      <tr key={project.id} className="border-t">
                        <td className="px-4 py-3 font-medium">
                          <Link className="hover:text-primary" href={`/projects/${project.id}`}>
                            {project.name}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">{project.use_case}</td>
                        <td className="px-4 py-3">
                          <Badge tone="success">Active</Badge>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-2">
                            <ActionLink href={`/projects/${project.id}/query`} label="Query" />
                            <ActionLink href={`/projects/${project.id}/compare`} label="Compare" />
                            <ActionLink href={`/projects/${project.id}/rbac`} label="RBAC" />
                          </div>
                        </td>
                      </tr>
                    ))}
                    {!projects.length ? (
                      <tr>
                        <td className="px-4 py-8 text-sm text-muted-foreground" colSpan={4}>
                          {projectsQuery.isLoading
                            ? "Loading projects..."
                            : projectsQuery.isError
                              ? "Unable to load projects. Sign in again or check that the API is reachable."
                              : "No projects yet. Create a project to unlock document, strategy, query, and report views."}
                        </td>
                      </tr>
                    ) : null}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Experiments</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {recentExperiments.map(([name, metric, value]) => (
                <div key={name} className="rounded-md border p-3">
                  <div className="text-sm font-medium">{name}</div>
                  <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                    <span>{metric}</span>
                    <span className="font-semibold text-foreground">{value}</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <ReadinessCard title="Backend RBAC" status="Enforced for workspace/project/retrieval APIs" />
          <ReadinessCard title="Retrieval safety" status="Unauthorized chunks are filtered before scoring" />
          <ReadinessCard title="Exports" status="Reports and integration snippets available" />
        </div>
      </section>
    </AppShell>
  );
}

function ActionLink({ href, label }: { href: string; label: string }) {
  return (
    <Link className="rounded-sm border px-2 py-1 text-xs font-medium hover:bg-muted" href={href}>
      {label}
    </Link>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  tone
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  tone: "success" | "info" | "warning";
}) {
  const toneClass = {
    success: "text-emerald-700",
    info: "text-cyan-700",
    warning: "text-amber-700"
  }[tone];
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-5">
        <div>
          <div className="text-sm text-muted-foreground">{label}</div>
          <div className="mt-1 text-2xl font-semibold">{value}</div>
        </div>
        <div className="rounded-md bg-muted p-2">
          <Icon className={`h-5 w-5 ${toneClass}`} />
        </div>
      </CardContent>
    </Card>
  );
}

function ReadinessCard({ title, status }: { title: string; status: string }) {
  return (
    <Card>
      <CardContent className="flex items-start gap-3 p-4">
        <AlertTriangle className="mt-0.5 h-4 w-4 text-amber-600" />
        <div>
          <div className="text-sm font-medium">{title}</div>
          <div className="mt-1 text-xs text-muted-foreground">{status}</div>
        </div>
      </CardContent>
    </Card>
  );
}
