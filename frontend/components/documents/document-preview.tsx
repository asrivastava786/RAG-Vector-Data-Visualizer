import { AlertTriangle, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DocumentDetail } from "@/types/api";

export function DocumentPreview({ document }: { document: DocumentDetail }) {
  const warnings = document.preview.warnings ?? [];
  const structureEntries = Object.entries(document.preview.structure ?? {});

  return (
    <div className="grid gap-5 xl:grid-cols-[1.4fr_0.8fr]">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Parsed Document Preview</CardTitle>
          <Badge tone="neutral">{document.preview.character_count.toLocaleString()} chars</Badge>
        </CardHeader>
        <CardContent>
          <div className="max-h-[620px] overflow-auto rounded-md border bg-background p-4 font-mono text-sm leading-6 text-foreground">
            {document.preview.text ? (
              <pre className="whitespace-pre-wrap">{document.preview.text}</pre>
            ) : (
              <div className="flex min-h-48 items-center justify-center text-muted-foreground">
                No extracted text yet. Run processing after upload.
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="space-y-5">
        <Card>
          <CardHeader>
            <CardTitle>Detected Structure</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {structureEntries.length ? (
              structureEntries.map(([key, value]) => (
                <div key={key} className="rounded-md border bg-background p-3">
                  <div className="text-xs uppercase text-muted-foreground">{key}</div>
                  <div className="mt-1 break-words text-sm">{renderValue(value)}</div>
                </div>
              ))
            ) : (
              <EmptyState icon={FileText} label="Structure metadata will appear after processing." />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Warnings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {warnings.length ? (
              warnings.map((warning) => (
                <div key={warning} className="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                  <AlertTriangle className="mt-0.5 h-4 w-4" />
                  <span>{warning}</span>
                </div>
              ))
            ) : (
              <EmptyState icon={AlertTriangle} label="No extraction warnings recorded." />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function renderValue(value: unknown) {
  if (Array.isArray(value)) {
    return value.length ? `${value.length} detected` : "None";
  }
  if (typeof value === "object" && value !== null) {
    return JSON.stringify(value);
  }
  return String(value);
}

function EmptyState({ icon: Icon, label }: { icon: React.ElementType; label: string }) {
  return (
    <div className="flex items-center gap-2 rounded-md border bg-background p-3 text-sm text-muted-foreground">
      <Icon className="h-4 w-4" />
      {label}
    </div>
  );
}
