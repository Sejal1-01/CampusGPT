import { CHART_SERIES_COUNT } from "../config";

export function readChartColors(): string[] {
  const styles = getComputedStyle(document.documentElement);
  return Array.from({ length: CHART_SERIES_COUNT }, (_, index) => {
    const variable = `--chart-series-${index + 1}`;
    return styles.getPropertyValue(variable).trim() || `var(${variable})`;
  });
}
