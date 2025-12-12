import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from "recharts";
import { Agent } from "../App";

interface TimingChartProps {
  agents: Agent[];
}

export function TimingChart({ agents }: TimingChartProps) {
  // Map agents to simple timing data
  const data = agents.map(agent => ({
    name: agent.id.substring(0, 8),
    avg_iteration: parseFloat(agent.avg_iteration_time?.toFixed(2) || "0"),
    avg_latency: parseFloat(agent.avg_llm_latency?.toFixed(2) || "0"),
    avg_tool: parseFloat(agent.avg_tool_execution_time?.toFixed(2) || "0")
  }));

  return (
    <div className="h-full w-full">
      <h3 className="text-lg font-semibold text-slate-100 mb-4">System Latency Metrics (Seconds)</h3>
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
            <Legend />
            <Bar dataKey="avg_iteration" name="Total Iteration" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="avg_latency" name="LLM Latency" fill="#a855f7" radius={[4, 4, 0, 0]} />
            <Bar dataKey="avg_tool" name="Tool Exec" fill="#22c55e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
