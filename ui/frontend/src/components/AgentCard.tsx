import { Play, Pause, Square, SkipForward, Activity, Power, Clock } from 'lucide-react';
import clsx from 'clsx';
import { Terminal } from './Terminal';

export interface Agent {
    id: string;
    is_running: bool;
    is_paused: bool;
    iteration: number;
    current_task: string;
    last_log: string[];
    last_heartbeat: number;
}

interface AgentCardProps {
    agent: Agent;
    onControl: (id: string, cmd: string) => void;
}

export function AgentCard({ agent, onControl }: AgentCardProps) {
    const now = Date.now() / 1000;
    const isOffline = (now - agent.last_heartbeat) > 15;
    
    let status = 'STOPPED';
    let statusColor = 'text-red-500 bg-red-500/10 border-red-500/20';
    
    if (isOffline) {
        status = 'OFFLINE';
        statusColor = 'text-slate-500 bg-slate-500/10 border-slate-500/20';
    } else if (agent.is_paused) {
        status = 'PAUSED';
        statusColor = 'text-amber-500 bg-amber-500/10 border-amber-500/20';
    } else if (agent.is_running) {
        status = 'RUNNING';
        statusColor = 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
    }

    return (
        <div className="bg-dark-700 border border-dark-600 rounded-xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-300 flex flex-col group">
            <div className="p-4 border-b border-dark-600 bg-dark-800/50 flex justify-between items-center backdrop-blur-sm">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                        <Activity size={18} />
                    </div>
                    <h3 className="font-semibold text-lg text-slate-100">{agent.id}</h3>
                </div>
                <div className={clsx("px-3 py-1 rounded-full text-xs font-bold border flex items-center gap-1.5", statusColor)}>
                    {status === 'RUNNING' && <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />}
                    {status}
                </div>
            </div>

            <div className="p-5 flex-grow space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div className="bg-dark-800 p-3 rounded-lg border border-dark-600/50">
                        <div className="text-slate-400 text-xs uppercase tracking-wider mb-1 flex items-center gap-1">
                            <Clock size={12} />
                            Iteration
                        </div>
                        <div className="text-xl font-mono font-bold text-slate-200">#{agent.iteration}</div>
                    </div>
                    <div className="bg-dark-800 p-3 rounded-lg border border-dark-600/50">
                         <div className="text-slate-400 text-xs uppercase tracking-wider mb-1">Heartbeat</div>
                         <div className={clsx("text-xl font-mono font-bold", isOffline ? "text-red-400" : "text-emerald-400")}>
                            {Math.floor(now - agent.last_heartbeat)}s
                         </div>
                    </div>
                </div>

                <div>
                    <div className="text-slate-400 text-xs uppercase tracking-wider mb-1">Current Task</div>
                    <div className="text-sm font-medium text-slate-200 bg-dark-800 p-2 rounded border border-dark-600/50 min-h-[40px] flex items-center">
                        {agent.current_task || 'Idle'}
                    </div>
                </div>
                
                <Terminal logs={agent.last_log} />
            </div>

            <div className="p-4 bg-dark-800 border-t border-dark-600 flex gap-2">
                {agent.is_paused ? (
                    <button 
                        onClick={() => onControl(agent.id, 'resume')}
                        className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white p-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
                    >
                        <Play size={16} /> Resume
                    </button>
                ) : (
                    <button 
                        onClick={() => onControl(agent.id, 'pause')}
                        disabled={!agent.is_running || isOffline}
                        className="flex-1 bg-amber-600 hover:bg-amber-500 text-white p-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Pause size={16} /> Pause
                    </button>
                )}
                
                <button 
                     onClick={() => onControl(agent.id, 'skip')}
                     disabled={isOffline}
                     className="flex-1 bg-blue-600 hover:bg-blue-500 text-white p-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <SkipForward size={16} /> Skip
                </button>

                <button 
                     onClick={() => onControl(agent.id, 'stop')}
                     disabled={isOffline}
                     className="flex-1 bg-red-600 hover:bg-red-500 text-white p-2 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <Square size={16} /> Stop
                </button>
            </div>
        </div>
    );
}
