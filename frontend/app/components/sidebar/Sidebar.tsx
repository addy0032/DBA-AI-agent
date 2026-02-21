"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import {
    LayoutDashboard, MessageSquareCode, Database, Settings,
    Cpu, Clock, Workflow, HardDrive,
    Table2, BarChart3, Server, Brain,
    RefreshCw, ChevronDown, Check
} from "lucide-react";
import { cn } from "@/lib/utils";
import { observabilityApi } from "@/services/observabilityApi";

const routes = [
    { label: "Overview", icon: LayoutDashboard, href: "/dashboard", color: "text-sky-500" },
    { label: "Server Health", icon: Cpu, href: "/server", color: "text-violet-500" },
    { label: "Workload", icon: Workflow, href: "/workload", color: "text-amber-500" },
    { label: "Wait Stats", icon: Clock, href: "/waits", color: "text-rose-500" },
    { label: "I/O & Storage", icon: HardDrive, href: "/io", color: "text-orange-500" },
    { label: "Indexes", icon: Table2, href: "/indexes", color: "text-teal-500" },
    { label: "Query Store", icon: BarChart3, href: "/query-store", color: "text-cyan-500" },
    { label: "Databases", icon: Server, href: "/databases", color: "text-indigo-500" },
    { label: "Configuration", icon: Settings, href: "/configuration", color: "text-zinc-400" },
    { divider: true },
    { label: "AI Analysis", icon: Brain, href: "/ai", color: "text-pink-500" },
    { label: "Chat Agent", icon: MessageSquareCode, href: "/chat", color: "text-emerald-500" },
];

export function Sidebar() {
    const pathname = usePathname();
    const [activeDb, setActiveDb] = useState<string>("");
    const [databases, setDatabases] = useState<string[]>([]);
    const [showDbPicker, setShowDbPicker] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [switching, setSwitching] = useState(false);

    // Load active DB and database list
    useEffect(() => {
        observabilityApi.getActiveDb().then(r => setActiveDb(r.database)).catch(() => { });
        observabilityApi.listDatabases().then(r => setDatabases(r.databases)).catch(() => { });
    }, []);

    const handleSwitchDb = useCallback(async (dbName: string) => {
        if (dbName === activeDb) { setShowDbPicker(false); return; }
        setSwitching(true);
        try {
            await observabilityApi.switchDb(dbName);
            setActiveDb(dbName);
            setShowDbPicker(false);
            // Reload the page to refresh all components
            window.location.reload();
        } catch (e) {
            console.error("DB switch failed:", e);
        } finally {
            setSwitching(false);
        }
    }, [activeDb]);

    const handleRefresh = useCallback(async () => {
        setRefreshing(true);
        try {
            await observabilityApi.refreshAll();
            // Small delay then reload to show new data
            setTimeout(() => window.location.reload(), 300);
        } catch (e) {
            console.error("Refresh failed:", e);
        } finally {
            setRefreshing(false);
        }
    }, []);

    return (
        <div className="flex flex-col h-full bg-[#111111] text-white border-r border-[#222]">
            {/* Brand */}
            <div className="px-4 py-5 flex items-center border-b border-[#222]">
                <div className="w-8 h-8 mr-3 flex items-center justify-center bg-gradient-to-br from-emerald-500 to-cyan-600 rounded-lg">
                    <Database className="w-4 h-4 text-white" />
                </div>
                <div>
                    <h1 className="text-sm font-bold tracking-tight">SQL Server</h1>
                    <p className="text-[10px] text-zinc-500 font-mono">Observability Platform</p>
                </div>
            </div>

            {/* Database Selector */}
            <div className="px-3 pt-3 pb-1">
                <div className="relative">
                    <button
                        onClick={() => setShowDbPicker(!showDbPicker)}
                        className="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-[#1a1a1a] border border-[#2a2a2a] hover:border-[#444] transition text-left"
                    >
                        <div className="flex items-center gap-2 min-w-0">
                            <Database className="w-3.5 h-3.5 text-cyan-500 flex-shrink-0" />
                            <span className="text-xs font-medium text-zinc-200 truncate">{activeDb || "..."}</span>
                        </div>
                        <ChevronDown className={cn("w-3.5 h-3.5 text-zinc-500 transition-transform flex-shrink-0", showDbPicker && "rotate-180")} />
                    </button>

                    {showDbPicker && (
                        <div className="absolute top-full left-0 right-0 mt-1 bg-[#0d0d0d] border border-[#333] rounded-lg shadow-2xl z-50 max-h-48 overflow-y-auto">
                            {databases.map(db => (
                                <button
                                    key={db}
                                    onClick={() => handleSwitchDb(db)}
                                    disabled={switching}
                                    className={cn(
                                        "w-full flex items-center gap-2 px-3 py-2 text-xs text-left transition hover:bg-[#1a1a1a]",
                                        db === activeDb ? "text-cyan-400" : "text-zinc-400"
                                    )}
                                >
                                    {db === activeDb && <Check className="w-3 h-3 text-cyan-400 flex-shrink-0" />}
                                    <span className={db === activeDb ? "font-semibold" : "ml-5"}>{db}</span>
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Refresh Button */}
            <div className="px-3 pb-2 pt-1">
                <button
                    onClick={handleRefresh}
                    disabled={refreshing}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-emerald-600/10 border border-emerald-600/20 hover:bg-emerald-600/20 text-emerald-400 text-xs font-medium transition disabled:opacity-50"
                >
                    <RefreshCw className={cn("w-3.5 h-3.5", refreshing && "animate-spin")} />
                    {refreshing ? "Refreshing..." : "Refresh All Metrics"}
                </button>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-0.5">
                {routes.map((route, i) => {
                    if ('divider' in route && route.divider) {
                        return <div key={i} className="my-3 border-t border-[#222]" />;
                    }
                    const r = route as { label: string; icon: any; href: string; color: string };
                    const isActive = pathname === r.href || pathname.startsWith(r.href + "/");
                    return (
                        <Link
                            key={r.href}
                            href={r.href}
                            className={cn(
                                "text-[13px] group flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all",
                                isActive
                                    ? "text-white bg-[#1a1a2e] border border-[#2a2a3e]"
                                    : "text-zinc-400 hover:text-white hover:bg-[#1a1a1a]"
                            )}
                        >
                            <r.icon className={cn("h-4 w-4 flex-shrink-0", isActive ? r.color : "text-zinc-500 group-hover:text-zinc-300")} />
                            <span className="font-medium">{r.label}</span>
                        </Link>
                    );
                })}
            </nav>

            {/* Footer */}
            <div className="px-4 py-3 border-t border-[#222]">
                <p className="text-[10px] text-zinc-600 font-mono">v2.0 Enterprise</p>
            </div>
        </div>
    );
}
