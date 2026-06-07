"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { DocumentPreview } from "@/components/documents/document-preview";
import { DocumentStatusBadge } from "@/components/documents/document-status-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export default function DocumentDetailPage() {
  const params = useParams<{ documentId: string }>();
  const documentId = params.documentId;
  const queryClient = useQueryClient();
  const documentQuery = useQuery({
    queryKey: ["document", documentId],
    queryFn: () => api.document(documentId),
    retry: false
  });
  const processMutation = useMutation({
    mutationFn: () => api.processDocument(documentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["document", documentId] })
  });

  return (
    <AppShell>
      <section className="space-y-5">
        {documentQuery.data ? (
          <>
            <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
              <div>
                <Link className="mb-2 inline-flex items-center gap-2 text-sm text-muted-foreground" href={`/projects/${documentQuery.data.project_id}`}>
                  <ArrowLeft className="h-4 w-4" />
                  Project dashboard
                </Link>
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <DocumentStatusBadge status={documentQuery.data.status} />
                  {documentQuery.data.tags_json.map((tag) => (
                    <Badge key={tag} tone="neutral">{tag}</Badge>
                  ))}
                </div>
                <h1 className="text-2xl font-semibold">{documentQuery.data.title}</h1>
                <p className="mt-1 text-sm text-muted-foreground">{documentQuery.data.filename}</p>
              </div>
              <Button
                disabled={processMutation.isPending}
                variant="secondary"
                onClick={() => processMutation.mutate()}
              >
                <RefreshCw className="h-4 w-4" />
                {processMutation.isPending ? "Processing" : "Run processing"}
              </Button>
            </div>

            <div className="grid gap-4 md:grid-cols-4">
              <InfoCard label="Content type" value={documentQuery.data.content_type} />
              <InfoCard label="Pages" value={documentQuery.data.page_count?.toString() ?? "n/a"} />
              <InfoCard label="Allowed roles" value={documentQuery.data.allowed_roles_json.join(", ")} />
              <InfoCard label="Updated" value={new Date(documentQuery.data.updated_at).toLocaleDateString()} />
            </div>

            <DocumentPreview document={documentQuery.data} />
          </>
        ) : documentQuery.isError ? (
          <Card>
            <CardHeader>
              <CardTitle>Document unavailable</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              The document could not be loaded. It may not exist, or your current role may not have access to it.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            <div className="h-20 animate-pulse rounded-md bg-muted" />
            <div className="h-96 animate-pulse rounded-md bg-muted" />
          </div>
        )}
      </section>
    </AppShell>
  );
}

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-xs uppercase text-muted-foreground">{label}</div>
        <div className="mt-1 truncate text-sm font-medium">{value}</div>
      </CardContent>
    </Card>
  );
}
