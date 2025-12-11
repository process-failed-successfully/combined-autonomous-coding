import { useState, useEffect } from 'react';
import { LayoutDashboard, Moon, Sun, RefreshCw } from 'lucide-react';
import { AgentCard, Agent } from './components/AgentCard';

function App() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [focusedId, setFocusedId] = useState<string | null>(null);

  const fetchAgents = async () => {
    try {
      const res = await fetch('/api/dashboard');
      if (!res.ok) throw new Error('Failed to fetch');
      const data = await res.json();
      setAgents(data);
      setError(null);
    } catch (err) {
      setError('Failed to connect to dashboard server.');
    } finally {
      setLoading(false);
    }
  };

  const handleControl = async (id: string, cmd: string) => {
    try {
      await fetch('/api/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: id, command: cmd })
      });
      // Optimistic upate or quick refetch
      setTimeout(fetchAgents, 100);
    } catch (e) {
      console.error(e);
    }
  };
  
  const toggleFocus = (id: string) => {
      setFocusedId(curr => curr === id ? null : id);
  };

  useEffect(() => {
    fetchAgents();
    const interval = setInterval(fetchAgents, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-dark-900 text-slate-100 selection:bg-blue-500/30">
      
      {/* Header */}
      <header className="border-b border-dark-700 bg-dark-900/50 backdrop-blur-md sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
             <div className="bg-blue-600 p-2 rounded-lg shadow-lg shadow-blue-900/20">
                <LayoutDashboard className="text-white" size={24} />
             </div>
             <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">Agent Nexus</h1>
                <p className="text-xs text-slate-500 font-medium tracking-wide">AUTONOMOUS CONTROL CENTER</p>
             </div>
          </div>

          <div className="flex items-center gap-4">
             {error ? (
                 <div className="flex items-center gap-2 text-red-400 text-sm bg-red-400/10 px-3 py-1.5 rounded-full border border-red-400/20">
                    <div className="w-2 h-2 rounded-full bg-red-500" />
                    Disconnected
                 </div>
             ) : (
                 <div className="flex items-center gap-2 text-emerald-400 text-sm bg-emerald-400/10 px-3 py-1.5 rounded-full border border-emerald-400/20">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    {agents.length} Active System{agents.length !== 1 ? 's' : ''}
                 </div>
             )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        
        {loading && (
             <div className="flex items-center justify-center h-64 text-slate-500 gap-3">
                <RefreshCw className="animate-spin" /> Loading System...
             </div>
        )}

        {!loading && agents.length === 0 && !error && (
            <div className="flex flex-col items-center justify-center h-96 text-slate-500 border-2 border-dashed border-dark-700 rounded-2xl bg-dark-800/30">
                <div className="p-4 bg-dark-800 rounded-full mb-4">
                    <LayoutDashboard size={48} className="opacity-50" />
                </div>
                <h2 className="text-xl font-semibold text-slate-300 mb-2">No Agents Detected</h2>
                <p className="text-sm max-w-md text-center mb-6">Start an agent with <code>--agent gemini</code> to see it appear here instantly.</p>
            </div>
        )}

        <div className={`grid gap-6 ${focusedId ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'}`}>
            {agents
              .filter(agent => !focusedId || agent.id === focusedId)
              .map(agent => (
                <AgentCard 
                    key={agent.id} 
                    agent={agent} 
                    onControl={handleControl} 
                    isFocused={focusedId === agent.id}
                    onToggleFocus={() => toggleFocus(agent.id)}
                />
            ))}
        </div>

      </main>
    </div>
  )
}

export default App
