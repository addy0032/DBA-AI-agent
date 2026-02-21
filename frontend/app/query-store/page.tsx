"use client";

import { useEffect, useState } from "react";
import { observabilityApi } from "@/services/observabilityApi";
import { BarChart3, AlertTriangle, Bug, TrendingUp, X, Copy, CheckCheck } from "lucide-react";

export default function QueryStorePage() {
    const [data, setData] = useState<any>(null);
    const [selectedSql, setSelectedSql] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        const load = async () => {
            try {
                const res = await observabilityApi.getQueryStore();
                setData(res.current);
            } catch (e) { console.error(e); }
        };
        load();
        const id = setInterval(load, 300000);
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

    if (!data) return <div className="p-6 text-zinc-600">Loading Query Store data...</div>;

    if (!data.is_enabled) {
        return (
            <div className="p-6 max-w-[1600px] mx-auto">
                <h1 className="text-2xl font-bold flex items-center gap-3 mb-6">
                    <BarChart3 className="w-6 h-6 text-cyan-500" /> Query Store
                </h1>
                <div className="bg-amber-950/20 border border-amber-800/30 rounded-xl p-8 text-center">
                    <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-3" />
                    <p className="text-amber-300 font-medium">Query Store is not enabled on this database.</p>
                    <p className="text-zinc-500 text-sm mt-1">Enable via: ALTER DATABASE [YourDB] SET QUERY_STORE = ON</p>
                </div>
            </div>
        );
    }

    const sniffingCandidates = data.parameter_sniffing_candidates ?? [];
    const suspectedCount = sniffingCandidates.filter((c: any) => c.suspected).length;

    return (
        <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
            <h1 className="text-2xl font-bold flex items-center gap-3">
                <BarChart3 className="w-6 h-6 text-cyan-500" /> Query Store
            </h1>

            {/* Stats Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <p className="text-xs text-zinc-500 mb-1">Forced Plans</p>
                    <p className="text-2xl font-bold text-cyan-400">{data.forced_plan_count}</p>
                </div>
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <p className="text-xs text-zinc-500 mb-1">Total Plans Tracked</p>
                    <p className="text-2xl font-bold text-zinc-300">{data.total_plans_tracked}</p>
                </div>
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <p className="text-xs text-zinc-500 mb-1">Regressed Queries</p>
                    <p className={`text-2xl font-bold ${data.regressed_queries?.length > 0 ? "text-red-400" : "text-emerald-400"}`}>{data.regressed_queries?.length ?? 0}</p>
                </div>
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <p className="text-xs text-zinc-500 mb-1 flex items-center gap-1"><Bug className="w-3 h-3" /> Param Sniffing Suspects</p>
                    <p className={`text-2xl font-bold ${suspectedCount > 0 ? "text-orange-400" : "text-emerald-400"}`}>{suspectedCount}</p>
                </div>
            </div>

            {/* Parameter Sniffing Suspects */}
            {sniffingCandidates.length > 0 && (
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <h2 className="text-base font-semibold text-zinc-300 mb-3 flex items-center gap-2">
                        <Bug className="w-4 h-4 text-orange-400" /> Parameter Sniffing Analysis
                        <span className="text-xs bg-orange-500/10 text-orange-400 px-2 py-0.5 rounded ml-2">
                            {suspectedCount} suspect(s)
                        </span>
                    </h2>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="border-b border-[#333] text-zinc-400 text-xs">
                                <tr>
                                    <th className="text-left py-2 px-3">Query ID</th>
                                    <th className="text-left py-2 px-3">SQL</th>
                                    <th className="text-right py-2 px-3">Plans</th>
                                    <th className="text-right py-2 px-3">Variance Ratio</th>
                                    <th className="text-right py-2 px-3">Stddev (μs)</th>
                                    <th className="text-right py-2 px-3">Min Dur (μs)</th>
                                    <th className="text-right py-2 px-3">Max Dur (μs)</th>
                                    <th className="text-center py-2 px-3">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#1a1a1a]">
                                {sniffingCandidates.map((c: any, i: number) => (
                                    <tr key={i} className={c.suspected ? "bg-orange-950/10" : "hover:bg-[#1a1a1a]"}>
                                        <td className="py-2 px-3 font-mono text-cyan-400">{c.query_id}</td>
                                        <td className="py-2 px-3 max-w-[250px]">
                                            <button
                                                onClick={() => openSql(c.query_text || "N/A")}
                                                className="text-left text-zinc-400 hover:text-cyan-400 truncate block max-w-[250px] transition-colors cursor-pointer text-xs"
                                                title="Click to view full SQL"
                                            >
                                                {c.query_text}
                                            </button>
                                        </td>
                                        <td className="py-2 px-3 text-right text-white font-bold">{c.plan_count}</td>
                                        <td className="py-2 px-3 text-right">
                                            <span className={`font-bold ${c.variance_ratio > 10 ? "text-red-400" : c.variance_ratio > 5 ? "text-amber-400" : c.variance_ratio > 3 ? "text-orange-400" : "text-zinc-400"}`}>
                                                {c.variance_ratio.toFixed(1)}x
                                            </span>
                                        </td>
                                        <td className="py-2 px-3 text-right text-zinc-400">{Math.round(c.duration_stddev_us).toLocaleString()}</td>
                                        <td className="py-2 px-3 text-right text-emerald-400">{Math.round(c.min_avg_duration_us).toLocaleString()}</td>
                                        <td className="py-2 px-3 text-right text-red-400">{Math.round(c.max_avg_duration_us).toLocaleString()}</td>
                                        <td className="py-2 px-3 text-center">
                                            {c.suspected ? (
                                                <span className="inline-flex items-center gap-1 text-orange-400 text-xs font-medium bg-orange-500/10 px-2 py-0.5 rounded">
                                                    <AlertTriangle className="w-3 h-3" /> Suspected
                                                </span>
                                            ) : (
                                                <span className="text-zinc-600 text-xs">Normal</span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Regressed Queries */}
            {data.regressed_queries?.length > 0 && (
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <h2 className="text-base font-semibold text-zinc-300 mb-3 flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-red-400" /> Regressed Queries
                    </h2>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="border-b border-[#333] text-zinc-400 text-xs">
                                <tr>
                                    <th className="text-left py-2 px-3">Query ID</th>
                                    <th className="text-left py-2 px-3">SQL</th>
                                    <th className="text-right py-2 px-3">Recent Avg (μs)</th>
                                    <th className="text-right py-2 px-3">Historical (μs)</th>
                                    <th className="text-right py-2 px-3">Regression %</th>
                                    <th className="text-right py-2 px-3">Plans</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#1a1a1a]">
                                {data.regressed_queries.map((q: any, i: number) => (
                                    <tr key={i} className="hover:bg-[#1a1a1a]">
                                        <td className="py-2 px-3 text-cyan-400 font-mono">{q.query_id}</td>
                                        <td className="py-2 px-3 max-w-[300px]">
                                            <button
                                                onClick={() => openSql(q.query_text || "N/A")}
                                                className="text-left text-zinc-400 hover:text-cyan-400 truncate block max-w-[300px] transition-colors cursor-pointer"
                                                title="Click to view full SQL"
                                            >
                                                {q.query_text}
                                            </button>
                                        </td>
                                        <td className="py-2 px-3 text-right text-red-400">{q.recent_avg_duration_us.toFixed(0)}</td>
                                        <td className="py-2 px-3 text-right text-zinc-400">{q.historical_avg_duration_us.toFixed(0)}</td>
                                        <td className="py-2 px-3 text-right font-bold text-red-300">{q.regression_pct.toFixed(0)}%</td>
                                        <td className="py-2 px-3 text-right text-zinc-500">{q.plan_count}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

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
