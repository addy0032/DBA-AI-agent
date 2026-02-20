"use client";

import { useEffect, useState } from "react";
import { observabilityApi } from "@/services/observabilityApi";
import { Settings, AlertTriangle, CheckCircle2, Info } from "lucide-react";

export default function ConfigurationPage() {
    const [data, setData] = useState<any>(null);

    useEffect(() => {
        const load = async () => {
            try {
                const res = await observabilityApi.getConfiguration();
                setData(res.current);
            } catch (e) { console.error(e); }
        };
        load();
    }, []);

    const settings = data?.settings ?? [];
    const traceFlags = data?.trace_flags ?? [];

    return (
        <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
            <h1 className="text-2xl font-bold flex items-center gap-3">
                <Settings className="w-6 h-6 text-zinc-400" /> Configuration Audit
            </h1>

            {/* Settings Table */}
            <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                <h2 className="text-base font-semibold text-zinc-300 mb-3">Server Settings</h2>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="border-b border-[#333] text-zinc-400 text-xs">
                            <tr>
                                <th className="text-left py-2 px-3">Setting</th>
                                <th className="text-right py-2 px-3">Value</th>
                                <th className="text-left py-2 px-3">Status</th>
                                <th className="text-left py-2 px-3">Notes</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[#1a1a1a]">
                            {settings.map((s: any, i: number) => (
                                <tr key={i} className="hover:bg-[#1a1a1a]">
                                    <td className="py-3 px-3 text-zinc-200 font-medium">{s.name}</td>
                                    <td className="py-3 px-3 text-right font-mono text-white">{String(s.value)}</td>
                                    <td className="py-3 px-3">
                                        {s.warning ? (
                                            <span className="flex items-center gap-1.5 text-amber-400">
                                                <AlertTriangle className="w-3.5 h-3.5" /> Warning
                                            </span>
                                        ) : (
                                            <span className="flex items-center gap-1.5 text-emerald-400">
                                                <CheckCircle2 className="w-3.5 h-3.5" /> OK
                                            </span>
                                        )}
                                    </td>
                                    <td className="py-3 px-3 text-zinc-500 text-xs max-w-[400px]">
                                        {s.warning || s.recommended || "—"}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Trace Flags */}
            <div className="bg-[#111] border border-[#222] rounded-xl p-5">
                <h2 className="text-base font-semibold text-zinc-300 mb-3 flex items-center gap-2">
                    <Info className="w-4 h-4 text-zinc-500" /> Trace Flags
                </h2>
                {traceFlags.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                        {traceFlags.map((tf: number) => (
                            <span key={tf} className="bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded font-mono text-sm">{tf}</span>
                        ))}
                    </div>
                ) : (
                    <p className="text-zinc-600 text-sm">No trace flags enabled.</p>
                )}
            </div>
        </div>
    );
}
