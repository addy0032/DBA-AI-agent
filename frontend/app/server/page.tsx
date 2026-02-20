"use client";

import { useEffect, useState } from "react";
import { observabilityApi } from "@/services/observabilityApi";
import { Cpu, MemoryStick, Activity, Server, Gauge } from "lucide-react";

export default function ServerPage() {
    const [cpu, setCpu] = useState<any>(null);
    const [memory, setMemory] = useState<any>(null);

    useEffect(() => {
        const poll = async () => {
            try {
                const [c, m] = await Promise.all([
                    observabilityApi.getCpu(),
                    observabilityApi.getMemory(),
                ]);
                setCpu(c.current);
                setMemory(m.current);
            } catch (e) { console.error(e); }
        };
        poll();
        const id = setInterval(poll, 5000);
        return () => clearInterval(id);
    }, []);

    const cpuPct = cpu?.sql_cpu_percent ?? 0;
    const memPct = memory ? ((memory.total_server_memory_mb / Math.max(memory.target_server_memory_mb, 1)) * 100).toFixed(1) : "0";

    return (
        <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
            <h1 className="text-2xl font-bold flex items-center gap-3">
                <Cpu className="w-6 h-6 text-violet-500" /> Server Health
            </h1>

            {/* CPU Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard label="SQL CPU Usage" value={`${cpuPct}%`} color={cpuPct > 80 ? "text-red-400" : cpuPct > 50 ? "text-amber-400" : "text-emerald-400"} icon={<Cpu className="w-5 h-5" />} />
                <MetricCard label="System Idle" value={`${cpu?.system_idle_percent ?? 0}%`} color="text-zinc-400" icon={<Activity className="w-5 h-5" />} />
                <MetricCard label="Other Processes" value={`${(cpu?.other_process_cpu_percent ?? 0).toFixed(1)}%`} color="text-amber-400" icon={<Server className="w-5 h-5" />} />
                <MetricCard label="Signal Wait %" value={`${(cpu?.signal_wait_pct ?? 0).toFixed(1)}%`} color={cpu?.signal_wait_pct > 20 ? "text-red-400" : "text-zinc-400"} icon={<Gauge className="w-5 h-5" />} />
            </div>

            {/* Scheduler Section */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <MetricCard label="Schedulers" value={cpu?.scheduler_count ?? 0} color="text-violet-400" icon={<Cpu className="w-5 h-5" />} />
                <MetricCard label="Runnable Tasks" value={cpu?.runnable_tasks_count ?? 0} color={cpu?.runnable_tasks_count > 10 ? "text-red-400" : "text-emerald-400"} icon={<Activity className="w-5 h-5" />} />
                <MetricCard label={`Workers (${cpu?.current_workers_count ?? 0} / ${cpu?.max_workers_count ?? 0})`} value={cpu?.current_workers_count ?? 0} color="text-zinc-400" icon={<Server className="w-5 h-5" />} />
            </div>

            {/* Memory Section */}
            <h2 className="text-xl font-semibold flex items-center gap-2 pt-4">
                <MemoryStick className="w-5 h-5 text-violet-500" /> Memory
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard label="Server Memory (MB)" value={`${(memory?.total_server_memory_mb ?? 0).toFixed(0)}`} color="text-violet-400" icon={<MemoryStick className="w-5 h-5" />} />
                <MetricCard label="Target Memory (MB)" value={`${(memory?.target_server_memory_mb ?? 0).toFixed(0)}`} color="text-zinc-400" icon={<MemoryStick className="w-5 h-5" />} />
                <MetricCard label="Page Life Expectancy" value={memory?.page_life_expectancy ?? 0} color={memory?.page_life_expectancy < 300 ? "text-red-400" : "text-emerald-400"} icon={<Activity className="w-5 h-5" />} />
                <MetricCard label="Buffer Cache Hit %" value={`${(memory?.buffer_cache_hit_ratio ?? 0).toFixed(1)}%`} color={memory?.buffer_cache_hit_ratio < 95 ? "text-amber-400" : "text-emerald-400"} icon={<Gauge className="w-5 h-5" />} />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <MetricCard label="Memory Grants Pending" value={memory?.memory_grants_pending ?? 0} color={memory?.memory_grants_pending > 0 ? "text-red-400" : "text-emerald-400"} icon={<Activity className="w-5 h-5" />} />
                <MetricCard label="Free Memory (MB)" value={`${((memory?.free_memory_kb ?? 0) / 1024).toFixed(0)}`} color="text-zinc-400" icon={<MemoryStick className="w-5 h-5" />} />
                <MetricCard label="Physical Memory Available (MB)" value={`${(memory?.available_physical_memory_mb ?? 0).toFixed(0)}`} color="text-zinc-400" icon={<Server className="w-5 h-5" />} />
            </div>
        </div>
    );
}

function MetricCard({ label, value, color, icon }: { label: string; value: any; color: string; icon: React.ReactNode }) {
    return (
        <div className="bg-[#111] border border-[#222] rounded-xl p-5 flex items-center justify-between">
            <div>
                <p className="text-xs text-zinc-500 font-medium mb-1">{label}</p>
                <p className={`text-2xl font-bold tracking-tight ${color}`}>{value}</p>
            </div>
            <div className="text-zinc-600">{icon}</div>
        </div>
    );
}
