import { MetricSnapshot, Anomaly, Recommendation, TriggerAnalysisResponse, HealthCheck } from "../types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function fetchWithHandler(endpoint: string, options: RequestInit = {}) {
    try {
        const res = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...options.headers,
            },
        });

        if (!res.ok) {
            const errorText = await res.text();
            throw new Error(`API Error: ${res.status} - ${errorText}`);
        }

        return await res.json();
    } catch (error) {
        console.error(`Fetch error for ${endpoint}:`, error);
        throw error;
    }
}

export const dbaApi = {
    getMetricsCurrent: (): Promise<MetricSnapshot> => fetchWithHandler("/metrics/current"),
    getMetricsHistory: (count: number = 10): Promise<MetricSnapshot[]> => fetchWithHandler(`/metrics/history?count=${count}`),
    getAnomalies: (): Promise<Anomaly[]> => fetchWithHandler("/anomalies"),
    getLatestRecommendation: (): Promise<Recommendation | null> => fetchWithHandler("/recommendations"),
    getRecommendationHistory: (limit: number = 10): Promise<Recommendation[]> => fetchWithHandler(`/recommendations/history?limit=${limit}`),
    triggerAnalysis: (): Promise<TriggerAnalysisResponse> => fetchWithHandler("/trigger-analysis", { method: "POST" }),
    getHealth: (): Promise<HealthCheck> => fetchWithHandler("/health"),
};
