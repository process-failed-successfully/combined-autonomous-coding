import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

interface AgentData {
  id: string;
  total_iterations: number;
  loc_count: number;
  is_running: boolean;
  manager_approvals: number;
  manager_rejections: number;
}

interface PerformanceGraphProps {
  data: AgentData[];
  type: "iterations" | "status" | "decisions";
}

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8"];

export function PerformanceGraph({ data, type }: PerformanceGraphProps) {
  if (type === "iterations") {
    return (
      <div className="h-[300px] w-full">
         <h4 className="text-sm font-medium mb-4">Total Iterations per Agent</h4>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis dataKey="id" tick={{ fontSize: 12 }} tickFormatter={(val) => val.split("-")[0]} />
            <YAxis />
            <Tooltip 
                contentStyle={{ backgroundColor: "#1f2937", border: "none", color: "#f3f4f6" }}
                itemStyle={{ color: "#f3f4f6" }}
            />
            <Bar dataKey="total_iterations" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (type === "decisions") {
      const decisionData = data.map(agent => ({
          name: agent.id.split('-')[0],
          Approvals: agent.manager_approvals,
          Rejections: agent.manager_rejections
      }));

       return (
      <div className="h-[300px] w-full">
         <h4 className="text-sm font-medium mb-4">Manager Decisions</h4>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={decisionData}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis />
            <Tooltip 
                 contentStyle={{ backgroundColor: "#1f2937", border: "none", color: "#f3f4f6" }}
                 itemStyle={{ color: "#f3f4f6" }}
            />
            <Bar dataKey="Approvals" fill="#22c55e" stackId="a" radius={[0, 0, 4, 4]} />
            <Bar dataKey="Rejections" fill="#ef4444" stackId="a" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (type === "status") {
    const active = data.filter((d) => d.is_running).length;
    const idle = data.length - active;
    const pieData = [
      { name: "Active", value: active },
      { name: "Offline", value: idle },
    ];

    return (
      <div className="h-[300px] w-full">
        <h4 className="text-sm font-medium mb-4">Agent Status</h4>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              fill="#8884d8"
              paddingAngle={5}
              dataKey="value"
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={index === 0 ? "#22c55e" : "#64748b"} />
              ))}
            </Pie>
            <Tooltip 
                 contentStyle={{ backgroundColor: "#1f2937", border: "none", color: "#f3f4f6" }}
                 itemStyle={{ color: "#f3f4f6" }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return null;
}
