"use client";

import {
  Activity,
  BarChart3,
  Database,
  Layers,
  FileText,
  GitCompare,
  Home,
  LockKeyhole,
  Settings,
  ShieldCheck,
  Upload,
  Workflow
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const projectsQuery = useQuery({ queryKey: ["shell-projects"], queryFn: () => api.projects() });
  const project = projectsQuery.data?.[0];
  const projectBase = project ? `/projects/${project.id}` : "/dashboard";
  const navItems = [
    { id: "dashboard", href: "/dashboard", label: "Dashboard", icon: Home },
    {
      id: "documents",
      href: project ? `${projectBase}/documents/upload` : "/dashboard",
      label: "Documents",
      icon: Upload
    },
    {
      id: "strategies",
      href: project ? `${projectBase}/strategies/new` : "/dashboard",
      label: "Strategies",
      icon: Workflow
    },
    { id: "query", href: project ? `${projectBase}/query` : "/dashboard", label: "Query Analysis", icon: Activity },
    { id: "compare", href: project ? `${projectBase}/compare` : "/dashboard", label: "Comparison", icon: GitCompare },
    { id: "data-layer", href: project ? `${projectBase}/data-layer` : "/dashboard", label: "Data Layer", icon: Layers },
    { id: "rbac", href: project ? `${projectBase}/rbac` : "/dashboard", label: "RBAC Safety", icon: ShieldCheck },
    { id: "reports", href: project ? `${projectBase}/reports` : "/dashboard", label: "Reports", icon: FileText },
    { id: "admin", href: "/admin", label: "Admin", icon: Settings }
  ];

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r bg-card lg:block">
        <div className="flex h-16 items-center gap-3 border-b px-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Database className="h-5 w-5" />
          </div>
          <div>
            <div className="text-sm font-semibold">RAG Visual Optimizer</div>
            <div className="text-xs text-muted-foreground">Enterprise RAG intelligence</div>
          </div>
        </div>
        <div className="space-y-6 p-4">
          <div className="rounded-md border bg-background p-3">
            <div className="text-xs uppercase text-muted-foreground">Workspace</div>
            <div className="mt-1 flex items-center justify-between gap-2">
              <span className="truncate text-sm font-medium">Demo Workspace</span>
              <Badge tone="info">Owner</Badge>
            </div>
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = item.href === "/dashboard" ? pathname === item.href : pathname.startsWith(item.href);
              return (
                <Link
                  key={item.id}
                  href={item.href}
                  className={cn(
                    "flex h-10 items-center gap-3 rounded-md px-3 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
                    active && "bg-muted text-foreground"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>
      <main className="lg:pl-72">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b bg-background/95 px-5 backdrop-blur">
          <div>
            <div className="text-sm font-semibold">Optimization Console</div>
            <div className="text-xs text-muted-foreground">Workspace-scoped and RBAC enforced</div>
          </div>
          <div className="flex items-center gap-2">
            <Badge tone="success">API healthy</Badge>
            <Badge tone="success">Phase 8</Badge>
            <LockKeyhole className="h-4 w-4 text-muted-foreground" />
          </div>
        </header>
        <div className="p-5">{children}</div>
      </main>
    </div>
  );
}
