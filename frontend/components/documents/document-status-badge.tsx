import { Badge } from "@/components/ui/badge";

export function DocumentStatusBadge({ status }: { status: string }) {
  const tone =
    status === "processed"
      ? "success"
      : status === "failed"
        ? "danger"
        : status === "processing"
          ? "warning"
          : "info";
  return <Badge tone={tone}>{status}</Badge>;
}

