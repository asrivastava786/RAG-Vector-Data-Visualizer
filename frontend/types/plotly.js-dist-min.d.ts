declare module "plotly.js-dist-min" {
  type PlotlyElement = HTMLDivElement;

  export function react(
    element: PlotlyElement,
    data: Array<Record<string, unknown>>,
    layout: Record<string, unknown>,
    config: Record<string, unknown>
  ): Promise<unknown>;

  export function purge(element: PlotlyElement): void;

  const Plotly: {
    react: typeof react;
    purge: typeof purge;
  };

  export default Plotly;
}
