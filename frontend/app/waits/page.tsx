"use client";

import { useEffect, useState, useRef } from "react";
import { observabilityApi } from "@/services/observabilityApi";
import { Clock } from "lucide-react";
import ReactECharts from "echarts-for-react";

export default function WaitsPage() {
    const [current, setCurrent] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);

    useEffect(() => {
        const poll = async () => {
            try {
                const data = await observabilityApi.getWaits();
                setCurrent(data.current);
                setHistory(data.history || []);
            } catch (e) { console.error(e); }
        };
        poll();
        const id = setInterval(poll, 5000);
        return () => clearInterval(id);
    }, []);

    // Build stacked area chart from history
    const waitTypes = new Set<string>();
    history.forEach(h => h.waits?.forEach((w: any) => waitTypes.add(w.wait_type)));
    const sortedTypes = Array.from(waitTypes).slice(0, 8);

    const timestamps = history.map(h => new Date(h.timestamp).toLocaleTimeString());
    const series = sortedTypes.map(wt => ({
        name: wt,
        type: "line" as const,
        stack: "waits",
        areaStyle: { opacity: 0.4 },
        smooth: true,
        data: history.map(h => {
            const found = h.waits?.find((w: any) => w.wait_type === wt);
            return found ? Math.round(found.wait_rate_ms_per_sec) : 0;
        }),
    }));

    const stackedOption = {
        backgroundColor: "transparent",
        tooltip: { trigger: "axis" as const },
        legend: { data: sortedTypes, textStyle: { color: "#aaa", fontSize: 10 }, bottom: 0 },
        grid: { top: 30, right: 20, bottom: 60, left: 60 },
        xAxis: { type: "category" as const, data: timestamps, axisLabel: { color: "#666", fontSize: 10 } },
        yAxis: { type: "value" as const, name: "ms/sec", axisLabel: { color: "#666" }, splitLine: { lineStyle: { color: "#222" } } },
        series,
    };

    return (
        <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
            <h1 className="text-2xl font-bold flex items-center gap-3">
                <Clock className="w-6 h-6 text-rose-500" /> Wait Statistics (Delta)
            </h1>

            {/* Stacked Area Chart */}
            <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                <h2 className="text-base font-semibold text-zinc-300 mb-3">Wait Rate Trends (ms/sec)</h2>
                {history.length > 1 ? (
                    <ReactECharts option={stackedOption} style={{ height: 350 }} opts={{ renderer: "canvas" }} />
                ) : (
                    <div className="h-[350px] flex items-center justify-center text-zinc-600">Collecting data...</div>
                )}
            </div>

            {/* Current Waits Table */}
            <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                <h2 className="text-base font-semibold text-zinc-300 mb-3">Active Wait Types</h2>
                {current?.waits?.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="border-b border-[#333] text-zinc-400 text-xs">
                                <tr>
                                    <th className="text-left py-2 px-3">Wait Type</th>
                                    <th className="text-right py-2 px-3">Rate (ms/sec)</th>
                                    <th className="text-right py-2 px-3">Dominance %</th>
                                    <th className="text-right py-2 px-3">Delta (ms)</th>
                                    <th className="text-right py-2 px-3">Tasks Delta</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-[#1a1a1a]">
                                {current.waits.map((w: any, i: number) => (
                                    <tr key={i} className="hover:bg-[#1a1a1a]">
                                        <td className="py-2 px-3 font-mono text-rose-300">{w.wait_type}</td>
                                        <td className="py-2 px-3 text-right text-white font-bold">{w.wait_rate_ms_per_sec.toFixed(1)}</td>
                                        <td className="py-2 px-3 text-right">
                                            <span className="inline-flex items-center gap-1">
                                                <span className="inline-block h-2 rounded" style={{ width: `${Math.min(w.dominance_pct, 100)}%`, maxWidth: 60, minWidth: 2, backgroundColor: w.dominance_pct > 40 ? '#ef4444' : w.dominance_pct > 15 ? '#f59e0b' : '#22c55e' }} />
                                                <span className="text-zinc-400">{w.dominance_pct.toFixed(1)}%</span>
                                            </span>
                                        </td>
                                        <td className="py-2 px-3 text-right text-zinc-400">{w.wait_time_delta_ms.toFixed(0)}</td>
                                        <td className="py-2 px-3 text-right text-zinc-500">{w.waiting_tasks_delta}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <p className="text-zinc-600 text-sm">No wait data yet...</p>
                )}
            </div>
        </div>
    );
}
