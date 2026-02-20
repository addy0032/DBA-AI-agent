import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "SQL DBA AI Agent Dashboard",
    description: "Enterprise monitoring and AI recommendations for SQL Server",
};

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen bg-zinc-50 dark:bg-[#0a0a0a] text-zinc-950 dark:text-zinc-50">
            {children}
        </div>
    );
}
