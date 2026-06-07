"use client";

import { useEffect, useRef } from "react";
import type { ScatterResponse } from "@/types/api";

type PlotlyLike = {
  react: (
    element: HTMLDivElement,
    data: Array<Record<string, unknown>>,
    layout: Record<string, unknown>,
    config: Record<string, unknown>
  ) => Promise<unknown>;
  purge: (element: HTMLDivElement) => void;
};

type PlotlyModule = PlotlyLike & { default?: PlotlyLike };

export function EmbeddingScatterPlot({ data }: { data?: ScatterResponse }) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let mounted = true;
    const element = ref.current;
    async function render() {
      if (!element || !data?.points.length) {
        return;
      }
      const loaded = (await import("plotly.js-dist-min")) as PlotlyModule;
      const plotly = loaded.default ?? loaded;
      if (!mounted) {
        return;
      }
      const groups = groupByType(data.points);
      await plotly.react(
        element,
        Object.entries(groups).map(([type, points]) => ({
          type: "scatter",
          mode: "markers+text",
          name: type,
          x: points.map((point) => point.x),
          y: points.map((point) => point.y),
          text: points.map((point) => point.label),
          textposition: "top center",
          marker: {
            size: points.map((point) => (point.type === "query" ? 18 : 10 + point.score * 12)),
            color: points.map((point) => colorForType(point.type)),
            line: { color: "#0f172a", width: 1 }
          },
          customdata: points.map((point) => [point.cluster, point.score]),
          hovertemplate: "%{text}<br>cluster: %{customdata[0]}<br>score: %{customdata[1]:.2f}<extra></extra>"
        })),
        {
          autosize: true,
          margin: { l: 28, r: 18, t: 18, b: 28 },
          paper_bgcolor: "rgba(0,0,0,0)",
          plot_bgcolor: "rgba(0,0,0,0)",
          xaxis: { zeroline: true, title: "" },
          yaxis: { zeroline: true, title: "" },
          showlegend: true,
          legend: { orientation: "h" }
        },
        { displayModeBar: false, responsive: true }
      );
    }
    void render();
    return () => {
      mounted = false;
      if (element) {
        void import("plotly.js-dist-min").then((loaded) => {
          const plotly = (loaded as PlotlyModule).default ?? (loaded as PlotlyModule);
          plotly.purge(element);
        });
      }
    };
  }, [data]);

  if (!data?.points.length) {
    return <EmptyVisual label="Run a query to generate scatter points." />;
  }

  return <div ref={ref} className="h-[360px] w-full" />;
}

function groupByType(points: ScatterResponse["points"]) {
  return points.reduce<Record<string, ScatterResponse["points"]>>((groups, point) => {
    groups[point.type] = groups[point.type] ?? [];
    groups[point.type].push(point);
    return groups;
  }, {});
}

function colorForType(type: string) {
  if (type === "query") {
    return "#0f766e";
  }
  if (type === "document") {
    return "#7c3aed";
  }
  return "#2563eb";
}

function EmptyVisual({ label }: { label: string }) {
  return (
    <div className="flex h-[360px] items-center justify-center rounded-md border bg-background text-sm text-muted-foreground">
      {label}
    </div>
  );
}
