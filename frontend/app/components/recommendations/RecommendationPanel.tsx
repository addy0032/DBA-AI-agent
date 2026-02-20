"use client";

import { Recommendation } from "@/types";
import { Card, CardHeader, CardTitle, CardContent } from "../shared/Card";
import { Badge } from "../shared/Badge";
import { format } from "date-fns";
import { Sparkles, Terminal } from "lucide-react";

interface RecommendationPanelProps {
    recommendation: Recommendation | null;
}

export function RecommendationPanel({ recommendation }: RecommendationPanelProps) {
    if (!recommendation) {
        return (
            <Card className="h-full flex flex-col">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-purple-500" />
                        AI DBA Analysis
                    </CardTitle>
                </CardHeader>
                <CardContent className="flex-1 flex flex-col items-center justify-center text-zinc-500 py-12">
                    <p>No AI analysis has been triggered or stored recently.</p>
                    <p className="text-sm mt-2">Click "Run AI Analysis" to generate insights.</p>
                </CardContent>
            </Card>
        );
    }

    const riskVariant =
        recommendation.risk_level === "HIGH" ? "critical" :
            recommendation.risk_level === "MEDIUM" ? "warning" : "info";

    return (
        <Card className="h-full flex flex-col border-purple-200 dark:border-purple-900/50 shadow-sm shadow-purple-500/5">
            <CardHeader className="bg-purple-50/50 dark:bg-purple-900/10 rounded-t-xl pb-4 border-b border-purple-100 dark:border-purple-900/30">
                <div className="flex items-start justify-between">
                    <div className="space-y-1">
                        <div className="flex flex-row items-center gap-2">
                            <Sparkles className="h-5 w-5 text-purple-500 fill-purple-500" />
                            <CardTitle className="text-lg">Latest AI Analysis</CardTitle>
                        </div>
                        <p className="text-xs text-zinc-500">
                            {format(new Date(recommendation.timestamp), "MMM dd, yyyy - HH:mm:ss")}
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Badge variant={riskVariant}>Risk: {recommendation.risk_level}</Badge>
                        <Badge variant="outline">Confidence: {Math.round(recommendation.confidence_score * 100)}%</Badge>
                    </div>
                </div>
            </CardHeader>

            <CardContent className="pt-6 space-y-6 overflow-y-auto max-h-[600px]">
                <div>
                    <h3 className="text-lg font-bold mb-2 text-zinc-900 dark:text-zinc-100">{recommendation.issue_summary}</h3>
                    <p className="text-sm text-zinc-700 dark:text-zinc-300 leading-relaxed bg-zinc-50 dark:bg-zinc-900 p-4 rounded-lg border border-zinc-100 dark:border-zinc-800">
                        {recommendation.technical_diagnosis}
                    </p>
                </div>

                <div>
                    <h4 className="font-semibold text-sm text-zinc-900 dark:text-zinc-100 uppercase tracking-wider mb-3">Recommended Actions</h4>
                    <div className="space-y-4">
                        {recommendation.recommended_actions.map((action, idx) => (
                            <div key={idx} className="border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden">
                                <div className="bg-zinc-100 dark:bg-zinc-900/60 p-3 flex items-center gap-3">
                                    <div className="bg-white dark:bg-zinc-800 text-xs font-bold px-2 py-1 rounded shadow-sm">
                                        {action.action_type}
                                    </div>
                                    <span className="text-sm font-medium">{action.description}</span>
                                </div>
                                {action.sql_statement && (
                                    <div className="p-4 bg-[#1e1e1e] text-[#d4d4d4] text-xs font-mono overflow-x-auto relative group">
                                        <Terminal className="absolute top-3 right-3 h-4 w-4 text-zinc-500 opacity-50" />
                                        <pre>{action.sql_statement}</pre>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
