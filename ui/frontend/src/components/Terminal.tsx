import { useRef, useEffect } from 'react';

interface TerminalProps {
    logs: string[];
}

export function Terminal({ logs }: TerminalProps) {
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    return (
        <div className="bg-dark-900 border border-dark-600 rounded-md p-3 font-mono text-xs text-slate-300 h-48 overflow-y-auto mt-4 shadow-inner">
            {logs.length === 0 && <div className="text-slate-600 italic">No logs yet...</div>}
            {logs.map((log, i) => (
                <div key={i} className="mb-1 border-b border-dark-700/50 pb-0.5 last:border-0 opacity-90 hover:opacity-100 transition-opacity whitespace-pre-wrap">
                    <span className="text-slate-500 mr-2">$</span>
                    {log}
                </div>
            ))}
            <div ref={bottomRef} />
        </div>
    );
}
