"use client";

import { useEffect, useState, useCallback } from "react";
import { observabilityApi } from "@/services/observabilityApi";
import { dbaApi } from "@/services/api";
import { HealthCheck } from "@/types";
import { Database, Cpu, MemoryStick, Clock, Workflow, HardDrive, Table2, RefreshCw, CheckCircle2, XCircle } from "lucide-react";
import { format } from "date-fns";
import ReactECharts from "echarts-for-react";

export default function DashboardPage() {
    const [health, setHealth] = useState<HealthCheck | null>(null);
    const [cpu, setCpu] = useState<any>(null);
    const [memory, setMemory] = useState<any>(null);
    const [sessions, setSessions] = useState<any>(null);
    const [waits, setWaits] = useState<any>(null);
    const [cpuHistory, setCpuHistory] = useState<any[]>([]);
    const [waitHistory, setWaitHistory] = useState<any[]>([]);
    const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
    const [blocking, setBlocking] = useState<any>(null);

    const pollFast = useCallback(async () => {
        try {
            const [h, c, s, w, b] = await Promise.all([
                dbaApi.getHealth(),
                observabilityApi.getCpu(),
                observabilityApi.getSessions(),
                observabilityApi.getWaits(),
                observabilityApi.getBlocking(),
            ]);
            setHealth(h);
            setCpu(c.current);
            setCpuHistory(c.history || []);
            setSessions(s.current);
            setWaits(w.current);
            setWaitHistory(w.history || []);
            setBlocking(b.current);
            setLastRefresh(new Date());
        } catch (e) { console.error(e); }
    }, []);

    const [mem, setMem] = useState<any>(null);
    const pollMedium = useCallback(async () => {
        try {
            const m = await observabilityApi.getMemory();
            setMemory(m.current);
        } catch (e) { console.error(e); }
    }, []);

    useEffect(() => {
        pollFast();
        pollMedium();
        const fast = setInterval(pollFast, 5000);
        const med = setInterval(pollMedium, 30000);
        return () => { clearInterval(fast); clearInterval(med); };
    }, [pollFast, pollMedium]);

    const cpuPct = cpu?.sql_cpu_percent ?? 0;
    const isHealthy = health?.status === "ok";

    // CPU history sparkline
    const cpuSparkline = {
        backgroundColor: "transparent",
        grid: { top: 5, right: 5, bottom: 5, left: 5 },
        xAxis: { show: false, type: "category" as const, data: cpuHistory.map((_: any, i: number) => i) },
        yAxis: { show: false, type: "value" as const, min: 0, max: 100 },
        series: [{
            type: "line" as const,
            data: cpuHistory.map((h: any) => h.sql_cpu_percent),
            smooth: true,
            showSymbol: false,
            lineStyle: { width: 2, color: cpuPct > 80 ? "#ef4444" : cpuPct > 50 ? "#f59e0b" : "#22c55e" },
            areaStyle: { opacity: 0.15, color: cpuPct > 80 ? "#ef4444" : cpuPct > 50 ? "#f59e0b" : "#22c55e" },
        }],
    };

    // Top waits mini bar
    const topWaits = (waits?.waits ?? []).slice(0, 5);
    const waitBarOption = {
        backgroundColor: "transparent",
        grid: { top: 5, right: 10, bottom: 5, left: 100 },
        yAxis: { type: "category" as const, data: topWaits.map((w: any) => w.wait_type), axisLabel: { color: "#999", fontSize: 9 }, axisTick: { show: false } },
        xAxis: { show: false, type: "value" as const },
        series: [{
            type: "bar" as const,
            data: topWaits.map((w: any) => w.wait_rate_ms_per_sec.toFixed(1)),
            itemStyle: { color: "#f43f5e", borderRadius: [0, 4, 4, 0] },
            barWidth: 14,
        }],
    };

    return (
        <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
            {/* Header */}
            <header className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-gradient-to-br from-emerald-500 to-cyan-600 rounded-lg flex items-center justify-center">
                        <Database className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold">SQL Server Overview</h1>
                        <div className="flex items-center gap-2 text-xs mt-0.5">
                            {isHealthy ? (
                                <span className="text-emerald-400 flex items-center gap-1"><CheckCircle2 className="w-3 h-3" /> Connected</span>
                            ) : (
                                <span className="text-red-400 flex items-center gap-1"><XCircle className="w-3 h-3" /> Offline</span>
                            )}
                            <span className="text-zinc-600">•</span>
                            <span className="text-zinc-500 flex items-center gap-1">
                                <RefreshCw className="w-3 h-3" />
                                {lastRefresh ? format(lastRefresh, "HH:mm:ss") : "--:--:--"}
                            </span>
                        </div>
                    </div>
                </div>
            </header>

            {/* KPI Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                <KPI label="SQL CPU" value={`${cpuPct}%`} color={cpuPct > 80 ? "text-red-400" : cpuPct > 50 ? "text-amber-400" : "text-emerald-400"} icon={<Cpu className="w-4 h-4" />} />
                <KPI label="PLE" value={memory?.page_life_expectancy ?? "…"} color={memory?.page_life_expectancy < 300 ? "text-red-400" : "text-emerald-400"} icon={<MemoryStick className="w-4 h-4" />} />
                <KPI label="Active Sessions" value={sessions?.active_sessions ?? 0} color="text-sky-400" icon={<Workflow className="w-4 h-4" />} />
                <KPI label="Blocked" value={sessions?.blocked_sessions ?? 0} color={sessions?.blocked_sessions > 0 ? "text-red-400" : "text-emerald-400"} icon={<Workflow className="w-4 h-4" />} />
                <KPI label="Head Blockers" value={blocking?.head_blocker_count ?? 0} color={blocking?.head_blocker_count > 0 ? "text-red-400" : "text-zinc-400"} icon={<Workflow className="w-4 h-4" />} />
                <KPI label="Signal Wait %" value={`${(cpu?.signal_wait_pct ?? 0).toFixed(1)}%`} color={cpu?.signal_wait_pct > 15 ? "text-amber-400" : "text-zinc-400"} icon={<Clock className="w-4 h-4" />} />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* CPU Trend */}
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <h3 className="text-sm text-zinc-400 font-medium mb-2 flex items-center gap-2"><Cpu className="w-4 h-4 text-violet-400" /> CPU Trend</h3>
                    {cpuHistory.length > 1 ? (
                        <ReactECharts option={cpuSparkline} style={{ height: 120 }} opts={{ renderer: "canvas" }} />
                    ) : (
                        <div className="h-[120px] flex items-center justify-center text-zinc-700 text-xs">Collecting...</div>
                    )}
                </div>

                {/* Top Waits */}
                <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                    <h3 className="text-sm text-zinc-400 font-medium mb-2 flex items-center gap-2"><Clock className="w-4 h-4 text-rose-400" /> Top Waits (ms/sec)</h3>
                    {topWaits.length > 0 ? (
                        <ReactECharts option={waitBarOption} style={{ height: 120 }} opts={{ renderer: "canvas" }} />
                    ) : (
                        <div className="h-[120px] flex items-center justify-center text-zinc-700 text-xs">Collecting...</div>
                    )}
                </div>
            </div>

            {/* Memory Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <KPI label="Server Memory (MB)" value={(memory?.total_server_memory_mb ?? 0).toFixed(0)} color="text-violet-400" icon={<MemoryStick className="w-4 h-4" />} />
                <KPI label="Target (MB)" value={(memory?.target_server_memory_mb ?? 0).toFixed(0)} color="text-zinc-400" icon={<MemoryStick className="w-4 h-4" />} />
                <KPI label="Grants Pending" value={memory?.memory_grants_pending ?? 0} color={memory?.memory_grants_pending > 0 ? "text-red-400" : "text-emerald-400"} icon={<MemoryStick className="w-4 h-4" />} />
                <KPI label="Cache Hit %" value={`${(memory?.buffer_cache_hit_ratio ?? 0).toFixed(1)}%`} color={memory?.buffer_cache_hit_ratio < 95 ? "text-amber-400" : "text-emerald-400"} icon={<MemoryStick className="w-4 h-4" />} />
            </div>
        </div>
    );
}

function KPI({ label, value, color, icon }: { label: string; value: any; color: string; icon: React.ReactNode }) {
    return (
        <div className="bg-[#111] border border-[#222] rounded-xl p-4">
            <div className="flex items-center gap-2 text-zinc-500 text-[11px] mb-2">{icon} {label}</div>
            <p className={`text-2xl font-bold tracking-tight ${color}`}>{value}</p>
        </div>
    );
}
