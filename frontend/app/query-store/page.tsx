"use client";

import { useEffect, useState } from "react";
import { observabilityApi } from "@/services/observabilityApi";
import { BarChart3, AlertTriangle, CheckCircle2 } from "lucide-react";

export default function QueryStorePage() {
    const [data, setData] = useState<any>(null);

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

    return (
        <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
            <h1 className="text-2xl font-bold flex items-center gap-3">
                <BarChart3 className="w-6 h-6 text-cyan-500" /> Query Store
            </h1>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
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
            </div>

            {data.regressed_queries?.length > 0 && (
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <h2 className="text-base font-semibold text-zinc-300 mb-3">Regressed Queries</h2>
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
                                        <td className="py-2 px-3 text-zinc-400 max-w-[300px] truncate">{q.query_text}</td>
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
        </div>
    );
}
