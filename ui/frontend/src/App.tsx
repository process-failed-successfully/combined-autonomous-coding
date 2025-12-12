import { useEffect, useState } from "react";
import { 
  LayoutDashboard, 
  Terminal as TerminalIcon, 
  Activity, 
  Code2, 
  CheckCircle2, 
  XCircle,
  Zap,
  BarChart3
} from "lucide-react";
import { AgentCard } from "./components/AgentCard";
import { StatsCard } from "./components/StatsCard";
import { PerformanceGraph } from "./components/PerformanceGraph";
import { ToolUsageChart } from "./components/ToolUsageChart";
import { TimingChart } from "./components/TimingChart";
import { cn } from "./lib/utils";

// Matching backend AgentState exactly
export interface Agent {
  id: string;
  is_running: boolean;
  is_paused: boolean;
  iteration: number;
  current_task: string;
  last_log: string[];
  last_heartbeat: number;
  // New Metrics
  loc_count: number;
  manager_approvals: number;
  manager_rejections: number;
  total_iterations: number;
  
  // Advanced Dev Metrics
  start_time: number;
  error_count: number;
  total_errors: number;
  tool_usage: Record<string, number>;
  avg_iteration_time: number;
  avg_llm_latency: number;
  avg_tool_execution_time: number;
  feature_completion_count: number;
  feature_completion_pct: number;
}

function App() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "performance" | "development">("overview");

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const res = await fetch("/api/dashboard");
        const data = await res.json();
        setAgents(data);
      } catch (e) {
        console.error("Failed to fetch agents", e);
      } finally {
        setLoading(false);
      }
    };

    fetchAgents();
    const interval = setInterval(fetchAgents, 1000);
    return () => clearInterval(interval);
  }, []);

  // Computed Stats
  const activeAgents = agents.filter((a) => a.is_running).length;
  const totalIterations = agents.reduce((sum, a) => sum + (a.total_iterations || a.iteration || 0), 0);
  const totalLoc = agents.reduce((sum, a) => sum + (a.loc_count || 0), 0);
  
  const totalApprovals = agents.reduce((sum, a) => sum + (a.manager_approvals || 0), 0);
  const totalRejections = agents.reduce((sum, a) => sum + (a.manager_rejections || 0), 0);
  const approvalRate = totalApprovals + totalRejections > 0 
    ? Math.round((totalApprovals / (totalApprovals + totalRejections)) * 100) 
    : 0;

  // Global Feature Progress (Average across agents or max?)
  // Assuming single project for now, so max or first agent is fine.
  const featureCount = agents.length > 0 ? Math.max(...agents.map(a => a.feature_completion_count || 0)) : 0;
  const featurePct = agents.length > 0 ? Math.max(...agents.map(a => a.feature_completion_pct || 0)) : 0;
    
  // Handlers required by AgentCard
  const handleControl = async (id: string, cmd: string) => {
    try {
      await fetch('/api/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: id, command: cmd })
      });
      // Optimistic update
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 font-sans selection:bg-blue-500/30">
      {/* Sidebar / Navigation */}
      <div className="fixed left-0 top-0 h-full w-64 border-r border-slate-800 bg-slate-900/50 backdrop-blur-xl p-6">
        <div className="flex items-center gap-3 mb-8">
          <div className="h-8 w-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
            <Zap className="h-5 w-5 text-blue-500" />
          </div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            AgentZero
          </h1>
        </div>

        <nav className="space-y-2">
          <button
            onClick={() => setActiveTab("overview")}
            className={cn(
              "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200",
              activeTab === "overview"
                ? "bg-blue-500/10 text-blue-400 shadow-sm"
                : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
            )}
          >
            <LayoutDashboard className="h-4 w-4" />
            Overview
          </button>
          
           <button
            onClick={() => setActiveTab("performance")}
            className={cn(
              "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200",
              activeTab === "performance"
                ? "bg-blue-500/10 text-blue-400 shadow-sm"
                : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
            )}
          >
            <Activity className="h-4 w-4" />
            Performance
          </button>

          <button
            onClick={() => setActiveTab("development")}
            className={cn(
              "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200",
              activeTab === "development"
                ? "bg-blue-500/10 text-blue-400 shadow-sm"
                : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
            )}
          >
            <BarChart3 className="h-4 w-4" />
            Development
          </button>
        </nav>
      </div>

      {/* Main Content */}
      <main className="pl-64">
        <div className="max-w-[1600px] mx-auto p-8 space-y-8">
          
          {/* Header */}
          <div className="flex items-center justify-between">
            <h2 className="text-3xl font-bold tracking-tight text-slate-100">
              {activeTab === "overview" ? "Mission Control" : activeTab === "performance" ? "Performance Analytics" : "Development Metrics"}
            </h2>
            <div className="flex items-center gap-2 text-sm text-slate-400 bg-slate-900/50 px-4 py-2 rounded-full border border-slate-800">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              System Operational
            </div>
          </div>

          {/* Key Metrics Row (All Tabs for now, slightly cleaner) */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatsCard
              title="Active Agents"
              value={activeAgents}
              icon={TerminalIcon}
              description="Agents currently running tasks"
              trend={activeAgents > 0 ? "+ Online" : "Offline"}
              className="bg-slate-900 border-slate-800"
            />
            <StatsCard
              title="Total Iterations"
              value={totalIterations.toLocaleString()}
              icon={Activity}
              description="Cumulative autonomous cycles"
              className="bg-slate-900 border-slate-800"
            />
             {activeTab === "development" ? (
                <>
                    <StatsCard
                        title="Feature Progress"
                        value={`${featureCount} Done`}
                        icon={CheckCircle2}
                        description={`Verification: ${featurePct.toFixed(1)}%`}
                        className="bg-slate-900 border-slate-800"
                    />
                    <StatsCard
                        title="Avg Latency"
                        value={`${(agents[0]?.avg_llm_latency || 0).toFixed(1)}s`}
                        icon={Zap}
                        description="Mean LLM Response Time"
                        className="bg-slate-900 border-slate-800"
                    />
                </>
             ) : (
                <>
                    <StatsCard
                    title="Lines of Code"
                    value={totalLoc.toLocaleString()}
                    icon={Code2}
                    description="Total code generated/modified"
                    trend="+12% vs last session"
                    className="bg-slate-900 border-slate-800"
                    />
                    <StatsCard
                    title="Manager Approval Rate"
                    value={`${approvalRate}%`}
                    icon={totalApprovals > totalRejections ? CheckCircle2 : XCircle}
                    description={`${totalApprovals} Approved / ${totalRejections} Rejected`}
                    className={cn(
                        "bg-slate-900 border-slate-800",
                        approvalRate < 50 && (totalApprovals+totalRejections) > 0 ? "border-red-500/50" : ""
                    )}
                    />
                </>
             )}
          </div>

          {activeTab === "overview" && (
             <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              {loading ? (
                <div className="col-span-full flex items-center justify-center p-12 text-slate-500">
                  <Activity className="h-6 w-6 animate-spin mr-2" />
                  Connecting to Neural Interface...
                </div>
              ) : agents.length === 0 ? (
                <div className="col-span-full text-center p-12 text-slate-500 border border-slate-800 rounded-xl border-dashed">
                  No agents detected. Start an agent to begin.
                </div>
              ) : (
                agents.map((agent) => (
                  <AgentCard 
                    key={agent.id} 
                    agent={agent}
                    onControl={handleControl}
                    isFocused={false} // Simplification for now
                    onToggleFocus={() => {}}
                  />
                ))
              )}
            </div>
          )}

          {activeTab === "performance" && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Charts */}
                <div className="p-6 rounded-xl border border-slate-800 bg-slate-900 shadow-sm">
                    <PerformanceGraph data={agents} type="iterations" />
                </div>
                 <div className="p-6 rounded-xl border border-slate-800 bg-slate-900 shadow-sm">
                    <PerformanceGraph data={agents} type="decisions" />
                </div>
                 <div className="p-6 rounded-xl border border-slate-800 bg-slate-900 shadow-sm lg:col-span-2">
                    <PerformanceGraph data={agents} type="status" />
                </div>
            </div>
          )}

          {activeTab === "development" && (
             <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Dev Charts */}
                <div className="p-6 rounded-xl border border-slate-800 bg-slate-900 shadow-sm">
                    <ToolUsageChart agents={agents} />
                </div>
                 <div className="p-6 rounded-xl border border-slate-800 bg-slate-900 shadow-sm">
                    <TimingChart agents={agents} />
                </div>
                
                {/* Feature List Status (Mocked/Simple for now) */}
                <div className="p-6 rounded-xl border border-slate-800 bg-slate-900 shadow-sm lg:col-span-2">
                    <h3 className="text-lg font-semibold text-slate-100 mb-4">Project Verification Status</h3>
                    <div className="w-full bg-slate-800 rounded-full h-4 mb-2">
                        <div 
                            className="bg-emerald-500 h-4 rounded-full transition-all duration-500" 
                            style={{ width: `${featurePct}%` }}
                        ></div>
                    </div>
                    <div className="flex justify-between text-sm text-slate-400">
                        <span>{featureCount} Features Passing</span>
                        <span>{featurePct.toFixed(1)}% Verified</span>
                    </div>
                </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
