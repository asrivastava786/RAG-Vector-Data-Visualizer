"use client";

import { useQuery } from "@tanstack/react-query";
import { KeyRound, ScrollText, Settings, Users } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export default function AdminPage() {
  const workspacesQuery = useQuery({ queryKey: ["workspaces"], queryFn: api.workspaces });
  const workspaceId = workspacesQuery.data?.[0]?.id ?? "";
  const usersQuery = useQuery({
    queryKey: ["admin-users", workspaceId],
    queryFn: () => api.adminUsers(workspaceId),
    enabled: Boolean(workspaceId)
  });
  const logsQuery = useQuery({
    queryKey: ["admin-audit-logs", workspaceId],
    queryFn: () => api.adminAuditLogs(workspaceId),
    enabled: Boolean(workspaceId)
  });
  const settingsQuery = useQuery({
    queryKey: ["admin-settings", workspaceId],
    queryFn: () => api.adminSettings(workspaceId),
    enabled: Boolean(workspaceId)
  });

  return (
    <AppShell>
      <section className="space-y-5">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <h1 className="text-2xl font-semibold">Admin Settings</h1>
            <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
              Manage workspace users, provider settings, API key placeholders, and audit trails.
            </p>
          </div>
          <Badge tone="info">Phase 7</Badge>
        </div>

        <div className="grid gap-5 xl:grid-cols-2">
          <Card>
            <CardHeader className="flex flex-row items-start justify-between">
              <CardTitle>Users</CardTitle>
              <Users className="h-5 w-5 text-muted-foreground" />
            </CardHeader>
            <CardContent className="space-y-2">
              {(usersQuery.data ?? []).map((user) => (
                <div key={user.user_id} className="flex items-center justify-between rounded-md border bg-background p-3 text-sm">
                  <div>
                    <div className="font-medium">{user.full_name}</div>
                    <div className="text-xs text-muted-foreground">{user.email}</div>
                  </div>
                  <Badge tone={user.is_active ? "success" : "danger"}>{user.role}</Badge>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-start justify-between">
              <CardTitle>Provider Settings</CardTitle>
              <Settings className="h-5 w-5 text-muted-foreground" />
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <Setting label="Storage" value={settingsQuery.data?.storage_provider ?? "-"} />
              <Setting label="Embeddings" value={(settingsQuery.data?.embedding_providers ?? []).join(", ")} />
              <Setting label="Rate limiting" value={settingsQuery.data?.rate_limiting ?? "-"} />
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-5 xl:grid-cols-2">
          <Card>
            <CardHeader className="flex flex-row items-start justify-between">
              <CardTitle>API Keys</CardTitle>
              <KeyRound className="h-5 w-5 text-muted-foreground" />
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              {settingsQuery.data?.api_keys_placeholder ?? "Loading settings..."}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-start justify-between">
              <CardTitle>Audit Logs</CardTitle>
              <ScrollText className="h-5 w-5 text-muted-foreground" />
            </CardHeader>
            <CardContent className="max-h-96 space-y-2 overflow-auto">
              {(logsQuery.data ?? []).map((log) => (
                <div key={log.id} className="rounded-md border bg-background p-3 text-sm">
                  <div className="font-medium">{log.action}</div>
                  <div className="mt-1 text-xs text-muted-foreground">
                    {log.entity_type} - {new Date(log.created_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </section>
    </AppShell>
  );
}

function Setting({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-background p-3">
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 font-medium">{value}</div>
    </div>
  );
}
