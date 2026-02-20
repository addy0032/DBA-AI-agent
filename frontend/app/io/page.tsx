"use client";

import { useEffect, useState } from "react";
import { observabilityApi } from "@/services/observabilityApi";
import { HardDrive } from "lucide-react";
import ReactECharts from "echarts-for-react";

export default function IOPage() {
    const [io, setIO] = useState<any>(null);

    useEffect(() => {
        const poll = async () => {
            try {
                const data = await observabilityApi.getIO();
                setIO(data.current);
            } catch (e) { console.error(e); }
        };
        poll();
        const id = setInterval(poll, 30000);
        return () => clearInterval(id);
    }, []);

    const files = io?.files ?? [];
    const latencyOption = {
        backgroundColor: "transparent",
        tooltip: { trigger: "axis" as const },
        legend: { data: ["Read (ms)", "Write (ms)"], textStyle: { color: "#aaa" }, bottom: 0 },
        grid: { top: 20, right: 20, bottom: 50, left: 120 },
        yAxis: { type: "category" as const, data: files.map((f: any) => `${f.database_name}/${f.file_name}`), axisLabel: { color: "#999", fontSize: 10 } },
        xAxis: { type: "value" as const, name: "ms", axisLabel: { color: "#666" }, splitLine: { lineStyle: { color: "#222" } } },
        series: [
            { name: "Read (ms)", type: "bar" as const, data: files.map((f: any) => f.read_latency_ms), itemStyle: { color: "#3b82f6" } },
            { name: "Write (ms)", type: "bar" as const, data: files.map((f: any) => f.write_latency_ms), itemStyle: { color: "#f59e0b" } },
        ],
    };

    return (
        <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
            <h1 className="text-2xl font-bold flex items-center gap-3">
                <HardDrive className="w-6 h-6 text-orange-500" /> I/O & Storage
            </h1>

            {/* TempDB */}
            <div className="grid grid-cols-2 gap-4">
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <p className="text-xs text-zinc-500 mb-1">TempDB Used</p>
                    <p className="text-2xl font-bold text-orange-400">{(io?.tempdb_used_mb ?? 0).toFixed(1)} MB</p>
                </div>
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <p className="text-xs text-zinc-500 mb-1">TempDB Free</p>
                    <p className="text-2xl font-bold text-emerald-400">{(io?.tempdb_free_mb ?? 0).toFixed(1)} MB</p>
                </div>
            </div>

            {/* File Latency Chart */}
            <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                <h2 className="text-base font-semibold text-zinc-300 mb-3">File Latency (ms)</h2>
                {files.length > 0 ? (
                    <ReactECharts option={latencyOption} style={{ height: Math.max(200, files.length * 35) }} opts={{ renderer: "canvas" }} />
                ) : (
                    <div className="h-[200px] flex items-center justify-center text-zinc-600">Loading...</div>
                )}
            </div>

            {/* File Details Table */}
            <div className="bg-[#111] border border-[#222] rounded-xl p-5 overflow-x-auto">
                <table className="w-full text-sm">
                    <thead className="border-b border-[#333] text-zinc-400 text-xs">
                        <tr>
                            <th className="text-left py-2 px-3">Database</th>
                            <th className="text-left py-2 px-3">File</th>
                            <th className="text-left py-2 px-3">Type</th>
                            <th className="text-right py-2 px-3">Size (MB)</th>
                            <th className="text-right py-2 px-3">Read Lat</th>
                            <th className="text-right py-2 px-3">Write Lat</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1a1a1a]">
                        {files.map((f: any, i: number) => (
                            <tr key={i} className="hover:bg-[#1a1a1a]">
                                <td className="py-2 px-3 text-zinc-300">{f.database_name}</td>
                                <td className="py-2 px-3 text-zinc-400">{f.file_name}</td>
                                <td className="py-2 px-3 text-zinc-500">{f.file_type}</td>
                                <td className="py-2 px-3 text-right text-zinc-300">{f.size_mb.toFixed(1)}</td>
                                <td className={`py-2 px-3 text-right ${f.read_latency_ms > 20 ? "text-red-400" : "text-zinc-400"}`}>{f.read_latency_ms.toFixed(1)} ms</td>
                                <td className={`py-2 px-3 text-right ${f.write_latency_ms > 20 ? "text-red-400" : "text-zinc-400"}`}>{f.write_latency_ms.toFixed(1)} ms</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
