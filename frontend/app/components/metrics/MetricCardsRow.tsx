import { MetricSnapshot } from "@/types";
import { Card, CardHeader, CardTitle, CardContent } from "../shared/Card";
import { Activity, Users, Clock, Database, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { formatNumber, formatTime } from "@/lib/utils";

interface MetricCardsRowProps {
    current: MetricSnapshot | null;
    previous: MetricSnapshot | null;
}

export function MetricCardsRow({ current, previous }: MetricCardsRowProps) {
    if (!current) return null;

    const currentActive = current.active_sessions_count;
    const prevActive = previous?.active_sessions_count ?? currentActive;

    const currentBlocking = current.blocking_chains.length;
    const prevBlocking = previous?.blocking_chains.length ?? currentBlocking;

    const currentTopWait = current.top_wait_stats[0]?.wait_time_ms ?? 0;
    const prevTopWait = previous?.top_wait_stats[0]?.wait_time_ms ?? currentTopWait;

    const currentExpensive = current.expensive_queries.length;
    const prevExpensive = previous?.expensive_queries.length ?? currentExpensive;

    const getTrend = (curr: number, prev: number, invert: boolean = false) => {
        if (curr === prev) return <Minus className="h-4 w-4 text-zinc-500" />;
        const isUp = curr > prev;
        const isBad = invert ? !isUp : isUp;
        const color = isBad ? "text-red-500" : "text-green-500";
        const Icon = isUp ? TrendingUp : TrendingDown;
        return <Icon className={`h-4 w-4 ${color}`} />;
    };

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
                        Active Sessions
                    </CardTitle>
                    <Users className="h-4 w-4 text-zinc-500" />
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-between">
                        <div className="text-2xl font-bold">{formatNumber(currentActive)}</div>
                        {getTrend(currentActive, prevActive)}
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
                        Blocking Sessions
                    </CardTitle>
                    <Activity className="h-4 w-4 text-zinc-500" />
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-between">
                        <div className="text-2xl font-bold">{currentBlocking}</div>
                        {getTrend(currentBlocking, prevBlocking)}
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
                        Top Wait Time
                    </CardTitle>
                    <Clock className="h-4 w-4 text-zinc-500" />
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-between">
                        <div className="text-2xl font-bold">{formatTime(currentTopWait)}</div>
                        {getTrend(currentTopWait, prevTopWait)}
                    </div>
                    <p className="text-xs text-zinc-500 mt-1 truncate">
                        {current.top_wait_stats[0]?.wait_type || "None"}
                    </p>
                </CardContent>
            </Card>

            <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
                        Expensive Queries
                    </CardTitle>
                    <Database className="h-4 w-4 text-zinc-500" />
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-between">
                        <div className="text-2xl font-bold">{currentExpensive}</div>
                        {getTrend(currentExpensive, prevExpensive)}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
