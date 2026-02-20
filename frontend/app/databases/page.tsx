"use client";

import { useEffect, useState } from "react";
import { observabilityApi } from "@/services/observabilityApi";
import { Server, ShieldCheck, ShieldAlert } from "lucide-react";
import { format } from "date-fns";

export default function DatabasesPage() {
    const [data, setData] = useState<any>(null);

    useEffect(() => {
        const load = async () => {
            try {
                const res = await observabilityApi.getDatabases();
                setData(res.current);
            } catch (e) { console.error(e); }
        };
        load();
        const id = setInterval(load, 300000);
        return () => clearInterval(id);
    }, []);

    const databases = data?.databases ?? [];

    const isBackupStale = (date: string | null) => {
        if (!date) return true;
        const hours = (Date.now() - new Date(date).getTime()) / (1000 * 60 * 60);
        return hours > 24;
    };

    return (
        <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
            <h1 className="text-2xl font-bold flex items-center gap-3">
                <Server className="w-6 h-6 text-indigo-500" /> Databases
                <span className="text-sm text-zinc-500 font-normal">({databases.length})</span>
            </h1>

            <div className="bg-[#111] border border-[#222] rounded-xl p-5 overflow-x-auto">
                <table className="w-full text-sm">
                    <thead className="border-b border-[#333] text-zinc-400 text-xs">
                        <tr>
                            <th className="text-left py-2 px-3">Database</th>
                            <th className="text-left py-2 px-3">State</th>
                            <th className="text-left py-2 px-3">Recovery</th>
                            <th className="text-right py-2 px-3">Compat</th>
                            <th className="text-right py-2 px-3">Size (MB)</th>
                            <th className="text-right py-2 px-3">Free (MB)</th>
                            <th className="text-left py-2 px-3">Last Full Backup</th>
                            <th className="text-left py-2 px-3">Last Log Backup</th>
                            <th className="text-left py-2 px-3">Log Reuse Wait</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-[#1a1a1a]">
                        {databases.map((db: any, i: number) => (
                            <tr key={i} className="hover:bg-[#1a1a1a]">
                                <td className="py-2 px-3 font-medium text-indigo-300">{db.db_name}</td>
                                <td className="py-2 px-3">
                                    <span className={`px-2 py-0.5 rounded text-xs ${db.state_desc === "ONLINE" ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"}`}>
                                        {db.state_desc}
                                    </span>
                                </td>
                                <td className="py-2 px-3 text-zinc-400">{db.recovery_model}</td>
                                <td className="py-2 px-3 text-right text-zinc-500">{db.compatibility_level}</td>
                                <td className="py-2 px-3 text-right text-zinc-300">{db.size_mb?.toFixed(1)}</td>
                                <td className="py-2 px-3 text-right text-zinc-400">{db.free_space_mb?.toFixed(1)}</td>
                                <td className="py-2 px-3">
                                    <span className="flex items-center gap-1.5">
                                        {isBackupStale(db.last_full_backup) ? <ShieldAlert className="w-3 h-3 text-red-400" /> : <ShieldCheck className="w-3 h-3 text-emerald-400" />}
                                        <span className={isBackupStale(db.last_full_backup) ? "text-red-400" : "text-zinc-400"}>
                                            {db.last_full_backup ? format(new Date(db.last_full_backup), "MMM d, HH:mm") : "Never"}
                                        </span>
                                    </span>
                                </td>
                                <td className="py-2 px-3 text-zinc-500">
                                    {db.last_log_backup ? format(new Date(db.last_log_backup), "MMM d, HH:mm") : "—"}
                                </td>
                                <td className="py-2 px-3 text-zinc-500">{db.log_reuse_wait_desc || "NOTHING"}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
