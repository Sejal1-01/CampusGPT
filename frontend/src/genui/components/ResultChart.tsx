import { memo, useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { readChartColors } from "../../lib/chartColors";
import { X_KEY, type ChartKind, type ChartPoint } from "../chartPlan";

interface ResultChartProps {
  kind: ChartKind;
  points: ChartPoint[];
  series: string[];
  xLabel: string;
}

const CHART_HEIGHT_PX = 300;

function colorAt(colors: string[], index: number): string {
  return colors[index % colors.length] ?? "currentColor";
}

function PieView({
  points,
  series,
  colors,
}: {
  points: ChartPoint[];
  series: string[];
  colors: string[];
}) {
  const valueKey = series[0] ?? "";
  return (
    <PieChart>
      <Pie data={points} dataKey={valueKey} nameKey={X_KEY} outerRadius="80%" label>
        {points.map((point, index) => (
          <Cell key={String(point[X_KEY])} fill={colorAt(colors, index)} />
        ))}
      </Pie>
      <Tooltip />
      <Legend />
    </PieChart>
  );
}

function CartesianView({
  kind,
  points,
  series,
  xLabel,
  colors,
}: ResultChartProps & { colors: string[] }) {
  const axes = [
    <CartesianGrid key="grid" strokeDasharray="3 3" stroke="var(--color-border)" />,
    <XAxis key="x" dataKey={X_KEY} name={xLabel} tick={{ fontSize: 12 }} />,
    <YAxis key="y" tick={{ fontSize: 12 }} />,
    <Tooltip key="tooltip" />,
    series.length > 1 ? <Legend key="legend" /> : null,
  ];
  if (kind === "line") {
    return (
      <LineChart data={points}>
        {axes}
        {series.map((name, index) => (
          <Line
            key={name}
            type="monotone"
            dataKey={name}
            stroke={colorAt(colors, index)}
            strokeWidth={2}
            connectNulls={false}
          />
        ))}
      </LineChart>
    );
  }
  return (
    <BarChart data={points}>
      {axes}
      {series.map((name, index) => (
        <Bar key={name} dataKey={name} fill={colorAt(colors, index)} radius={[4, 4, 0, 0]} />
      ))}
    </BarChart>
  );
}

function ResultChart(props: ResultChartProps) {
  const colors = useMemo(() => readChartColors(), []);
  return (
    <div className="result-chart" data-testid={`result-chart-${props.kind}`}>
      <ResponsiveContainer width="100%" height={CHART_HEIGHT_PX}>
        {props.kind === "pie" ? (
          <PieView points={props.points} series={props.series} colors={colors} />
        ) : (
          <CartesianView {...props} colors={colors} />
        )}
      </ResponsiveContainer>
    </div>
  );
}

export default memo(ResultChart);
