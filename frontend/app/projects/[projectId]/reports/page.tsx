"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Download, FileJson } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

const formats = ["json", "yaml", "langchain", "llamaindex", "fastapi"];

export default function ReportsPage({ params }: { params: { projectId: string } }) {
  const [format, setFormat] = useState("json");
  const recommendationQuery = useQuery({
    queryKey: ["project-recommendation", params.projectId],
    queryFn: () => api.projectRecommendation(params.projectId)
  });
  const exportMutation = useMutation({
    mutationFn: () => api.exportConfig(params.projectId, format)
  });

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
            <h1 className="text-2xl font-semibold">Reports</h1>
            <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
              Review recommended retrieval settings and generate deployable integration snippets.
            </p>
          </div>
          <Badge tone="info">Phase 7</Badge>
        </div>

        <div className="grid gap-5 xl:grid-cols-[0.7fr_1.3fr]">
          <Card>
            <CardHeader className="flex flex-row items-start justify-between">
              <CardTitle>Export Config</CardTitle>
              <FileJson className="h-5 w-5 text-muted-foreground" />
            </CardHeader>
            <CardContent className="space-y-4">
              <label className="block text-sm">
                <span className="font-medium">Format</span>
                <select
                  className="mt-1 h-10 w-full rounded-md border bg-background px-3 outline-none focus:ring-2 focus:ring-primary"
                  value={format}
                  onChange={(event) => setFormat(event.target.value)}
                >
                  {formats.map((item) => (
                    <option key={item} value={item}>{item}</option>
                  ))}
                </select>
              </label>
              <Button disabled={exportMutation.isPending} onClick={() => exportMutation.mutate()}>
                <Download className="h-4 w-4" />
                {exportMutation.isPending ? "Generating" : "Generate export"}
              </Button>
              <div className="rounded-md border bg-background p-3 text-sm">
                <div className="font-medium">Recommended strategy</div>
                <div className="mt-1 text-muted-foreground">
                  {recommendationQuery.data?.recommended_strategy_name ?? "Run a comparison first"}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Export Output</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="min-h-80 overflow-auto rounded-md border bg-background p-4 text-sm">
                {exportMutation.data?.content ??
                  JSON.stringify(recommendationQuery.data?.recommended_config ?? {}, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </div>
      </section>
    </AppShell>
  );
}
