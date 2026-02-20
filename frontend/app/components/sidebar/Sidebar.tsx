"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, MessageSquareCode, Database, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

export function Sidebar() {
    const pathname = usePathname();

    const routes = [
        {
            label: "Dashboard",
            icon: LayoutDashboard,
            href: "/dashboard",
            color: "text-sky-500",
        },
        {
            label: "AI Chat Agent",
            icon: MessageSquareCode,
            href: "/chat",
            color: "text-emerald-500",
        }
    ];

    return (
        <div className="space-y-4 py-4 flex flex-col h-full bg-[#111111] text-white border-r border-[#222]">
            <div className="px-3 py-2 flex-1">
                <Link href="/dashboard" className="flex items-center pl-3 mb-14">
                    <div className="relative w-8 h-8 mr-4 flex items-center justify-center bg-zinc-800 rounded-lg">
                        <Database className="w-5 h-5 text-white" />
                    </div>
                    <h1 className="text-xl font-bold">
                        DBA Agent
                    </h1>
                </Link>
                <div className="space-y-1">
                    {routes.map((route) => (
                        <Link
                            key={route.href}
                            href={route.href}
                            className={cn(
                                "text-sm group flex p-3 w-full justify-start font-medium cursor-pointer hover:text-white hover:bg-zinc-800/50 rounded-lg transition",
                                pathname === route.href ? "text-white bg-zinc-800" : "text-zinc-400"
                            )}
                        >
                            <div className="flex items-center flex-1">
                                <route.icon className={cn("h-5 w-5 mr-3", route.color)} />
                                {route.label}
                            </div>
                        </Link>
                    ))}
                </div>
            </div>
            {/* Version indicator */}
            <div className="px-6 py-4 border-t border-[#222]">
                <div className="flex items-center gap-x-2 text-xs text-zinc-500 font-mono">
                    <Settings className="w-4 h-4" />
                    v2.0.0 (Enterprise)
                </div>
            </div>
        </div>
    );
}
