"use client";

import { useEffect, useRef } from "react";
import type { GraphResponse } from "@/types/api";

type CytoscapeInstance = {
  destroy: () => void;
  fit: () => void;
};

type CytoscapeModule = {
  default: (options: Record<string, unknown>) => CytoscapeInstance;
};

export function SemanticGraph({ data }: { data?: GraphResponse }) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!ref.current || !data?.nodes.length) {
      return;
    }
    const graphData = data;
    let graph: CytoscapeInstance | null = null;
    let mounted = true;
    async function render() {
      const cytoscape = ((await import("cytoscape")) as CytoscapeModule).default;
      if (!mounted || !ref.current) {
        return;
      }
      graph = cytoscape({
        container: ref.current,
        elements: [
          ...graphData.nodes.map((node) => ({
            data: {
              id: node.id,
              label: node.label,
              type: node.type
            }
          })),
          ...graphData.edges.map((edge) => ({
            data: {
              id: `${edge.source}_${edge.target}`,
              source: edge.source,
              target: edge.target,
              label: edge.label,
              weight: edge.weight
            }
          }))
        ],
        style: [
          {
            selector: "node",
            style: {
              "background-color": "data(type)",
              label: "data(label)",
              color: "#0f172a",
              "font-size": "11px",
              "text-wrap": "wrap",
              "text-max-width": "110px",
              width: 34,
              height: 34
            }
          },
          { selector: 'node[type = "query"]', style: { "background-color": "#0f766e", width: 46, height: 46 } },
          { selector: 'node[type = "document"]', style: { "background-color": "#7c3aed" } },
          { selector: 'node[type = "chunk"]', style: { "background-color": "#2563eb" } },
          {
            selector: "edge",
            style: {
              width: "mapData(weight, 0, 1, 1, 6)",
              "line-color": "#94a3b8",
              "target-arrow-color": "#94a3b8",
              "target-arrow-shape": "triangle",
              "curve-style": "bezier",
              label: "data(label)",
              "font-size": "9px",
              color: "#475569"
            }
          }
        ],
        layout: { name: "breadthfirst", directed: true, padding: 24, spacingFactor: 1.15 }
      });
      graph.fit();
    }
    void render();
    return () => {
      mounted = false;
      graph?.destroy();
    };
  }, [data]);

  if (!data?.nodes.length) {
    return <EmptyVisual label="Run a query to generate the query-to-chunk graph." />;
  }

  return <div ref={ref} className="h-[360px] w-full rounded-md border bg-background" />;
}

function EmptyVisual({ label }: { label: string }) {
  return (
    <div className="flex h-[360px] items-center justify-center rounded-md border bg-background text-sm text-muted-foreground">
      {label}
    </div>
  );
}
