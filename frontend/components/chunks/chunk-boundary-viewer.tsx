import { AlertTriangle, Braces, FileText, LockKeyhole } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ChunkRecord } from "@/types/api";

export function ChunkBoundaryViewer({ chunks }: { chunks: ChunkRecord[] }) {
  if (!chunks.length) {
    return (
      <div className="flex min-h-52 items-center justify-center rounded-md border bg-background text-sm text-muted-foreground">
        No indexed chunks are visible for this role yet.
      </div>
    );
  }

  return (
    <div className="grid gap-4">
      {chunks.map((chunk) => {
        const warnings = chunk.metadata_json.warnings ?? [];
        return (
          <Card key={chunk.id}>
            <CardHeader className="flex flex-row items-start justify-between gap-4">
              <div>
                <CardTitle>Chunk {chunk.chunk_index + 1}</CardTitle>
                <div className="mt-1 flex flex-wrap gap-2 text-xs text-muted-foreground">
                  <span>{chunk.token_count} tokens</span>
                  <span>
                    offsets {chunk.start_offset}-{chunk.end_offset}
                  </span>
                  {chunk.section_heading ? <span>{chunk.section_heading}</span> : null}
                </div>
              </div>
              <div className="flex flex-wrap justify-end gap-2">
                {chunk.allowed_roles_json.map((role) => (
                  <Badge key={role} tone="info">
                    {role}
                  </Badge>
                ))}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-md border bg-background p-4 font-mono text-sm leading-6">
                <pre className="max-h-64 whitespace-pre-wrap">{chunk.text}</pre>
              </div>
              <div className="grid gap-3 md:grid-cols-3">
                <MetaPill
                  icon={FileText}
                  label="Source"
                  value={chunk.metadata_json.source_document_title ?? chunk.document_id}
                />
                <MetaPill
                  icon={Braces}
                  label="Splitter"
                  value={String(chunk.metadata_json.splitter ?? "indexed")}
                />
                <MetaPill
                  icon={LockKeyhole}
                  label="Access"
                  value={chunk.allowed_users_json.length ? "Role and user scoped" : "Role scoped"}
                />
              </div>
              {warnings.length ? (
                <div className="flex flex-wrap gap-2">
                  {warnings.map((warning) => (
                    <span
                      key={warning}
                      className="inline-flex items-center gap-1 rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-900"
                    >
                      <AlertTriangle className="h-3.5 w-3.5" />
                      {warning}
                    </span>
                  ))}
                </div>
              ) : null}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

function MetaPill({
  icon: Icon,
  label,
  value
}: {
  icon: React.ElementType;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start gap-2 rounded-md border bg-background p-3">
      <Icon className="mt-0.5 h-4 w-4 text-muted-foreground" />
      <div className="min-w-0">
        <div className="text-xs uppercase text-muted-foreground">{label}</div>
        <div className="truncate text-sm font-medium">{value}</div>
      </div>
    </div>
  );
}
