"use client";

import { useEffect, useState } from "react";
import { observabilityApi } from "@/services/observabilityApi";
import { Workflow, AlertTriangle, Search, X, Copy, CheckCheck } from "lucide-react";

export default function WorkloadPage() {
    const [sessions, setSessions] = useState<any>(null);
    const [blocking, setBlocking] = useState<any>(null);
    const [queries, setQueries] = useState<any>(null);
    const [selectedSql, setSelectedSql] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        const poll = async () => {
            try {
                const [s, b, q] = await Promise.all([
                    observabilityApi.getSessions(),
                    observabilityApi.getBlocking(),
                    observabilityApi.getQueries(),
                ]);
                setSessions(s.current);
                setBlocking(b.current);
                setQueries(q.current);
            } catch (e) { console.error(e); }
        };
        poll();
        const id = setInterval(poll, 5000);
        return () => clearInterval(id);
    }, []);

    const openSql = (sql: string) => { setSelectedSql(sql); setCopied(false); };
    const closeSql = () => setSelectedSql(null);
    const copySql = async () => {
        if (selectedSql) {
            await navigator.clipboard.writeText(selectedSql);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    return (
        <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
            <h1 className="text-2xl font-bold flex items-center gap-3">
                <Workflow className="w-6 h-6 text-amber-500" /> Active Workload
            </h1>

            {/* Session Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard label="Total Sessions" value={sessions?.total_sessions ?? 0} />
                <StatCard label="Active" value={sessions?.active_sessions ?? 0} color="text-emerald-400" />
                <StatCard label="Sleeping" value={sessions?.sleeping_sessions ?? 0} color="text-zinc-400" />
                <StatCard label="Blocked" value={sessions?.blocked_sessions ?? 0} color={sessions?.blocked_sessions > 0 ? "text-red-400" : "text-emerald-400"} />
            </div>

            {/* Blocking Tree */}
            <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
                    <AlertTriangle className="w-5 h-5 text-red-400" /> Blocking Chains
                    <span className="text-xs bg-[#1a1a1a] px-2 py-0.5 rounded text-zinc-500 ml-2">
                        {blocking?.head_blocker_count ?? 0} head blocker(s)
                    </span>
                </h2>
                {blocking?.chains?.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="border-b border-[#333] text-zinc-400 text-xs">
                                <tr>
                                    <th className="text-left py-2 px-3">Session</th>
                                    <th className="text-left py-2 px-3">Blocked By</th>
                                    <th className="text-left py-2 px-3">Wait</th>
                                    <th className="text-left py-2 px-3">Duration (ms)</th>
                                    <th className="text-left py-2 px-3">Command</th>
                                    <th className="text-left py-2 px-3">SQL</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#1a1a1a]">
                                {blocking.chains.map((b: any, i: number) => (
                                    <tr key={i} className={b.is_head_blocker ? "bg-red-950/20" : ""}>
                                        <td className="py-2 px-3 font-mono text-white">{b.session_id}</td>
                                        <td className="py-2 px-3 font-mono text-red-400">{b.blocking_session_id}</td>
                                        <td className="py-2 px-3 text-amber-400">{b.wait_type}</td>
                                        <td className="py-2 px-3 text-zinc-300">{b.wait_time_ms.toLocaleString()}</td>
                                        <td className="py-2 px-3 text-zinc-400">{b.command}</td>
                                        <td className="py-2 px-3 max-w-[300px]">
                                            <button
                                                onClick={() => openSql(b.sql_text || "N/A")}
                                                className="text-left text-zinc-500 hover:text-cyan-400 truncate block max-w-[300px] transition-colors cursor-pointer"
                                                title="Click to view full SQL"
                                            >
                                                {b.sql_text || "—"}
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p className="text-zinc-600 text-sm">No blocking detected.</p>
                )}
            </div>

            {/* Top Queries */}
            <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
                    <Search className="w-5 h-5 text-amber-400" /> Top Queries by CPU
                </h2>
                {queries?.top_by_cpu?.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="border-b border-[#333] text-zinc-400 text-xs">
                                <tr>
                                    <th className="text-left py-2 px-3">Hash</th>
                                    <th className="text-right py-2 px-3">Executions</th>
                                    <th className="text-right py-2 px-3">Worker Time (μs)</th>
                                    <th className="text-right py-2 px-3">Reads</th>
                                    <th className="text-left py-2 px-3">Database</th>
                                    <th className="text-left py-2 px-3">SQL</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#1a1a1a]">
                                {queries.top_by_cpu.map((q: any, i: number) => (
                                    <tr key={i} className="hover:bg-[#1a1a1a]">
                                        <td className="py-2 px-3 font-mono text-cyan-400 text-xs">{q.query_hash}</td>
                                        <td className="py-2 px-3 text-right text-zinc-300">{q.execution_count.toLocaleString()}</td>
                                        <td className="py-2 px-3 text-right text-amber-300">{q.total_worker_time.toLocaleString()}</td>
                                        <td className="py-2 px-3 text-right text-zinc-400">{q.total_logical_reads.toLocaleString()}</td>
                                        <td className="py-2 px-3 text-zinc-500">{q.database_name}</td>
                                        <td className="py-2 px-3 max-w-[300px]">
                                            <button
                                                onClick={() => openSql(q.sql_text || "N/A")}
                                                className="text-left text-zinc-500 hover:text-cyan-400 truncate block max-w-[300px] transition-colors cursor-pointer"
                                                title="Click to view full SQL"
                                            >
                                                {q.sql_text}
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p className="text-zinc-600 text-sm">Loading query data...</p>
                )}
            </div>

            {/* SQL Modal */}
            {selectedSql && (
                <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-6" onClick={closeSql}>
                    <div className="bg-[#0d0d0d] border border-[#333] rounded-2xl w-full max-w-3xl max-h-[80vh] flex flex-col shadow-2xl" onClick={(e) => e.stopPropagation()}>
                        {/* Header */}
                        <div className="flex items-center justify-between px-5 py-4 border-b border-[#222]">
                            <h3 className="text-sm font-semibold text-zinc-300">Full SQL Statement</h3>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={copySql}
                                    className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition"
                                >
                                    {copied ? <CheckCheck className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                                    {copied ? "Copied!" : "Copy"}
                                </button>
                                <button onClick={closeSql} className="text-zinc-500 hover:text-white transition p-1">
                                    <X className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                        {/* Body */}
                        <div className="p-5 overflow-auto flex-1">
                            <pre className="text-sm text-emerald-300 font-mono whitespace-pre-wrap break-words leading-relaxed">{selectedSql}</pre>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function StatCard({ label, value, color = "text-white" }: { label: string; value: any; color?: string }) {
    return (
        <div className="bg-[#111] border border-[#222] rounded-xl p-5">
            <p className="text-xs text-zinc-500 mb-1">{label}</p>
            <p className={`text-3xl font-bold ${color}`}>{value}</p>
        </div>
    );
}
