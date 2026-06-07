"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { Badge } from "@/components/ui/badge";
import type { StrategyLeaderboardRow } from "@/types/api";

export function StrategyLeaderboard({ rows }: { rows: StrategyLeaderboardRow[] }) {
  if (!rows.length) {
    return (
      <div className="flex min-h-44 items-center justify-center rounded-md border bg-background text-sm text-muted-foreground">
        No leaderboard data yet.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="h-64 rounded-md border bg-background p-3">
        <ResponsiveContainer height="100%" width="100%">
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="strategy_name" tick={{ fontSize: 11 }} />
            <YAxis tickFormatter={(value) => `${Math.round(Number(value) * 100)}%`} />
            <Tooltip formatter={(value) => `${Math.round(Number(value) * 100)}%`} />
            <Bar dataKey="overall_score" fill="#0f766e" name="Overall score" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="overflow-hidden rounded-md border">
        <table className="w-full text-left text-sm">
          <thead className="bg-muted text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-3 py-2">Strategy</th>
              <th className="px-3 py-2">Score</th>
              <th className="px-3 py-2">Precision</th>
              <th className="px-3 py-2">Recall</th>
              <th className="px-3 py-2">Latency</th>
              <th className="px-3 py-2">RBAC</th>
              <th className="px-3 py-2">Recommendation</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={row.strategy_id} className="border-t bg-background">
                <td className="px-3 py-3 font-medium">
                  <div className="flex items-center gap-2">
                    {row.strategy_name}
                    {index === 0 && !row.rbac_leakage_count ? <Badge tone="success">Best</Badge> : null}
                  </div>
                </td>
                <td className="px-3 py-3">{formatPercent(row.overall_score)}</td>
                <td className="px-3 py-3">{formatPercent(row.context_precision)}</td>
                <td className="px-3 py-3">{formatPercent(row.context_recall)}</td>
                <td className="px-3 py-3">{Math.round(row.latency_ms)} ms</td>
                <td className="px-3 py-3">
                  <Badge tone={row.rbac_leakage_count ? "danger" : "success"}>
                    {row.rbac_leakage_count}
                  </Badge>
                </td>
                <td className="px-3 py-3">{row.recommendation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}
