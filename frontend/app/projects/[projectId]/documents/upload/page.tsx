"use client";

import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, FileUp, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { WorkspaceRole } from "@/types/api";

const roles: WorkspaceRole[] = ["owner", "admin", "developer", "analyst", "viewer"];

export default function DocumentUploadPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [selectedRoles, setSelectedRoles] = useState<WorkspaceRole[]>(["owner", "admin", "developer"]);
  const [tags, setTags] = useState("policy, source");
  const [department, setDepartment] = useState("");
  const [sensitivity, setSensitivity] = useState("internal");
  const [error, setError] = useState<string | null>(null);

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!file) {
        throw new Error("Choose a document to upload.");
      }
      if (!selectedRoles.length) {
        throw new Error("Select at least one allowed role.");
      }
      return api.uploadDocument(projectId, {
        title: title || file.name,
        file,
        allowedRoles: selectedRoles,
        tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean),
        metadata: {
          department,
          sensitivity,
          source: "manual_upload"
        }
      });
    },
    onSuccess: (document) => {
      router.push(`/documents/${document.id}`);
    },
    onError: (err) => setError(err instanceof Error ? err.message : "Upload failed")
  });

  function toggleRole(role: WorkspaceRole) {
    setSelectedRoles((current) =>
      current.includes(role) ? current.filter((item) => item !== role) : [...current, role]
    );
  }

  return (
    <AppShell>
      <section className="space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <Link className="mb-2 inline-flex items-center gap-2 text-sm text-muted-foreground" href={`/projects/${projectId}`}>
              <ArrowLeft className="h-4 w-4" />
              Project dashboard
            </Link>
            <h1 className="text-2xl font-semibold">Upload Source Document</h1>
            <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
              Store the original document, capture access rules, and start the extraction pipeline used by chunk inspection.
            </p>
          </div>
          <Badge tone="info">Phase 2</Badge>
        </div>

        <div className="grid gap-5 xl:grid-cols-[1fr_0.7fr]">
          <Card>
            <CardHeader>
              <CardTitle>Document Metadata</CardTitle>
            </CardHeader>
            <CardContent>
              <form
                className="space-y-5"
                onSubmit={(event) => {
                  event.preventDefault();
                  uploadMutation.mutate();
                }}
              >
                <Field label="Title" value={title} onChange={(event) => setTitle(event.target.value)} />
                <label className="block text-sm">
                  <span className="font-medium">Document file</span>
                  <input
                    className="mt-1 block w-full rounded-md border bg-background p-2 text-sm"
                    type="file"
                    accept=".pdf,.docx,.txt,.md,.html,.htm"
                    onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                  />
                </label>
                <div className="grid gap-4 md:grid-cols-2">
                  <Field label="Department" value={department} onChange={(event) => setDepartment(event.target.value)} />
                  <Field label="Sensitivity" value={sensitivity} onChange={(event) => setSensitivity(event.target.value)} />
                </div>
                <Field label="Tags" value={tags} onChange={(event) => setTags(event.target.value)} />
                <div>
                  <div className="text-sm font-medium">Allowed roles</div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {roles.map((role) => (
                      <button
                        key={role}
                        className={`rounded-md border px-3 py-2 text-sm capitalize ${
                          selectedRoles.includes(role) ? "border-primary bg-primary text-primary-foreground" : "bg-background"
                        }`}
                        type="button"
                        onClick={() => toggleRole(role)}
                      >
                        {role}
                      </button>
                    ))}
                  </div>
                </div>
                {error ? <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
                <Button disabled={uploadMutation.isPending} type="submit">
                  <FileUp className="h-4 w-4" />
                  {uploadMutation.isPending ? "Uploading" : "Upload and process"}
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-start justify-between">
              <CardTitle>Access Guardrails</CardTitle>
              <ShieldCheck className="h-5 w-5 text-muted-foreground" />
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <p>Backend upload requires developer-or-higher workspace access.</p>
              <p>Document records are workspace and project scoped at creation time.</p>
              <p>Allowed roles and users are stored with the document and copied into chunks in Phase 3.</p>
              <p>Non-admin users only see documents matching their role or explicit user grant.</p>
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
