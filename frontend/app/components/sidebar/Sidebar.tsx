"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard, MessageSquareCode, Database, Settings,
    Cpu, MemoryStick, Clock, Workflow, HardDrive,
    Table2, BarChart3, Server, Brain
} from "lucide-react";
import { cn } from "@/lib/utils";

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

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
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
