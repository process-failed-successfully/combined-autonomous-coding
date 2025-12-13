import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from "recharts";
import { Agent } from "../App";

interface ToolUsageChartProps {
  agents: Agent[];
}

const COLORS = {
  bash: "#3b82f6", // blue
  write: "#22c55e", // green
  read: "#f59e0b", // amber
  search: "#a855f7", // purple
};

export function ToolUsageChart({ agents }: ToolUsageChartProps) {
  // Aggregate tool usage across all agents
  const data = [
    { name: "bash", value: 0 },
    { name: "write", value: 0 },
    { name: "read", value: 0 },
    { name: "search", value: 0 },
  ];

  agents.forEach((agent) => {
    if (agent.tool_usage) {
      data[0].value += agent.tool_usage.bash || 0;
      data[1].value += agent.tool_usage.write || 0;
      data[2].value += agent.tool_usage.read || 0;
      data[3].value += agent.tool_usage.search || 0;
    }
  });

  return (
    <div className="h-full w-full">
      <h3 className="text-lg font-semibold text-slate-100 mb-4">Tool Usage Distribution</h3>
      <div className="h-[250px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="name" stroke="#64748b" />
            <YAxis stroke="#64748b" />
            <Tooltip
              contentStyle={{ backgroundColor: "#0f172a", borderColor: "#1e293b" }}
              itemStyle={{ color: "#f8fafc" }}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[entry.name as keyof typeof COLORS] || "#64748b"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
