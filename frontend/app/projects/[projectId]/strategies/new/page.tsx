"use client";

import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, BrainCircuit, Play } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { SplitterType } from "@/types/api";

const splitterOptions: Array<{ value: SplitterType; label: string; detail: string }> = [
  { value: "recursive", label: "Recursive", detail: "Headings, paragraphs, sentences, words" },
  { value: "heading", label: "Heading", detail: "Preserve section boundaries first" },
  { value: "fixed", label: "Fixed", detail: "Deterministic token-window baseline" },
  { value: "semantic", label: "Semantic", detail: "Paragraph grouping by embedding similarity" },
  { value: "table_aware", label: "Table-aware", detail: "Preserve markdown tables as blocks" }
];

export default function NewStrategyPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const router = useRouter();
  const [name, setName] = useState("Heading recursive baseline");
  const [splitterType, setSplitterType] = useState<SplitterType>("recursive");
  const [chunkSize, setChunkSize] = useState(600);
  const [overlap, setOverlap] = useState(100);
  const [preserveHeadings, setPreserveHeadings] = useState(true);
  const [preserveTables, setPreserveTables] = useState(true);
  const [semanticThreshold, setSemanticThreshold] = useState(0.72);
  const [error, setError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: () => {
      if (overlap >= chunkSize) {
        throw new Error("Overlap must be smaller than chunk size.");
      }
      return api.createStrategy(projectId, {
        name,
        splitter_type: splitterType,
        chunk_size: chunkSize,
        overlap,
        preserve_headings: preserveHeadings,
        preserve_tables: preserveTables,
        semantic_threshold: splitterType === "semantic" ? semanticThreshold : null,
        config_json: {
          embedding_provider: "deterministic_local",
          indexing_mode: "rbac_safe"
        }
      });
    },
    onSuccess: (strategy) => router.push(`/strategies/${strategy.id}`),
    onError: (err) => setError(err instanceof Error ? err.message : "Strategy creation failed")
  });

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
            <h1 className="text-2xl font-semibold">Create Chunking Strategy</h1>
            <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
              Define a splitter configuration that will generate RBAC-scoped chunks and embeddings.
            </p>
          </div>
          <Badge tone="info">Phase 3</Badge>
        </div>

        <div className="grid gap-5 xl:grid-cols-[1fr_0.65fr]">
          <Card>
            <CardHeader className="flex flex-row items-start justify-between">
              <CardTitle>Strategy Builder</CardTitle>
              <BrainCircuit className="h-5 w-5 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <form
                className="space-y-5"
                onSubmit={(event) => {
                  event.preventDefault();
                  createMutation.mutate();
                }}
              >
                <Field label="Strategy name" value={name} onChange={(event) => setName(event.target.value)} />
                <label className="block text-sm">
                  <span className="font-medium">Splitter type</span>
                  <select
                    className="mt-1 h-10 w-full rounded-md border bg-background px-3 outline-none focus:ring-2 focus:ring-primary"
                    value={splitterType}
                    onChange={(event) => setSplitterType(event.target.value as SplitterType)}
                  >
                    {splitterOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="grid gap-4 md:grid-cols-2">
                  <NumberField label="Chunk size" value={chunkSize} onChange={setChunkSize} min={50} max={4000} />
                  <NumberField label="Overlap" value={overlap} onChange={setOverlap} min={0} max={1000} />
                </div>
                {splitterType === "semantic" ? (
                  <NumberField
                    label="Semantic threshold"
                    value={semanticThreshold}
                    onChange={setSemanticThreshold}
                    min={0}
                    max={1}
                    step={0.01}
                  />
                ) : null}
                <div className="grid gap-3 md:grid-cols-2">
                  <Toggle
                    checked={preserveHeadings}
                    label="Preserve headings"
                    onChange={setPreserveHeadings}
                  />
                  <Toggle checked={preserveTables} label="Preserve tables" onChange={setPreserveTables} />
                </div>
                {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
                <Button disabled={createMutation.isPending} type="submit">
                  <Play className="h-4 w-4" />
                  {createMutation.isPending ? "Creating" : "Create strategy"}
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Splitter Behavior</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {splitterOptions.map((option) => (
                <div
                  key={option.value}
                  className={`rounded-md border p-3 ${
                    option.value === splitterType ? "border-primary bg-primary/5" : "bg-background"
                  }`}
                >
                  <div className="text-sm font-medium">{option.label}</div>
                  <div className="mt-1 text-xs text-muted-foreground">{option.detail}</div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
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

function NumberField({
  label,
  value,
  onChange,
  min,
  max,
  step = 1
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step?: number;
}) {
  return (
    <label className="block text-sm">
      <span className="font-medium">{label}</span>
      <input
        className="mt-1 h-10 w-full rounded-md border bg-background px-3 outline-none focus:ring-2 focus:ring-primary"
        max={max}
        min={min}
        step={step}
        type="number"
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}

function Toggle({
  checked,
  label,
  onChange
}: {
  checked: boolean;
  label: string;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-3 rounded-md border bg-background p-3 text-sm">
      <span className="font-medium">{label}</span>
      <input checked={checked} type="checkbox" onChange={(event) => onChange(event.target.checked)} />
    </label>
  );
}
