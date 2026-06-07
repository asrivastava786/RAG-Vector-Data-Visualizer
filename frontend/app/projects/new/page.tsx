"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, FolderPlus } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

const useCases = [
  "HR policy assistant",
  "legal contract QA",
  "technical documentation",
  "finance reports",
  "customer support KB",
  "medical records",
  "compliance documents",
  "custom"
];

export default function NewProjectPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [name, setName] = useState("New RAG Optimization Project");
  const [description, setDescription] = useState("");
  const [useCase, setUseCase] = useState(useCases[0]);
  const [workspaceName, setWorkspaceName] = useState("New Optimization Workspace");
  const [error, setError] = useState<string | null>(null);
  const workspacesQuery = useQuery({ queryKey: ["workspaces"], queryFn: api.workspaces });
  const workspaceId = workspacesQuery.data?.[0]?.id ?? "";
  const workspaceError =
    workspacesQuery.error instanceof Error ? workspacesQuery.error.message : "Unable to load workspaces.";
  const workspaceReady = Boolean(workspaceId);
  const createWorkspaceMutation = useMutation({
    mutationFn: () => api.createWorkspace({ name: workspaceName }),
    onSuccess: async () => {
      setError(null);
      await queryClient.invalidateQueries({ queryKey: ["workspaces"] });
      await queryClient.invalidateQueries({ queryKey: ["shell-projects"] });
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Workspace creation failed")
  });
  const createMutation = useMutation({
    mutationFn: () => {
      if (workspacesQuery.isPending) {
        throw new Error("Workspace membership is still loading.");
      }
      if (workspacesQuery.isError) {
        throw new Error(workspaceError);
      }
      if (!workspaceId) {
        throw new Error("Create a workspace before creating a project.");
      }
      return api.createProject({
        workspace_id: workspaceId,
        name,
        description: description || null,
        use_case: useCase
      });
    },
    onSuccess: (project) => router.push(`/projects/${project.id}`),
    onError: (err) => setError(err instanceof Error ? err.message : "Project creation failed")
  });

  return (
    <AppShell>
      <section className="space-y-5">
        <div className="flex items-end justify-between gap-4">
          <div>
            <Link className="mb-2 inline-flex items-center gap-2 text-sm text-muted-foreground" href="/dashboard">
              <ArrowLeft className="h-4 w-4" />
              Dashboard
            </Link>
            <h1 className="text-2xl font-semibold">Create Project</h1>
            <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
              Create a workspace-scoped RAG optimization project with a use-case profile.
            </p>
          </div>
          <Badge tone="info">Workspace scoped</Badge>
        </div>

        {workspacesQuery.isError ? (
          <Card className="max-w-3xl border-red-200 bg-red-50">
            <CardHeader>
              <CardTitle>Workspace Unavailable</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-red-800">
              <p>{workspaceError}</p>
              <Link className="inline-flex font-medium underline" href="/login">
                Sign in again
              </Link>
            </CardContent>
          </Card>
        ) : null}

        {!workspacesQuery.isPending && !workspacesQuery.isError && !workspaceReady ? (
          <Card className="max-w-3xl">
            <CardHeader className="flex flex-row items-start justify-between">
              <CardTitle>Workspace Setup</CardTitle>
              <Badge tone="warning">Required</Badge>
            </CardHeader>
            <CardContent>
              <form
                className="space-y-4"
                onSubmit={(event) => {
                  event.preventDefault();
                  createWorkspaceMutation.mutate();
                }}
              >
                <Field
                  label="Workspace name"
                  value={workspaceName}
                  onChange={(event) => setWorkspaceName(event.target.value)}
                />
                <Button disabled={createWorkspaceMutation.isPending || !workspaceName.trim()} type="submit">
                  <FolderPlus className="h-4 w-4" />
                  {createWorkspaceMutation.isPending ? "Creating workspace" : "Create workspace"}
                </Button>
              </form>
            </CardContent>
          </Card>
        ) : null}

        <Card className="max-w-3xl">
          <CardHeader className="flex flex-row items-start justify-between">
            <CardTitle>Project Details</CardTitle>
            <FolderPlus className="h-5 w-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <form
              className="space-y-4"
              onSubmit={(event) => {
                event.preventDefault();
                createMutation.mutate();
              }}
            >
              <Field label="Name" value={name} onChange={(event) => setName(event.target.value)} />
              <Field
                label="Description"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
              />
              <label className="block text-sm">
                <span className="font-medium">Use case</span>
                <select
                  className="mt-1 h-10 w-full rounded-md border bg-background px-3 outline-none focus:ring-2 focus:ring-primary"
                  value={useCase}
                  onChange={(event) => setUseCase(event.target.value)}
                >
                  {useCases.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
              {workspaceReady ? (
                <div className="rounded-md border bg-muted/40 p-3 text-sm text-muted-foreground">
                  Project will be created in {workspacesQuery.data?.[0]?.name}.
                </div>
              ) : null}
              {error ? (
                <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
              ) : null}
              <Button disabled={createMutation.isPending || workspacesQuery.isPending || workspacesQuery.isError} type="submit">
                <FolderPlus className="h-4 w-4" />
                {createMutation.isPending ? "Creating" : "Create project"}
              </Button>
            </form>
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
