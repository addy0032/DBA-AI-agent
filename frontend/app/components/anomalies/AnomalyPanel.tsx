"use client";

import { useState } from "react";
import { Anomaly } from "@/types";
import { Card, CardHeader, CardTitle, CardContent } from "../shared/Card";
import { Badge } from "../shared/Badge";
import { ChevronDown, ChevronRight, AlertTriangle } from "lucide-react";
import { format } from "date-fns";

interface AnomalyCardProps {
    anomaly: Anomaly;
}

function AnomalyCard({ anomaly }: AnomalyCardProps) {
    const [expanded, setExpanded] = useState(false);

    const severityVariant =
        anomaly.severity === "CRITICAL" ? "critical" :
            anomaly.severity === "WARNING" ? "warning" : "info";

    return (
        <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/50 overflow-hidden transition-all">
            <div
                className="flex items-center justify-between p-4 cursor-pointer hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center gap-4">
                    <Badge variant={severityVariant}>{anomaly.severity}</Badge>
                    <span className="font-semibold">{anomaly.type.replace(/_/g, " ")}</span>
                    <span className="text-sm text-zinc-500 hidden md:inline-block">| {anomaly.root_resource}</span>
                </div>
                <div className="flex flex-row items-center gap-4">
                    <span className="text-xs text-zinc-500">{format(new Date(anomaly.timestamp), "HH:mm:ss")}</span>
                    {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </div>
            </div>

            {expanded && (
                <div className="p-4 border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 text-sm overflow-x-auto">
                    <p className="font-medium text-zinc-700 dark:text-zinc-300 mb-2">Resource: {anomaly.root_resource}</p>
                    <pre className="text-xs text-zinc-600 dark:text-zinc-400 p-2 bg-zinc-100 dark:bg-zinc-900 rounded-md whitespace-pre-wrap">
                        {JSON.stringify(anomaly.context_data, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
}

interface AnomalyPanelProps {
    anomalies: Anomaly[];
}

export function AnomalyPanel({ anomalies }: AnomalyPanelProps) {
    // Sort by severity
    const sorted = [...anomalies].sort((a, b) => {
        const s = { "CRITICAL": 3, "WARNING": 2, "INFO": 1 };
        return (s[b.severity as keyof typeof s] || 0) - (s[a.severity as keyof typeof s] || 0);
    });

    return (
        <Card className="h-full flex flex-col">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                        <AlertTriangle className="h-5 w-5 text-amber-500" />
                        Active Anomalies
                    </CardTitle>
                    <Badge variant="outline">{anomalies.length} Detected</Badge>
                </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto max-h-[500px]">
                {sorted.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-zinc-500 py-12">
                        <div className="h-12 w-12 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mb-4">
                            <span className="text-green-600 dark:text-green-400 text-xl font-bold">✓</span>
                        </div>
                        <p>No active anomalies detected.</p>
                    </div>
                ) : (
                    <div className="flex flex-col gap-3">
                        {sorted.map((a) => (
                            <AnomalyCard key={a.id} anomaly={a} />
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
