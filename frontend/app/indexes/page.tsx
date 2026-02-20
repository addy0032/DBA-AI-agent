"use client";

import { useEffect, useState } from "react";
import { observabilityApi } from "@/services/observabilityApi";
import { Table2, AlertCircle } from "lucide-react";

export default function IndexesPage() {
    const [data, setData] = useState<any>(null);

    useEffect(() => {
        const load = async () => {
            try {
                const res = await observabilityApi.getIndexes();
                setData(res.current);
            } catch (e) { console.error(e); }
        };
        load();
        const id = setInterval(load, 300000); // 5 min
        return () => clearInterval(id);
    }, []);

    const fragmented = data?.fragmented ?? [];
    const missing = data?.missing ?? [];

    return (
        <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
            <h1 className="text-2xl font-bold flex items-center gap-3">
                <Table2 className="w-6 h-6 text-teal-500" /> Index & Schema Health
            </h1>

            {/* Fragmentation Table */}
            <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                <h2 className="text-base font-semibold text-zinc-300 mb-3">
                    Fragmented Indexes <span className="text-xs text-zinc-500">({fragmented.length})</span>
                </h2>
                {fragmented.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="border-b border-[#333] text-zinc-400 text-xs">
                                <tr>
                                    <th className="text-left py-2 px-3">Table</th>
                                    <th className="text-left py-2 px-3">Index</th>
                                    <th className="text-right py-2 px-3">Frag %</th>
                                    <th className="text-right py-2 px-3">Pages</th>
                                    <th className="text-right py-2 px-3">Seeks</th>
                                    <th className="text-right py-2 px-3">Scans</th>
                                    <th className="text-right py-2 px-3">Updates</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#1a1a1a]">
                                {fragmented.map((idx: any, i: number) => (
                                    <tr key={i} className="hover:bg-[#1a1a1a]">
                                        <td className="py-2 px-3 text-zinc-300">{idx.schema_name}.{idx.table_name}</td>
                                        <td className="py-2 px-3 text-teal-400">{idx.index_name}</td>
                                        <td className="py-2 px-3 text-right">
                                            <span className={`font-mono font-bold ${idx.avg_fragmentation_percent > 30 ? "text-red-400" : idx.avg_fragmentation_percent > 10 ? "text-amber-400" : "text-emerald-400"}`}>
                                                {idx.avg_fragmentation_percent.toFixed(1)}%
                                            </span>
                                        </td>
                                        <td className="py-2 px-3 text-right text-zinc-400">{idx.page_count.toLocaleString()}</td>
                                        <td className="py-2 px-3 text-right text-zinc-400">{idx.user_seeks.toLocaleString()}</td>
                                        <td className="py-2 px-3 text-right text-zinc-400">{idx.user_scans.toLocaleString()}</td>
                                        <td className="py-2 px-3 text-right text-zinc-400">{idx.user_updates.toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p className="text-zinc-600 text-sm">Loading or no fragmented indexes found.</p>
                )}
            </div>

            {/* Missing Indexes */}
            <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                <h2 className="text-base font-semibold text-zinc-300 mb-3 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-amber-400" /> Missing Indexes <span className="text-xs text-zinc-500">({missing.length})</span>
                </h2>
                {missing.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="border-b border-[#333] text-zinc-400 text-xs">
                                <tr>
                                    <th className="text-left py-2 px-3">Table</th>
                                    <th className="text-left py-2 px-3">Equality</th>
                                    <th className="text-left py-2 px-3">Inequality</th>
                                    <th className="text-left py-2 px-3">Include</th>
                                    <th className="text-right py-2 px-3">Impact Score</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#1a1a1a]">
                                {missing.map((m: any, i: number) => (
                                    <tr key={i} className="hover:bg-[#1a1a1a]">
                                        <td className="py-2 px-3 text-zinc-300">{m.schema_name}.{m.table_name}</td>
                                        <td className="py-2 px-3 text-emerald-400 text-xs font-mono max-w-[200px] truncate">{m.equality_columns || "—"}</td>
                                        <td className="py-2 px-3 text-amber-400 text-xs font-mono max-w-[200px] truncate">{m.inequality_columns || "—"}</td>
                                        <td className="py-2 px-3 text-zinc-500 text-xs font-mono max-w-[200px] truncate">{m.included_columns || "—"}</td>
                                        <td className="py-2 px-3 text-right font-bold text-purple-400">{m.impact_score.toFixed(0)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p className="text-zinc-600 text-sm">No missing indexes detected.</p>
                )}
            </div>
        </div>
    );
}
