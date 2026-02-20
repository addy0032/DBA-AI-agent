"use client";

import { useEffect, useState, useCallback } from "react";
import { Brain, Play } from "lucide-react";
import { dbaApi } from "@/services/api";
import { MetricSnapshot, Anomaly, Recommendation } from "@/types";
import { AnomalyPanel } from "../components/anomalies/AnomalyPanel";
import { RecommendationPanel } from "../components/recommendations/RecommendationPanel";
import { RecommendationHistory } from "../components/recommendations/RecommendationHistory";
import { Loader } from "../components/shared/Loader";

export default function AIPage() {
    const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
    const [activeRec, setActiveRec] = useState<Recommendation | null>(null);
    const [recHistory, setRecHistory] = useState<Recommendation[]>([]);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    const loadData = useCallback(async () => {
        try {
            const [a, r, h] = await Promise.all([
                dbaApi.getAnomalies(),
                dbaApi.getLatestRecommendation(),
                dbaApi.getRecommendationHistory(50),
            ]);
            setAnomalies(a);
            setActiveRec(r);
            setRecHistory(h);
        } catch (e) { console.error(e); }
    }, []);

    useEffect(() => {
        loadData();
        const id = setInterval(loadData, 10000);
        return () => clearInterval(id);
    }, [loadData]);

    const triggerAnalysis = async () => {
        setIsAnalyzing(true);
        try {
            await dbaApi.triggerAnalysis();
            await loadData();
        } catch (e) { console.error(e); } finally { setIsAnalyzing(false); }
    };

    return (
        <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold flex items-center gap-3">
                    <Brain className="w-6 h-6 text-pink-500" /> AI Analysis
                </h1>
                <button
                    onClick={triggerAnalysis}
                    disabled={isAnalyzing}
                    className="flex items-center gap-2 bg-pink-600 hover:bg-pink-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition disabled:opacity-50"
                >
                    {isAnalyzing ? <Loader size={16} /> : <Play className="w-4 h-4 fill-current" />}
                    {isAnalyzing ? "Analyzing..." : "Run AI Analysis"}
                </button>
            </div>

            <div className="grid gap-6 lg:grid-cols-12">
                <div className="lg:col-span-4">
                    <AnomalyPanel anomalies={anomalies} />
                </div>
                <div className="lg:col-span-8 space-y-6">
                    <div className="min-h-[400px]">
                        <RecommendationPanel recommendation={activeRec} />
                    </div>
                    <div className="bg-[#111] border border-[#222] rounded-xl p-4">
                        <RecommendationHistory history={recHistory} onSelect={setActiveRec} />
                    </div>
                </div>
            </div>
        </div>
    );
}
