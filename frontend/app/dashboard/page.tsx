"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { format } from "date-fns";
import { Database, Play, RefreshCw, Activity, CheckCircle2, XCircle } from "lucide-react";
import { MetricSnapshot, Anomaly, Recommendation, HealthCheck } from "@/types";
import { dbaApi } from "@/services/api";

import { MetricCardsRow } from "../components/metrics/MetricCardsRow";
import { LiveMetricsPanel } from "../components/charts/LiveMetricsPanel";
import { AnomalyPanel } from "../components/anomalies/AnomalyPanel";
import { RecommendationPanel } from "../components/recommendations/RecommendationPanel";
import { RecommendationHistory } from "../components/recommendations/RecommendationHistory";
import { FullPageLoader, Loader } from "../components/shared/Loader";

export default function DashboardPage() {
    const [isInitializing, setIsInitializing] = useState(true);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

    // Data State
    const [health, setHealth] = useState<HealthCheck | null>(null);
    const [currentMetrics, setCurrentMetrics] = useState<MetricSnapshot | null>(null);
    const [previousMetrics, setPreviousMetrics] = useState<MetricSnapshot | null>(null);
    const [history, setHistory] = useState<MetricSnapshot[]>([]);
    const [anomalies, setAnomalies] = useState<Anomaly[]>([]);

    // Rec State
    const [activeRecommendation, setActiveRecommendation] = useState<Recommendation | null>(null);
    const [recHistory, setRecHistory] = useState<Recommendation[]>([]);

    // Refs for tracking changes
    const lastMetricsRef = useRef<MetricSnapshot | null>(null);

    const fetchMetricsAndAnomalies = useCallback(async () => {
        try {
            const [_health, _current, _history, _anomalies] = await Promise.all([
                dbaApi.getHealth(),
                dbaApi.getMetricsCurrent(),
                dbaApi.getMetricsHistory(20),
                dbaApi.getAnomalies()
            ]);

            setHealth(_health);

            if (lastMetricsRef.current !== null && lastMetricsRef.current.timestamp !== _current.timestamp) {
                setPreviousMetrics(lastMetricsRef.current);
            }

            setCurrentMetrics(_current);
            lastMetricsRef.current = _current;

            setHistory(_history);
            setAnomalies(_anomalies);
            setLastRefresh(new Date());
        } catch (e) {
            console.error("Polling error", e);
        }
    }, []);

    const loadRecommendations = useCallback(async () => {
        try {
            const [_latest, _history] = await Promise.all([
                dbaApi.getLatestRecommendation(),
                dbaApi.getRecommendationHistory(50)
            ]);
            setActiveRecommendation(_latest);
            setRecHistory(_history);
        } catch (e) {
            console.error("Rec load error", e);
        }
    }, []);

    // Initial load
    useEffect(() => {
        Promise.all([fetchMetricsAndAnomalies(), loadRecommendations()]).finally(() => {
            setIsInitializing(false);
        });
    }, [fetchMetricsAndAnomalies, loadRecommendations]);

    // Polling Interval
    useEffect(() => {
        const intervalId = setInterval(fetchMetricsAndAnomalies, 5000);
        return () => clearInterval(intervalId);
    }, [fetchMetricsAndAnomalies]);

    const handleTriggerAnalysis = async () => {
        if (isAnalyzing) return;
        setIsAnalyzing(true);
        try {
            await dbaApi.triggerAnalysis();
            await loadRecommendations(); // Refresh exactly once after triggering
            await fetchMetricsAndAnomalies(); // force latest state sync
        } catch (e) {
            alert("Failed to trigger analysis.");
            console.error(e);
        } finally {
            setIsAnalyzing(false);
        }
    };

    if (isInitializing) {
        return <FullPageLoader />;
    }

    const isHealthy = health?.status === "ok" && health?.poller_running;

    return (
        <div className="flex flex-col min-h-screen">
            {/* Header Bar */}
            <header className="sticky top-0 z-10 border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-black/80 backdrop-blur-md px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-lg bg-zinc-950 dark:bg-white flex items-center justify-center">
                        <Database className="h-5 w-5 text-zinc-50 dark:text-zinc-950" />
                    </div>
                    <h1 className="font-bold text-lg tracking-tight hidden sm:block">SQL DBA AI Agent</h1>

                    <div className="ml-4 flex items-center gap-2 border-l border-zinc-200 dark:border-zinc-800 pl-4">
                        {isHealthy ? (
                            <span className="flex items-center gap-1.5 text-xs font-medium text-green-600 dark:text-green-500">
                                <CheckCircle2 className="h-4 w-4" /> Connected
                            </span>
                        ) : (
                            <span className="flex items-center gap-1.5 text-xs font-medium text-red-600 dark:text-red-500">
                                <XCircle className="h-4 w-4" /> Disconnected
                            </span>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <div className="hidden md:flex items-center gap-2 text-xs text-zinc-500">
                        <RefreshCw className="h-3 w-3 animate-spin duration-3000" />
                        Last refresh: {lastRefresh ? format(lastRefresh, "HH:mm:ss") : "--:--:--"}
                    </div>
                    <button
                        onClick={handleTriggerAnalysis}
                        disabled={isAnalyzing}
                        className="flex items-center gap-2 bg-zinc-950 dark:bg-zinc-50 hover:bg-zinc-800 dark:hover:bg-zinc-200 text-zinc-50 dark:text-zinc-950 transition-colors px-4 py-2 rounded-md text-sm font-medium shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isAnalyzing ? <Loader size={16} /> : <Play className="h-4 w-4 fill-current" />}
                        {isAnalyzing ? "Analyzing..." : "Run AI Analysis"}
                    </button>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 p-6 space-y-6 max-w-[1600px] mx-auto w-full">
                {/* System Overview */}
                <section>
                    <MetricCardsRow current={currentMetrics} previous={previousMetrics} />
                </section>

                {/* Live Visualizations */}
                <section>
                    <LiveMetricsPanel current={currentMetrics} history={history} />
                </section>

                {/* Anomalies & Recommendations */}
                <section className="grid gap-6 lg:grid-cols-12">
                    {/* Anomalies List */}
                    <div className="lg:col-span-4">
                        <AnomalyPanel anomalies={anomalies} />
                    </div>

                    {/* AI Recommendation Panel */}
                    <div className="lg:col-span-8 flex flex-col gap-6">
                        <div className="flex-1 min-h-[400px]">
                            <RecommendationPanel recommendation={activeRecommendation} />
                        </div>

                        {/* Recommendation History Bar */}
                        <div className="bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4">
                            <RecommendationHistory
                                history={recHistory}
                                onSelect={(rec) => setActiveRecommendation(rec)}
                            />
                        </div>
                    </div>
                </section>
            </main>
        </div>
    );
}
