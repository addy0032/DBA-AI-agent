"use client";

import { Recommendation } from "@/types";
import { format } from "date-fns";
import { Badge } from "../shared/Badge";
import { ChevronRight } from "lucide-react";
import { useState } from "react";

interface RecommendationHistoryProps {
    history: Recommendation[];
    onSelect: (rec: Recommendation) => void;
}

export function RecommendationHistory({ history, onSelect }: RecommendationHistoryProps) {
    const [activeId, setActiveId] = useState<string | null>(history[0]?.timestamp || null);

    if (!history || history.length === 0) return null;

    return (
        <div className="flex flex-col space-y-2">
            <h3 className="font-semibold text-sm mb-2 px-1 text-zinc-500">History Log</h3>
            <div className="flex flex-col gap-2 max-h-[300px] overflow-y-auto pr-2">
                {history.map((rec) => {
                    const isActive = rec.timestamp === activeId;
                    const riskVar = rec.risk_level === "HIGH" ? "critical" : rec.risk_level === "MEDIUM" ? "warning" : "info";

                    return (
                        <div
                            key={rec.timestamp}
                            onClick={() => {
                                setActiveId(rec.timestamp);
                                onSelect(rec);
                            }}
                            className={`p-3 rounded-lg border text-sm cursor-pointer transition-colors flex flex-col gap-2
                ${isActive
                                    ? "bg-purple-50 border-purple-200 dark:bg-purple-900/20 dark:border-purple-800"
                                    : "bg-white border-zinc-200 hover:bg-zinc-50 dark:bg-zinc-950 dark:border-zinc-800 dark:hover:bg-zinc-900"}
              `}
                        >
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-mono text-zinc-500">
                                    {format(new Date(rec.timestamp), "MM/dd HH:mm")}
                                </span>
                                <Badge variant={riskVar}>{rec.risk_level}</Badge>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="font-medium truncate max-w-[200px]" title={rec.issue_summary}>
                                    {rec.issue_summary}
                                </span>
                                <ChevronRight className="h-4 w-4 text-zinc-400 flex-shrink-0" />
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
